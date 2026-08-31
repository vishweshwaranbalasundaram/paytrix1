from sqlalchemy.orm import Session

from app.policies import intent_engine, price_sentinel, velocity_governor
from app.schemas import IntentEnvelope, Proposal


def run_safety_kernel(db: Session, user_id: str, intent_envelope: IntentEnvelope, proposal: Proposal) -> float:
    """Runs every interceptor in sequence. Any PaytrixError raised here
    propagates up to the checkout orchestrator, which halts before the
    gateway and mints a PrNE receipt instead.

    Order matters: dark-pattern and hard guards are checked first (cheapest,
    most clear-cut denials), then price sentinel, then velocity, then the
    weighted intent alignment score is computed last.
    """
    intent_engine.check_dark_pattern(intent_envelope, proposal)
    intent_engine.check_hard_guards(intent_envelope, proposal)
    price_sentinel.check_price(proposal.price_paise, proposal.baseline_price_paise)
    velocity_governor.check_velocity(db, user_id, proposal.price_paise)

    score = intent_engine.compute_alignment_score(intent_envelope, proposal)
    return score
