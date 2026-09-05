from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PAYTRIX"
    environment: str = "development"
    database_url: str = "sqlite:///./paytrix.db"
    prne_secret: str = "paytrix_dev_prne_secret_change_in_prod"

    # Safety kernel thresholds
    price_scalping_threshold_pct: float = 10.0
    velocity_max_transactions: int = 3
    velocity_window_minutes: int = 10
    velocity_max_spend_paise: int = 500_000  # ₹5,000

    intent_auto_execute_threshold: float = 0.85
    intent_confirmation_threshold: float = 0.50

    demo_user_id: str = "usr_demo_123"
    demo_user_balance_paise: int = 1_000_000  # ₹10,000

    # --- Agent identity & rate limiting ---
    demo_agent_id: str = "agt_demo_ui"
    demo_agent_key: str = "demo_agent_secret_key_do_not_use_in_prod"
    agent_rate_limit_per_minute: int = 30

    # --- Idempotency / replay protection ---
    idempotency_ttl_hours: int = 24

    # --- Step-up confirmation ---
    confirmation_secret: str = "paytrix_dev_confirmation_secret_change_in_prod"
    confirmation_token_ttl_seconds: int = 300  # 5 minutes

    class Config:
        env_file = ".env"


settings = Settings()
