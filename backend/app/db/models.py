import datetime as dt

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    available_balance_paise = Column(Integer, nullable=False, default=0)
    reserved_balance_paise = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    agent_id = Column(String, index=True, nullable=True)
    product_id = Column(String, nullable=True)
    amount_paise = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # COMPLETED, PENDING, ROLLED_BACK, BLOCKED
    gateway_called = Column(Boolean, default=False)
    gateway_ref = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    agent_id = Column(String, index=True, nullable=True)
    merchant_name = Column(String, nullable=True)
    product_metadata = Column(JSON, nullable=True)
    proposed_price_paise = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    agent_id = Column(String, index=True, nullable=True)
    event_type = Column(String, nullable=False)
    details = Column(JSON, nullable=True)  # sensitive fields pre-redacted
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class AuditLedger(Base):
    __tablename__ = "audit_ledger"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    amount_paise = Column(Integer, nullable=False, default=0)
    payload_hash = Column(String, nullable=False)
    previous_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class AgentKey(Base):
    """Registered AI agents allowed to call the checkout API. Keys are
    stored as SHA-256 hashes, never in plaintext."""
    __tablename__ = "agent_keys"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True, nullable=False)
    key_hash = Column(String, nullable=False)
    label = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class IdempotencyRecord(Base):
    """One row per trace_id ever processed. A repeat call with the same
    trace_id + identical payload replays the cached response instead of
    re-running the kernel; a repeat with a DIFFERENT payload is treated as
    a tamper/replay attempt and rejected outright."""
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    request_hash = Column(String, nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class PendingConfirmation(Base):
    """Holds a REQUIRE_CONFIRMATION checkout awaiting explicit user/agent
    step-up approval via POST /agent/confirm before any funds move."""
    __tablename__ = "pending_confirmations"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=True)
    product_id = Column(String, nullable=True)
    amount_paise = Column(Integer, nullable=False)
    confirmation_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Merchant(Base):
    """Lightweight merchant reputation tracker keyed by product_id. First
    time a product_id is seen it's flagged NEW_MERCHANT for extra scrutiny
    in the response's risk_flags."""
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=True)
    first_seen_at = Column(DateTime, default=dt.datetime.utcnow)
    request_count = Column(Integer, default=0)
