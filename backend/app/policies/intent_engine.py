from app.core.config import settings
from app.core.errors import CategoryMismatchError, DarkPatternError, MerchantTrustError
from app.schemas import IntentEnvelope, Proposal


def check_dark_pattern(intent_envelope: IntentEnvelope, proposal: Proposal) -> None:
    """Anti-Dark-Pattern Interceptor: halts execution the moment a hidden
    recurring subscription is detected on a non-consenting envelope."""
    if not intent_envelope.allow_recurring_subscriptions and proposal.has_hidden_subscription:
        raise DarkPatternError(
            f"Hidden recurring subscription detected on '{proposal.product_name}' "
            f"but envelope does not permit recurring subscriptions"
        )


def check_hard_guards(intent_envelope: IntentEnvelope, proposal: Proposal) -> None:
    if proposal.category != intent_envelope.required_category:
        raise CategoryMismatchError(
            f"Product category '{proposal.category}' does not match required "
            f"category '{intent_envelope.required_category}'"
        )
    if proposal.merchant_trust_score < intent_envelope.min_merchant_trust_score:
        raise MerchantTrustError(
            f"Merchant trust score {proposal.merchant_trust_score} is below the "
            f"required minimum {intent_envelope.min_merchant_trust_score}"
        )


def _price_fit_score(intent_envelope: IntentEnvelope, proposal: Proposal) -> float:
    price = proposal.price_paise
    target = intent_envelope.target_price_paise
    ceiling = intent_envelope.ceiling_price_paise

    if price <= target:
        return 1.0
    if price >= ceiling:
        return 0.0
    # Linear interpolation between target (1.0) and ceiling (0.0)
    span = ceiling - target
    if span <= 0:
        return 0.0
    return 1.0 - ((price - target) / span)


def compute_alignment_score(intent_envelope: IntentEnvelope, proposal: Proposal) -> float:
    """Alignment Score = (Price Fit x 40%) + (Trust Score x 35%) + (Product Rating x 25%)."""
    price_fit = _price_fit_score(intent_envelope, proposal)
    trust = min(max(proposal.merchant_trust_score, 0.0), 1.0)
    rating = min(max(proposal.product_rating / 5.0, 0.0), 1.0)

    score = (price_fit * 0.40) + (trust * 0.35) + (rating * 0.25)
    return round(score, 4)


def decide(score: float) -> str:
    if score >= settings.intent_auto_execute_threshold:
        return "AUTO_EXECUTE"
    if score >= settings.intent_confirmation_threshold:
        return "REQUIRE_CONFIRMATION"
    return "BLOCKED"
