from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text

from openclaw.config import settings
from openclaw.db.session import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check():
    checks = {"api": "ok"}

    # Check PostgreSQL
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    # Check Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
