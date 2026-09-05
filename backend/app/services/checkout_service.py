import datetime as dt

from sqlalchemy.orm import Session

from app.audit import ledger
from app.core.config import settings
from app.core.confirm_token import generate_confirmation_token, verify_confirmation_token
from app.core.errors import ConfirmationError, PaytrixError
from app.core.prne import generate_prne
from app.db.models import CheckoutSession, PendingConfirmation, Payment, RiskEvent
from app.db.seed import seed_demo_user
from app.payments.upi_reserve_pay import commit_payment, reserve_funds
from app.policies import idempotency, intent_engine, reputation
from app.policies.sandbox import redact_dict
from app.schemas import AlignmentBreakdown, CheckoutRequest, CheckoutResponse, ConfirmRequest
from app.services.safety import run_safety_kernel


def _log_risk_event(db: Session, trace_id: str, agent_id, event_type: str, details: dict) -> None:
    db.add(RiskEvent(trace_id=trace_id, agent_id=agent_id, event_type=event_type, details=redact_dict(details)))
    db.commit()


def _blocked_response(db: Session, trace_id: str, status: str, reason: str, amount_paise: int, risk_flags: list) -> CheckoutResponse:
    prne = generate_prne(trace_id, reason, amount_paise, gateway_called=False)
    ledger.append_event(db, trace_id, event_type="CHECKOUT_HALTED", status=status, amount_paise=amount_paise)
    return CheckoutResponse(
        trace_id=trace_id,
        status=status,
        reason=reason,
        razorpay_called=False,
        proof_of_non_execution=prne,
        amount_paise=amount_paise,
        risk_flags=risk_flags,
    )


def process_checkout(db: Session, request: CheckoutRequest, agent_id: str) -> CheckoutResponse:
    seed_demo_user(db)

    cached = idempotency.check_idempotency(db, request.trace_id, request.model_dump())
    if cached is not None:
        cached_response = CheckoutResponse(**cached)
        cached_response.idempotent_replay = True
        return cached_response

    db.add(
        CheckoutSession(
            trace_id=request.trace_id,
            user_id=request.user_id,
            agent_id=agent_id,
            merchant_name=request.proposal.product_name,
            product_metadata=redact_dict(request.proposal.model_dump()),
            proposed_price_paise=request.proposal.price_paise,
        )
    )
    db.commit()

    amount_paise = request.proposal.price_paise

    risk_flags = reputation.check_merchant_reputation(
        db, request.proposal.product_id, request.proposal.product_name
    )

    try:
        breakdown = intent_engine.compute_alignment_breakdown(request.intent_envelope, request.proposal)
        run_safety_kernel(db, request.user_id, request.intent_envelope, request.proposal)
    except PaytrixError as e:
        _log_risk_event(db, request.trace_id, agent_id, e.code, {"message": e.message, "proposal": request.proposal.model_dump()})
        resp = _blocked_response(db, request.trace_id, status="BLOCKED", reason=e.message, amount_paise=amount_paise, risk_flags=risk_flags)
        idempotency.store_response(db, request.trace_id, request.model_dump(), resp.model_dump())
        return resp

    score = breakdown["score"]
    decision = intent_engine.decide(score)

    if decision == "BLOCKED":
        reason = f"Intent alignment score {score:.2f} is below the minimum threshold"
        _log_risk_event(db, request.trace_id, agent_id, "INTENT_ALIGNMENT_BLOCKED", {"score": score})
        resp = _blocked_response(db, request.trace_id, status="BLOCKED", reason=reason, amount_paise=amount_paise, risk_flags=risk_flags)
        resp.alignment_score = score
        resp.alignment_breakdown = AlignmentBreakdown(**breakdown)
        idempotency.store_response(db, request.trace_id, request.model_dump(), resp.model_dump())
        return resp

    if decision == "REQUIRE_CONFIRMATION":
        reason = f"Intent alignment score {score:.2f} requires explicit step-up confirmation before execution"
        expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=settings.confirmation_token_ttl_seconds)
        token = generate_confirmation_token(request.trace_id, amount_paise, expires_at)

        db.add(
            PendingConfirmation(
                trace_id=request.trace_id,
                user_id=request.user_id,
                agent_id=agent_id,
                product_id=request.proposal.product_id,
                amount_paise=amount_paise,
                confirmation_token=token,
                expires_at=expires_at,
            )
        )
        db.commit()

        resp = _blocked_response(db, request.trace_id, status="REQUIRE_CONFIRMATION", reason=reason, amount_paise=amount_paise, risk_flags=risk_flags)
        resp.alignment_score = score
        resp.alignment_breakdown = AlignmentBreakdown(**breakdown)
        resp.confirmation_token = token
        resp.confirmation_expires_at = expires_at.isoformat()
        idempotency.store_response(db, request.trace_id, request.model_dump(), resp.model_dump())
        return resp

    try:
        reserve_funds(db, request.user_id, amount_paise)
        gateway_result = commit_payment(db, request.user_id, amount_paise)
    except PaytrixError as e:
        _log_risk_event(db, request.trace_id, agent_id, e.code, {"message": e.message})
        resp = _blocked_response(db, request.trace_id, status="BLOCKED", reason=e.message, amount_paise=amount_paise, risk_flags=risk_flags)
        idempotency.store_response(db, request.trace_id, request.model_dump(), resp.model_dump())
        return resp

    payment = Payment(
        trace_id=request.trace_id,
        user_id=request.user_id,
        agent_id=agent_id,
        product_id=request.proposal.product_id,
        amount_paise=amount_paise,
        status="COMPLETED",
        gateway_called=True,
        gateway_ref=gateway_result["gateway_ref"],
    )
    db.add(payment)
    db.commit()

    ledger.append_event(db, request.trace_id, event_type="PAYMENT_EXECUTED", status="COMPLETED", amount_paise=amount_paise)

    resp = CheckoutResponse(
        trace_id=request.trace_id,
        status="COMPLETED",
        alignment_score=score,
        alignment_breakdown=breakdown,
        risk_flags=risk_flags,
        razorpay_called=True,
        gateway_ref=gateway_result["gateway_ref"],
        amount_paise=amount_paise,
    )
    idempotency.store_response(db, request.trace_id, request.model_dump(), resp.model_dump())
    return resp


def process_confirmation(db: Session, request: ConfirmRequest) -> CheckoutResponse:
    pending = db.query(PendingConfirmation).filter(PendingConfirmation.trace_id == request.trace_id).first()

    if pending is None:
        raise ConfirmationError(f"No pending confirmation found for trace_id '{request.trace_id}'")
    if pending.consumed:
        raise ConfirmationError(f"trace_id '{request.trace_id}' was already confirmed")
    if dt.datetime.utcnow() > pending.expires_at:
        raise ConfirmationError(f"Confirmation token for trace_id '{request.trace_id}' has expired")
    if not verify_confirmation_token(pending.trace_id, pending.amount_paise, pending.expires_at, request.confirmation_token):
        raise ConfirmationError("Confirmation token is invalid or does not match this trace_id")

    amount_paise = pending.amount_paise

    try:
        reserve_funds(db, pending.user_id, amount_paise)
        gateway_result = commit_payment(db, pending.user_id, amount_paise)
    except PaytrixError as e:
        _log_risk_event(db, pending.trace_id, pending.agent_id, e.code, {"message": e.message})
        return _blocked_response(db, pending.trace_id, status="BLOCKED", reason=e.message, amount_paise=amount_paise, risk_flags=[])

    pending.consumed = True
    db.commit()

    payment = Payment(
        trace_id=pending.trace_id,
        user_id=pending.user_id,
        agent_id=pending.agent_id,
        product_id=pending.product_id,
        amount_paise=amount_paise,
        status="COMPLETED",
        gateway_called=True,
        gateway_ref=gateway_result["gateway_ref"],
    )
    db.add(payment)
    db.commit()

    ledger.append_event(db, pending.trace_id, event_type="PAYMENT_EXECUTED_POST_CONFIRMATION", status="COMPLETED", amount_paise=amount_paise)

    return CheckoutResponse(
        trace_id=pending.trace_id,
        status="COMPLETED",
        razorpay_called=True,
        gateway_ref=gateway_result["gateway_ref"],
        amount_paise=amount_paise,
    )
