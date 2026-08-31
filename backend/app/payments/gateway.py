import uuid


class MockRazorpayGateway:
    """Mock payment gateway. The class-level call_count exists purely so
    tests/telemetry can prove the Safety Kernel never touched the gateway
    when a transaction was blocked (Razorpay Call Count = 0)."""

    call_count: int = 0

    @classmethod
    def charge(cls, amount_paise: int) -> dict:
        cls.call_count += 1
        return {
            "status": "success",
            "gateway_ref": f"rzp_mock_{uuid.uuid4().hex[:16]}",
            "amount_paise": amount_paise,
        }

    @classmethod
    def reset(cls) -> None:
        cls.call_count = 0


gateway = MockRazorpayGateway()
