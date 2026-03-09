from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://leadflow:leadflow_pass@localhost:5432/leadflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Encryption
    ENCRYPTION_KEY: str = "change-me-32-byte-key-in-prod!!"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # App
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"

    # SMTP
    SMTP_DEFAULT_HOST: str = "smtp.gmail.com"
    SMTP_DEFAULT_PORT: int = 587

    # Webhooks
    WEBHOOK_SECRET: str = "change-me"
    SENDGRID_INBOUND_WEBHOOK_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Agent defaults
    AGENT_OUTBOUND_INTERVAL_SECONDS: int = 300
    AGENT_REPLY_HANDLER_INTERVAL_SECONDS: int = 120
    AGENT_SCORING_INTERVAL_SECONDS: int = 1800
    AGENT_RESEARCH_INTERVAL_SECONDS: int = 3600

    # Scoring
    HANDOFF_SCORE_THRESHOLD: int = 75
    MAX_AUTONOMOUS_REPLIES: int = 5
    AI_CONFIDENCE_THRESHOLD: float = 0.7

    # Rate limits
    DEFAULT_DAILY_SEND_LIMIT: int = 50

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
