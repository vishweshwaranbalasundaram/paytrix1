from sqlalchemy.orm import Session

from app.audit import ledger
from app.core.errors import PaytrixError
from app.core.prne import generate_prne
from app.db.models import CheckoutSession, Payment, RiskEvent
from app.db.seed import seed_demo_user
from app.payments.upi_reserve_pay import commit_payment, reserve_funds
from app.policies import intent_engine
from app.policies.sandbox import redact_dict
from app.schemas import CheckoutRequest, CheckoutResponse
from app.services.safety import run_safety_kernel


def _log_risk_event(db: Session, trace_id: str, event_type: str, details: dict) -> None:
    db.add(RiskEvent(trace_id=trace_id, event_type=event_type, details=redact_dict(details)))
    db.commit()


def _blocked_response(db: Session, trace_id: str, status: str, reason: str, amount_paise: int) -> CheckoutResponse:
    prne = generate_prne(trace_id, reason, amount_paise, gateway_called=False)
    ledger.append_event(db, trace_id, event_type="CHECKOUT_HALTED", status=status, amount_paise=amount_paise)
    return CheckoutResponse(
        trace_id=trace_id,
        status=status,
        reason=reason,
        razorpay_called=False,
        proof_of_non_execution=prne,
        amount_paise=amount_paise,
    )


def process_checkout(db: Session, request: CheckoutRequest) -> CheckoutResponse:
    seed_demo_user(db)  # ensures the demo wallet exists on a fresh DB

    db.add(
        CheckoutSession(
            trace_id=request.trace_id,
            user_id=request.user_id,
            merchant_name=request.proposal.product_name,
            product_metadata=redact_dict(request.proposal.model_dump()),
            proposed_price_paise=request.proposal.price_paise,
        )
    )
    db.commit()

    amount_paise = request.proposal.price_paise

    # --- Safety Kernel pipeline ---
    try:
        score = run_safety_kernel(db, request.user_id, request.intent_envelope, request.proposal)
    except PaytrixError as e:
        _log_risk_event(db, request.trace_id, e.code, {"message": e.message, "proposal": request.proposal.model_dump()})
        return _blocked_response(db, request.trace_id, status="BLOCKED", reason=e.message, amount_paise=amount_paise)

    decision = intent_engine.decide(score)

    if decision == "BLOCKED":
        reason = f"Intent alignment score {score:.2f} is below the minimum threshold"
        _log_risk_event(db, request.trace_id, "INTENT_ALIGNMENT_BLOCKED", {"score": score})
        resp = _blocked_response(db, request.trace_id, status="BLOCKED", reason=reason, amount_paise=amount_paise)
        resp.alignment_score = score
        return resp

    if decision == "REQUIRE_CONFIRMATION":
        reason = f"Intent alignment score {score:.2f} requires explicit user confirmation before execution"
        resp = _blocked_response(db, request.trace_id, status="REQUIRE_CONFIRMATION", reason=reason, amount_paise=amount_paise)
        resp.alignment_score = score
        return resp

    # --- AUTO_EXECUTE path ---
    try:
        reserve_funds(db, request.user_id, amount_paise)
        gateway_result = commit_payment(db, request.user_id, amount_paise)
    except PaytrixError as e:
        _log_risk_event(db, request.trace_id, e.code, {"message": e.message})
        return _blocked_response(db, request.trace_id, status="BLOCKED", reason=e.message, amount_paise=amount_paise)

    payment = Payment(
        trace_id=request.trace_id,
        user_id=request.user_id,
        product_id=request.proposal.product_id,
        amount_paise=amount_paise,
        status="COMPLETED",
        gateway_called=True,
        gateway_ref=gateway_result["gateway_ref"],
    )
    db.add(payment)
    db.commit()

    ledger.append_event(db, request.trace_id, event_type="PAYMENT_EXECUTED", status="COMPLETED", amount_paise=amount_paise)

    return CheckoutResponse(
        trace_id=request.trace_id,
        status="COMPLETED",
        alignment_score=score,
        razorpay_called=True,
        gateway_ref=gateway_result["gateway_ref"],
        amount_paise=amount_paise,
    )
