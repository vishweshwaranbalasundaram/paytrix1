from sqlalchemy.orm import Session

from app.core.errors import InsufficientBalanceError
from app.db.models import User
from app.payments.gateway import MockRazorpayGateway


def reserve_funds(db: Session, user_id: str, amount_paise: int) -> User:
    """Atomically locks `amount_paise` from available -> reserved balance."""
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .with_for_update()
        .first()
    )
    if user is None:
        raise InsufficientBalanceError(f"No wallet found for user {user_id}")
    if user.available_balance_paise < amount_paise:
        raise InsufficientBalanceError(
            f"Available balance ₹{user.available_balance_paise/100:.2f} is less than "
            f"required ₹{amount_paise/100:.2f}"
        )
    user.available_balance_paise -= amount_paise
    user.reserved_balance_paise += amount_paise
    db.commit()
    db.refresh(user)
    return user


def commit_payment(db: Session, user_id: str, amount_paise: int) -> dict:
    """Executes the gateway charge and clears the reserved hold on success."""
    result = MockRazorpayGateway.charge(amount_paise)

    user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
    user.reserved_balance_paise -= amount_paise
    db.commit()
    return result


def release_funds(db: Session, user_id: str, amount_paise: int) -> User:
    """Releases a reserved hold back to available balance (rollback path)."""
    user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
    user.reserved_balance_paise -= amount_paise
    user.available_balance_paise += amount_paise
    db.commit()
    db.refresh(user)
    return user
