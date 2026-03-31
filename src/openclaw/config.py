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

    # Anthropic (API key kept as fallback — prefer `openclaw login` OAuth)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # OpenClaw auth & runtime
    OPENCLAW_CREDENTIALS_PATH: str = ""  # Override for creds file; default ~/.openclaw/credentials.json
    SKILLS_DIR: str = ""  # Override for skills directory path
    EC2_PUBLIC_IP: str = ""  # Public IP for webhook URL configuration
    MAX_PARALLEL_PROJECTS: int = 5  # Limit parallel project execution

    # Google AI (image/video gen — still uses API key)
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
    JWT_SECRET: str = ""  # Falls back to DASHBOARD_SECRET if empty
    JWT_EXPIRY_HOURS: int = 24

    # Worker
    TASK_TIMEOUT_S: int = 600  # 10 minutes max per task (light agents)
    HEAVY_TASK_TIMEOUT_S: int = 1800  # 30 minutes for designer/engineer/QA

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
