from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.audit.ledger import verify_chain
from app.core.errors import PaytrixError
from app.db.database import get_db
from app.db.models import AuditLedger
from app.policies.agent_identity import check_agent_rate_limit, verify_agent
from app.schemas import CheckoutRequest, CheckoutResponse, ConfirmRequest, LedgerResponse
from app.services.checkout_service import process_checkout, process_confirmation

router = APIRouter()


def _authenticate_agent(
    db: Session,
    x_agent_id: str | None,
    x_agent_key: str | None,
) -> str:
    try:
        agent_id = verify_agent(db, x_agent_id, x_agent_key)
        check_agent_rate_limit(db, agent_id)
        return agent_id
    except PaytrixError as e:
        raise HTTPException(status_code=401, detail={"code": e.code, "message": e.message})


@router.post("/agent/checkout", response_model=CheckoutResponse)
def checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    x_agent_id: str | None = Header(default=None),
    x_agent_key: str | None = Header(default=None),
):
    agent_id = _authenticate_agent(db, x_agent_id, x_agent_key)
    try:
        return process_checkout(db, request, agent_id)
    except PaytrixError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.post("/agent/confirm", response_model=CheckoutResponse)
def confirm(
    request: ConfirmRequest,
    db: Session = Depends(get_db),
    x_agent_id: str | None = Header(default=None),
    x_agent_key: str | None = Header(default=None),
):
    _authenticate_agent(db, x_agent_id, x_agent_key)
    try:
        return process_confirmation(db, request)
    except PaytrixError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@router.get("/agent/ledger", response_model=LedgerResponse)
def get_ledger(db: Session = Depends(get_db)):
    entries = db.query(AuditLedger).order_by(AuditLedger.id.asc()).all()
    return LedgerResponse(ledger=entries, chain_valid=verify_chain(db))
