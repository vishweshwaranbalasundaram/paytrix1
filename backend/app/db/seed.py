from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User


def seed_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.user_id == settings.demo_user_id).first()
    if user is None:
        user = User(
            user_id=settings.demo_user_id,
            available_balance_paise=settings.demo_user_balance_paise,
            reserved_balance_paise=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
