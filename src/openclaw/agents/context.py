"""Context load/save/summarize for agent conversations."""

from __future__ import annotations

import json

import structlog
import redis.asyncio as redis
from sqlalchemy import select

from openclaw.config import settings
from openclaw.db.session import async_session_factory
from openclaw.models.agent_log import AgentLog

logger = structlog.get_logger()


def _context_key(agent_type: str, project_id: str) -> str:
    return f"context:{agent_type}:{project_id}"


async def load_context(
    agent_type: str, project_id: str, max_messages: int = 50
) -> list[dict]:
    """Load conversation context from Redis (fast) or PostgreSQL (fallback)."""
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    key = _context_key(agent_type, project_id)

    # Try Redis first
    cached = await r.get(key)
    await r.aclose()
    if cached:
        return json.loads(cached)[-max_messages:]

    # Fallback to PostgreSQL
    async with async_session_factory() as session:
        stmt = (
            select(AgentLog)
            .where(
                AgentLog.agent_type == agent_type,
                AgentLog.project_id == project_id,
            )
            .order_by(AgentLog.created_at.desc())
            .limit(max_messages)
        )
        result = await session.execute(stmt)
        logs = result.scalars().all()

    messages = [
        {"role": log.role, "content": log.content} for log in reversed(logs)
    ]

    # Cache in Redis
    if messages:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.set(key, json.dumps(messages), ex=3600)
        await r.aclose()

    return messages


async def save_context(
    agent_type: str,
    project_id: str,
    messages: list[dict],
    task_id: str | None = None,
) -> None:
    """Save conversation context to Redis and PostgreSQL."""
    # Save to Redis
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    key = _context_key(agent_type, project_id)
    await r.set(key, json.dumps(messages), ex=3600)
    await r.aclose()

    # Save new messages to PostgreSQL
    async with async_session_factory() as session:
        for msg in messages[-2:]:  # Save the latest exchange
            log = AgentLog(
                project_id=project_id,
                task_id=task_id,
                agent_type=agent_type,
                role=msg["role"],
                content=msg["content"],
            )
            session.add(log)
        await session.commit()
