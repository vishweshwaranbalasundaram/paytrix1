import hashlib
import json

from sqlalchemy.orm import Session

from app.core.errors import IdempotencyConflictError
from app.db.models import IdempotencyRecord


def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check_idempotency(db: Session, trace_id: str, payload: dict):
    """Returns a cached response dict if this exact trace_id + payload was
    already processed (safe retry). Raises IdempotencyConflictError if the
    trace_id was reused with a DIFFERENT payload (replay/tamper attempt).
    Returns None if this trace_id is genuinely new."""
    request_hash = _hash_payload(payload)
    existing = db.query(IdempotencyRecord).filter(IdempotencyRecord.trace_id == trace_id).first()

    if existing is None:
        return None

    if existing.request_hash != request_hash:
        raise IdempotencyConflictError(
            f"trace_id '{trace_id}' was already used with a different payload — "
            f"possible replay or tamper attempt"
        )

    return existing.response_json


def store_response(db: Session, trace_id: str, payload: dict, response_json: dict) -> None:
    request_hash = _hash_payload(payload)
    db.add(
        IdempotencyRecord(
            trace_id=trace_id,
            request_hash=request_hash,
            response_json=response_json,
        )
    )
    db.commit()
