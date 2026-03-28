from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "OpenClaw"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://openclaw:password@localhost:5432/openclaw"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # WhatsApp
    WA_VERIFY_TOKEN: str = ""
    WA_ACCESS_TOKEN: str = ""
    WA_PHONE_NUMBER_ID: str = ""
    WA_APP_SECRET: str = ""
    OWNER_PHONE: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Google AI
    GOOGLE_AI_API_KEY: str = ""

    # Firecrawl
    FIRECRAWL_API_KEY: str = ""

    # Gmail
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    GMAIL_SENDER_EMAIL: str = ""

    # Vercel
    VERCEL_TOKEN: str = ""
    VERCEL_TEAM_ID: str = ""
    DEPLOY_DOMAIN: str = "openclaw.site"

    # Storage
    STORAGE_PATH: str = "/data/projects"

    # Postgres (for docker)
    POSTGRES_PASSWORD: str = "changeme"

    # Research Agent
    RESEARCH_INTERVAL_HOURS: int = 6
    RESEARCH_SOURCES: str = "awwwards,dribbble,css_tricks,smashing_magazine,codrops"

    # Learning Agent
    LEARNING_DAILY_CRON: str = "03:00"
    RELEVANCE_DECAY_HALFLIFE_DAYS: int = 90

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
