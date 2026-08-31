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
    merchant_name = Column(String, nullable=True)
    product_metadata = Column(JSON, nullable=True)
    proposed_price_paise = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, index=True, nullable=False)
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
