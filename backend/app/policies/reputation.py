from sqlalchemy.orm import Session

from app.db.models import Merchant


def check_merchant_reputation(db: Session, product_id: str, product_name: str) -> list[str]:
    """Rule-based reputation signal. Returns a list of risk flags (e.g.
    NEW_MERCHANT) rather than blocking outright — pairs with the merchant
    trust score already gated in the Intent Engine's hard guards to give a
    composite risk picture in the response, not just a single number."""
    flags: list[str] = []

    merchant = db.query(Merchant).filter(Merchant.product_id == product_id).first()
    if merchant is None:
        merchant = Merchant(product_id=product_id, product_name=product_name, request_count=1)
        db.add(merchant)
        db.commit()
        flags.append("NEW_MERCHANT")
    else:
        merchant.request_count += 1
        db.commit()

    return flags
