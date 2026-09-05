import datetime as dt
import hashlib
import hmac

from app.core.config import settings


def generate_confirmation_token(trace_id: str, amount_paise: int, expires_at: dt.datetime) -> str:
    message = f"{trace_id}|{amount_paise}|{expires_at.isoformat()}".encode("utf-8")
    signature = hmac.new(
        settings.confirmation_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return f"confirm_sha256:{signature}"


def verify_confirmation_token(trace_id: str, amount_paise: int, expires_at: dt.datetime, token: str) -> bool:
    expected = generate_confirmation_token(trace_id, amount_paise, expires_at)
    return hmac.compare_digest(expected, token)
