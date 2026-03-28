"""Publish messages to agent Redis Streams."""

import json
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis

from openclaw.config import settings
from openclaw.queue.streams import stream_name

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def publish(target_agent: str, message: dict) -> str:
    """Publish a message to an agent's stream. Returns the stream entry ID."""
    r = await get_redis()
    msg_id = message.get("id", uuid.uuid4().hex)
    payload = {
        "id": msg_id,
        "data": json.dumps(message),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entry_id = await r.xadd(stream_name(target_agent), payload)
    return entry_id
