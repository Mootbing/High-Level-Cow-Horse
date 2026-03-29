from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Clarmi Design Studio"
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

    # GitHub (bot account for generated website repos)
    GITHUB_PAT: str = ""

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

    # Dashboard
    DASHBOARD_SECRET: str = "changeme-openclaw-dashboard"

    # Railway auto-scaling
    RAILWAY_API_TOKEN: str = ""
    RAILWAY_HEAVY_SERVICE_ID: str = ""  # Service ID for heavy workers
    AUTOSCALE_ENABLED: bool = True
    AUTOSCALE_MIN_REPLICAS: int = 1
    AUTOSCALE_MAX_REPLICAS: int = 5
    AUTOSCALE_QUEUE_THRESHOLD: int = 3  # Pending messages to trigger scale-up
    AUTOSCALE_POLL_SECONDS: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
