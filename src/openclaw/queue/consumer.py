"""Redis Streams consumer with blocking reads, ack/nack, retry, and dead-letter."""

import asyncio
import json
import uuid

import structlog
import redis.asyncio as redis

from openclaw.config import settings
from openclaw.queue.streams import stream_name, group_name, DEADLETTER_STREAM

logger = structlog.get_logger()


class StreamConsumer:
    """Redis Streams consumer for a specific agent type."""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.stream = stream_name(agent_type)
        self.group = group_name(agent_type)
        self.consumer_name = f"{agent_type}-{uuid.uuid4().hex[:8]}"
        self.redis: redis.Redis | None = None

    async def connect(self) -> None:
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        if self.redis:
            await self.redis.aclose()

    async def read(
        self, count: int = 1, block_ms: int = 5000
    ) -> list[tuple[str, dict]]:
        """Read messages from the stream. Returns list of (entry_id, message_data)."""
        results = await self.redis.xreadgroup(
            groupname=self.group,
            consumername=self.consumer_name,
            streams={self.stream: ">"},
            count=count,
            block=block_ms,
        )
        messages = []
        if results:
            for _stream, entries in results:
                for entry_id, fields in entries:
                    try:
                        data = json.loads(fields.get("data", "{}"))
                        messages.append((entry_id, data))
                    except json.JSONDecodeError:
                        await self.send_to_deadletter(
                            entry_id, {"raw": str(fields)[:500]}, "JSONDecodeError"
                        )
        return messages

    async def ack(self, entry_id: str) -> None:
        await self.redis.xack(self.stream, self.group, entry_id)

    async def send_to_deadletter(
        self, entry_id: str, message: dict, error: str
    ) -> None:
        """Move a failed message to the dead-letter stream."""
        await self.redis.xadd(
            DEADLETTER_STREAM,
            {
                "original_stream": self.stream,
                "original_id": entry_id,
                "data": json.dumps(message),
                "error": error,
            },
        )
        await self.ack(entry_id)

    async def heartbeat(self) -> None:
        """Send a heartbeat to Redis."""
        key = f"health:{self.agent_type}:{self.consumer_name}"
        await self.redis.set(key, "alive", ex=30)
