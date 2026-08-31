import os

os.environ["DATABASE_URL"] = "sqlite:///./test_paytrix.db"

import pytest
from fastapi.testclient import TestClient

DB_FILE = "test_paytrix.db"


@pytest.fixture(autouse=True)
def clean_db():
    # Drop/recreate tables on the SAME engine/connection pool rather than
    # deleting the sqlite file out from under pooled connections (that causes
    # spurious "attempt to write a readonly database" errors).
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
            "product_id": "MED_101",
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


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "PAYTRIX"


def test_happy_path_auto_executes(client):
    res = client.post("/api/v1/agent/checkout", json=base_payload("tr_happy_1"))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "COMPLETED"
    assert body["razorpay_called"] is True
    assert body["gateway_ref"] is not None
    assert body["alignment_score"] >= 0.85


def test_dark_pattern_blocks_before_gateway(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_dark_1")
    payload["proposal"]["has_hidden_subscription"] = True
    payload["proposal"]["product_name"] = "Diabetes Care + Secret Club (₹299/mo)"

    res = client.post("/api/v1/agent/checkout", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert body["razorpay_called"] is False
    assert body["proof_of_non_execution"] is not None
    assert MockRazorpayGateway.call_count == 0


def test_price_scalping_blocks(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_scalp_1")
    payload["proposal"]["price_paise"] = 185000  # +27.5% over 145000 baseline

    res = client.post("/api/v1/agent/checkout", json=payload)
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert body["razorpay_called"] is False
    assert MockRazorpayGateway.call_count == 0


def test_velocity_limit_breach_after_three_transactions(client):
    from app.payments.gateway import MockRazorpayGateway

    for i in range(3):
        res = client.post("/api/v1/agent/checkout", json=base_payload(f"tr_velocity_{i}"))
        assert res.json()["status"] == "COMPLETED"

    res = client.post("/api/v1/agent/checkout", json=base_payload("tr_velocity_4th"))
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert "Velocity" in body["reason"] or "velocity" in body["reason"].lower()
    assert MockRazorpayGateway.call_count == 3


def test_low_alignment_score_blocked(client):
    payload = base_payload("tr_low_score_1")
    payload["proposal"]["price_paise"] = 158000  # near ceiling -> low price fit
    payload["proposal"]["merchant_trust_score"] = 0.81
    payload["proposal"]["product_rating"] = 2.0

    res = client.post("/api/v1/agent/checkout", json=payload)
    body = res.json()
    assert body["status"] in ("BLOCKED", "REQUIRE_CONFIRMATION")
    assert body["razorpay_called"] is False


def test_prne_signature_present_and_verifiable(client):
    from app.core.prne import verify_prne

    payload = base_payload("tr_prne_1")
    payload["proposal"]["has_hidden_subscription"] = True

    res = client.post("/api/v1/agent/checkout", json=payload)
    body = res.json()
    assert body["proof_of_non_execution"].startswith("prne_sha256:")
    assert verify_prne(
        body["trace_id"], body["reason"], body["amount_paise"], False, body["proof_of_non_execution"]
    )


def test_ledger_chain_is_valid_after_multiple_events(client):
    client.post("/api/v1/agent/checkout", json=base_payload("tr_ledger_1"))
    bad_payload = base_payload("tr_ledger_2")
    bad_payload["proposal"]["price_paise"] = 185000
    client.post("/api/v1/agent/checkout", json=bad_payload)

    res = client.get("/api/v1/agent/ledger")
    body = res.json()
    assert body["chain_valid"] is True
    assert len(body["ledger"]) >= 2


def test_gateway_isolation_on_category_mismatch(client):
    from app.payments.gateway import MockRazorpayGateway

    payload = base_payload("tr_category_1")
    payload["proposal"]["category"] = "electronics"

    res = client.post("/api/v1/agent/checkout", json=payload)
    body = res.json()
    assert body["status"] == "BLOCKED"
    assert MockRazorpayGateway.call_count == 0
