from typing import Any, Optional

from pydantic import BaseModel, Field


class IntentEnvelope(BaseModel):
    target_price_paise: int = Field(..., gt=0)
    ceiling_price_paise: int = Field(..., gt=0)
    min_merchant_trust_score: float = Field(..., ge=0, le=1)
    required_category: str
    allow_recurring_subscriptions: bool = False


class Proposal(BaseModel):
    product_id: str
    product_name: str
    category: str
    price_paise: int = Field(..., gt=0)
    baseline_price_paise: int = Field(..., gt=0)
    merchant_trust_score: float = Field(..., ge=0, le=1)
    product_rating: float = Field(..., ge=0, le=5)
    has_hidden_subscription: bool = False


class CheckoutRequest(BaseModel):
    user_id: str
    user_prompt: str
    trace_id: str
    intent_envelope: IntentEnvelope
    proposal: Proposal


class AlignmentBreakdown(BaseModel):
    score: float
    price_fit: float
    price_component: float
    trust_component: float
    rating_component: float
    weights: dict[str, float]


class CheckoutResponse(BaseModel):
    trace_id: str
    status: str  # COMPLETED, REQUIRE_CONFIRMATION, BLOCKED
    alignment_score: Optional[float] = None
    alignment_breakdown: Optional[AlignmentBreakdown] = None
    risk_flags: list[str] = []
    reason: Optional[str] = None
    razorpay_called: bool = False
    gateway_ref: Optional[str] = None
    proof_of_non_execution: Optional[str] = None
    amount_paise: Optional[int] = None
    confirmation_token: Optional[str] = None
    confirmation_expires_at: Optional[str] = None
    idempotent_replay: bool = False


class ConfirmRequest(BaseModel):
    trace_id: str
    confirmation_token: str


class LedgerEntryOut(BaseModel):
    id: int
    trace_id: str
    event_type: str
    status: str
    amount_paise: int
    payload_hash: str
    previous_hash: str

    class Config:
        from_attributes = True


class LedgerResponse(BaseModel):
    ledger: list[LedgerEntryOut]
    chain_valid: bool
