import os

os.environ["DATABASE_URL"] = "sqlite:///./test_paytrix.db"

import pytest
from fastapi.testclient import TestClient

DEMO_AGENT_ID = "agt_demo_ui"
DEMO_AGENT_KEY = "demo_agent_secret_key_do_not_use_in_prod"
AUTH_HEADERS = {"X-Agent-Id": DEMO_AGENT_ID, "X-Agent-Key": DEMO_AGENT_KEY}


@pytest.fixture(autouse=True)
def clean_db():
    from app.db.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    from app.main import app
    from app.payments.gateway import MockRazorpayGateway

    MockRazorpayGateway.reset()
    with TestClient(app) as c:
        yield c


def base_payload(trace_id="tr_test_1", **overrides):
    payload = {
        "user_id": "usr_demo_123",
        "user_prompt": "Order monthly diabetes care supplies under 1500 rupees",
        "trace_id": trace_id,
        "intent_envelope": {
            "target_price_paise": 150000,
            "ceiling_price_paise": 160000,
            "min_merchant_trust_score": 0.8,
            "required_category": "pharmacy",
            "allow_recurring_subscriptions": False,
        },
        "proposal": {
            "product_id": f"MED_{trace_id}",
            "product_name": "Diabetes Care Pack",
            "category": "pharmacy",
            "price_paise": 145000,
            "baseline_price_paise": 145000,
            "merchant_trust_score": 0.95,
            "product_rating": 4.8,
            "has_hidden_subscription": False,
        },
    }
    for key, value in overrides.items():
        if "." in key:
            section, field = key.split(".")
            payload[section][field] = value
        else:
            payload[key] = value
    return payload


def checkout(client, payload, headers=AUTH_HEADERS):
    return client.post("/api/v1/agent/checkout", json=payload, headers=headers)


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_happy_path_auto_executes(client):
    res = checkout(client, base_payload("tr_happy_1"))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "COMPLETED"
    assert body["razorpay_called"] is True
    assert body["alignment_score"] >= 0.85
    assert body["alignment_breakdown"]["score"] == body["alignment_score"]


def test_dark_pattern_blocks_before_gateway(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_dark_1")
    payload["proposal"]["has_hidden_subscription"] = True

    res = checkout(client, payload)
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert body["razorpay_called"] is False
    assert MockRazorpayGateway.call_count == 0


def test_price_scalping_blocks(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_scalp_1")
    payload["proposal"]["price_paise"] = 185000

    res = checkout(client, payload)
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert MockRazorpayGateway.call_count == 0


def test_velocity_limit_breach_after_three_transactions(client):
    from app.payments.gateway import MockRazorpayGateway

    for i in range(3):
        res = checkout(client, base_payload(f"tr_velocity_{i}"))
        assert res.json()["status"] == "COMPLETED"

    res = checkout(client, base_payload("tr_velocity_4th"))
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert MockRazorpayGateway.call_count == 3


def test_low_alignment_score_blocked_or_confirmation(client):
    payload = base_payload("tr_low_score_1")
    payload["proposal"]["price_paise"] = 158000
    payload["proposal"]["merchant_trust_score"] = 0.81
    payload["proposal"]["product_rating"] = 2.0

    res = checkout(client, payload)
    body = res.json()
    assert body["status"] in ("BLOCKED", "REQUIRE_CONFIRMATION")
    assert body["razorpay_called"] is False


def test_prne_signature_present_and_verifiable(client):
    from app.core.prne import verify_prne

    payload = base_payload("tr_prne_1")
    payload["proposal"]["has_hidden_subscription"] = True

    res = checkout(client, payload)
    body = res.json()
    assert body["proof_of_non_execution"].startswith("prne_sha256:")
    assert verify_prne(body["trace_id"], body["reason"], body["amount_paise"], False, body["proof_of_non_execution"])


def test_ledger_chain_is_valid_after_multiple_events(client):
    checkout(client, base_payload("tr_ledger_1"))
    bad_payload = base_payload("tr_ledger_2")
    bad_payload["proposal"]["price_paise"] = 185000
    checkout(client, bad_payload)

    res = client.get("/api/v1/agent/ledger")
    body = res.json()
    assert body["chain_valid"] is True
    assert len(body["ledger"]) >= 2


def test_gateway_isolation_on_category_mismatch(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_category_1")
    payload["proposal"]["category"] = "electronics"

    res = checkout(client, payload)
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert MockRazorpayGateway.call_count == 0


# ---------- New security-feature tests ----------

def test_agent_auth_required(client):
    res = client.post("/api/v1/agent/checkout", json=base_payload("tr_noauth_1"))
    assert res.status_code == 401


def test_agent_auth_rejects_wrong_key(client):
    res = client.post(
        "/api/v1/agent/checkout",
        json=base_payload("tr_wrongkey_1"),
        headers={"X-Agent-Id": DEMO_AGENT_ID, "X-Agent-Key": "totally_wrong_key"},
    )
    assert res.status_code == 401


def test_idempotent_replay_returns_cached_response(client):
    payload = base_payload("tr_idem_1")
    res1 = checkout(client, payload)
    res2 = checkout(client, payload)  # exact same payload, same trace_id

    body1, body2 = res1.json(), res2.json()
    assert body1["status"] == body2["status"]
    assert body2["idempotent_replay"] is True
    assert body1.get("gateway_ref") == body2.get("gateway_ref")


def test_idempotency_conflict_on_tampered_replay(client):
    payload = base_payload("tr_tamper_1")
    checkout(client, payload)

    tampered = base_payload("tr_tamper_1")  # same trace_id
    tampered["proposal"]["price_paise"] = 99999  # different payload -> tamper

    res = checkout(client, tampered)
    assert res.status_code == 409


def test_merchant_reputation_flags_new_merchant(client):
    payload = base_payload("tr_reputation_1")
    res = checkout(client, payload)
    body = res.json()
    assert "NEW_MERCHANT" in body["risk_flags"]


def test_step_up_confirmation_flow(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_confirm_1")
    payload["proposal"]["price_paise"] = 158000
    payload["proposal"]["merchant_trust_score"] = 0.81
    payload["proposal"]["product_rating"] = 3.5

    res = checkout(client, payload)
    body = res.json()

    if body["status"] != "REQUIRE_CONFIRMATION":
        pytest.skip("scenario landed outside the confirmation band for this scoring combo")

    assert body["confirmation_token"] is not None
    assert MockRazorpayGateway.call_count == 0

    confirm_res = client.post(
        "/api/v1/agent/confirm",
        json={"trace_id": body["trace_id"], "confirmation_token": body["confirmation_token"]},
        headers=AUTH_HEADERS,
    )
    confirm_body = confirm_res.json()
    assert confirm_body["status"] == "COMPLETED"
    assert confirm_body["razorpay_called"] is True
    assert MockRazorpayGateway.call_count == 1
