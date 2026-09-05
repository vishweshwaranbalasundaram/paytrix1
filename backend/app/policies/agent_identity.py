import datetime as dt
import hashlib

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AgentAuthError, AgentRateLimitError
from app.db.models import AgentKey, CheckoutSession


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def seed_demo_agent(db: Session) -> None:
    existing = db.query(AgentKey).filter(AgentKey.agent_id == settings.demo_agent_id).first()
    if existing is None:
        db.add(
            AgentKey(
                agent_id=settings.demo_agent_id,
                key_hash=_hash_key(settings.demo_agent_key),
                label="Demo UI agent (seeded)",
            )
        )
        db.commit()


def verify_agent(db: Session, agent_id: str | None, agent_key: str | None) -> str:
    """Verifies the caller's signed agent identity. Returns the verified
    agent_id, or raises AgentAuthError. Every checkout request MUST present
    a valid agent_id/agent_key pair so the audit trail can prove *which*
    AI agent initiated it, not just which user it claims to act for."""
    if not agent_id or not agent_key:
        raise AgentAuthError("Missing X-Agent-Id / X-Agent-Key headers — every agent must authenticate")

    record = db.query(AgentKey).filter(AgentKey.agent_id == agent_id).first()
    if record is None or record.key_hash != _hash_key(agent_key):
        raise AgentAuthError(f"Invalid agent credentials for agent_id '{agent_id}'")

    return agent_id


def check_agent_rate_limit(db: Session, agent_id: str) -> None:
    """Independent of the per-user Velocity Governor: this caps how many
    requests a single AI agent identity can fire per minute, regardless of
    which users it claims to act on behalf of."""
    window_start = dt.datetime.utcnow() - dt.timedelta(minutes=1)
    count = (
        db.query(CheckoutSession)
        .filter(CheckoutSession.agent_id == agent_id, CheckoutSession.created_at >= window_start)
        .count()
    )
    if count >= settings.agent_rate_limit_per_minute:
        raise AgentRateLimitError(
            f"Agent '{agent_id}' exceeded {settings.agent_rate_limit_per_minute} requests/minute"
        )
