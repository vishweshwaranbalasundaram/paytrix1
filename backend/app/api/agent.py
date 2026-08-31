from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.ledger import verify_chain
from app.db.database import get_db
from app.db.models import AuditLedger
from app.schemas import CheckoutRequest, CheckoutResponse, LedgerResponse
from app.services.checkout_service import process_checkout

router = APIRouter()


@router.post("/agent/checkout", response_model=CheckoutResponse)
def checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    return process_checkout(db, request)


@router.get("/agent/ledger", response_model=LedgerResponse)
def get_ledger(db: Session = Depends(get_db)):
    entries = db.query(AuditLedger).order_by(AuditLedger.id.asc()).all()
    return LedgerResponse(ledger=entries, chain_valid=verify_chain(db))
