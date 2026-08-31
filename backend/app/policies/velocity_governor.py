import datetime as dt

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import VelocityLimitError
from app.db.models import Payment


def check_velocity(db: Session, user_id: str, incoming_amount_paise: int) -> None:
    """Trips if the user's agent has exceeded max transactions or max spend
    within the rolling window (default: 3 txs / ₹5,000 / 10 minutes)."""
    window_start = dt.datetime.utcnow() - dt.timedelta(minutes=settings.velocity_window_minutes)

    recent = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.created_at >= window_start,
            Payment.status == "COMPLETED",
        )
        .all()
    )

    tx_count = len(recent)
    total_spend = sum(p.amount_paise for p in recent)

    if tx_count + 1 > settings.velocity_max_transactions:
        raise VelocityLimitError(
            f"Velocity breach: {tx_count} transactions already in the last "
            f"{settings.velocity_window_minutes}m (max {settings.velocity_max_transactions})"
        )

    if total_spend + incoming_amount_paise > settings.velocity_max_spend_paise:
        raise VelocityLimitError(
            f"Velocity breach: ₹{(total_spend + incoming_amount_paise)/100:.2f} would exceed "
            f"₹{settings.velocity_max_spend_paise/100:.2f} rolling {settings.velocity_window_minutes}m cap"
        )
