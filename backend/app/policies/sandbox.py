"""Redacts sensitive tokens (API keys, passwords, UPI VPAs) before anything
is written to RiskEvent logs or surfaced back to the client.
"""
import re
from typing import Any

_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?)([A-Za-z0-9_\-]{8,})'), r"\1[REDACTED]"),
    (re.compile(r'(?i)(password["\']?\s*[:=]\s*["\']?)([^\s"\']{3,})'), r"\1[REDACTED]"),
    (re.compile(r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b(?<!@gmail\.com)(?<!@yahoo\.com)"), "[REDACTED_VPA]"),
]

_SENSITIVE_KEYS = {"api_key", "apikey", "password", "secret", "vpa", "upi_id", "card_number"}


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_dict(data: Any) -> Any:
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if k.lower() in _SENSITIVE_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_dict(v)
        return out
    if isinstance(data, list):
        return [redact_dict(v) for v in data]
    if isinstance(data, str):
        return redact_text(data)
    return data
