"""Cryptographic Proof of Non-Execution (PrNE).

When the Safety Kernel halts a transaction before it ever reaches a payment
gateway, we generate a signed receipt proving that no gateway call was made.
This gives the user (and an auditor) a verifiable guarantee that
`Razorpay Call Count = 0` for that trace.
"""
import hashlib
import hmac

from app.core.config import settings


def generate_prne(trace_id: str, reason: str, amount_paise: int, gateway_called: bool = False) -> str:
    """HMAC-SHA256(prne_secret, trace_id | reason | amount_paise | gateway_called)."""
    message = f"{trace_id}|{reason}|{amount_paise}|{gateway_called}".encode("utf-8")
    signature = hmac.new(
        settings.prne_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return f"prne_sha256:{signature}"


def verify_prne(trace_id: str, reason: str, amount_paise: int, gateway_called: bool, signature: str) -> bool:
    expected = generate_prne(trace_id, reason, amount_paise, gateway_called)
    return hmac.compare_digest(expected, signature)
