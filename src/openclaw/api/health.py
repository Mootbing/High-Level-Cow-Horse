from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text

from openclaw.config import settings
from openclaw.db.session import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check():
    checks = {"api": "ok"}

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    r = None
    try:
        r = Redis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    finally:
        if r:
            await r.aclose()

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
