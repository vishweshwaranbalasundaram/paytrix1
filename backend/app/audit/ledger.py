import hashlib

from sqlalchemy.orm import Session

from app.db.models import AuditLedger

GENESIS_HASH = "0" * 64


def _get_last_hash(db: Session) -> str:
    last = db.query(AuditLedger).order_by(AuditLedger.id.desc()).first()
    return last.payload_hash if last else GENESIS_HASH


def append_event(db: Session, trace_id: str, event_type: str, status: str, amount_paise: int) -> AuditLedger:
    previous_hash = _get_last_hash(db)
    payload = f"{trace_id}|{event_type}|{status}|{amount_paise}|{previous_hash}".encode("utf-8")
    payload_hash = hashlib.sha256(payload).hexdigest()

    entry = AuditLedger(
        trace_id=trace_id,
        event_type=event_type,
        status=status,
        amount_paise=amount_paise,
        payload_hash=payload_hash,
        previous_hash=previous_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> bool:
    """Walk the full ledger and confirm every hash link is intact."""
    entries = db.query(AuditLedger).order_by(AuditLedger.id.asc()).all()
    previous_hash = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != previous_hash:
            return False
        payload = f"{entry.trace_id}|{entry.event_type}|{entry.status}|{entry.amount_paise}|{entry.previous_hash}".encode("utf-8")
        expected_hash = hashlib.sha256(payload).hexdigest()
        if expected_hash != entry.payload_hash:
            return False
        previous_hash = entry.payload_hash
    return True
