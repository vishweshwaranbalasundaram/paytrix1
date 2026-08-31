from app.core.config import settings
from app.core.errors import PriceScalpingError


def check_price(price_paise: int, baseline_price_paise: int) -> None:
    """Blocks any dynamic markup exceeding the configured threshold (default 10%)
    over the 7-day baseline price."""
    if baseline_price_paise <= 0:
        return
    max_allowed = baseline_price_paise * (1 + settings.price_scalping_threshold_pct / 100)
    if price_paise > max_allowed:
        markup_pct = ((price_paise - baseline_price_paise) / baseline_price_paise) * 100
        raise PriceScalpingError(
            f"Price ₹{price_paise/100:.2f} exceeds baseline ₹{baseline_price_paise/100:.2f} "
            f"by {markup_pct:.1f}% (cap: {settings.price_scalping_threshold_pct}%)"
        )
