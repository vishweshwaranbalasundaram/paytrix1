from app.schemas import Proposal


def value_efficiency_score(proposal: Proposal) -> float:
    """Simple vendor efficiency heuristic: rating per rupee spent, normalized.
    Higher is better. Used for telemetry/analytics, not a blocking gate."""
    if proposal.price_paise <= 0:
        return 0.0
    rupees = proposal.price_paise / 100
    return round((proposal.product_rating * proposal.merchant_trust_score) / (rupees ** 0.5), 4)
