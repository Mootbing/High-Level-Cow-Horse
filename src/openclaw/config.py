from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://openclaw:changeme@localhost:5432/openclaw"

    # Google AI (Nano Banana + Veo 3)
    GOOGLE_AI_API_KEY: str = ""

    # Google Places API (New)
    GOOGLE_PLACES_API_KEY: str = ""

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

    # API
    API_PORT: int = 8000
    AUDIT_WORKER_PORT: int = 8002
    DASHBOARD_CORS_ORIGIN: str = "http://localhost:3001"
    WEBSITE_CORS_ORIGIN: str = "https://clarmi.com"

    # Storage
    STORAGE_PATH: str = "./data/projects"

    # Lead Generation / Prospecting
    PROSPECTING_ENABLED: bool = False
    PROSPECTING_INDUSTRIES: str = ""  # Comma-separated: "restaurant,salon,dentist"
    PROSPECTING_LOCATIONS: str = ""   # Comma-separated: "Austin TX,Dallas TX"
    PROSPECTING_DAILY_LIMIT: int = 50

    # Postgres (for docker)
    POSTGRES_PASSWORD: str = "changeme"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
