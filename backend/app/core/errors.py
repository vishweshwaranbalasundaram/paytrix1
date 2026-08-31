class PaytrixError(Exception):
    """Base class for all Safety Kernel interceptor errors."""

    code: str = "PAYTRIX_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DarkPatternError(PaytrixError):
    code = "DARK_PATTERN_DETECTED"


class PriceScalpingError(PaytrixError):
    code = "PRICE_SCALPING_DETECTED"


class VelocityLimitError(PaytrixError):
    code = "VELOCITY_LIMIT_EXCEEDED"


class IntentAlignmentError(PaytrixError):
    code = "INTENT_ALIGNMENT_BLOCKED"


class InsufficientBalanceError(PaytrixError):
    code = "INSUFFICIENT_BALANCE"


class MerchantTrustError(PaytrixError):
    code = "MERCHANT_TRUST_TOO_LOW"


class CategoryMismatchError(PaytrixError):
    code = "CATEGORY_MISMATCH"
