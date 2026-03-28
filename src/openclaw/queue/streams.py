"""Redis Streams definitions and consumer group initialization."""

import redis.asyncio as redis

from openclaw.config import settings

AGENT_TYPES = [
    "ceo",
    "project_manager",
    "inbound",
    "designer",
    "engineer",
    "qa",
    "outbound",
    "client_comms",
    "research",
    "learning",
]


def stream_name(agent_type: str) -> str:
    return f"stream:agent:{agent_type}"


DEADLETTER_STREAM = "stream:agent:deadletter"


def group_name(agent_type: str) -> str:
    return f"group:{agent_type}:workers"


async def init_streams(redis_client: redis.Redis) -> None:
    """Create streams and consumer groups if they don't exist."""
    for agent_type in AGENT_TYPES:
        stream = stream_name(agent_type)
        group = group_name(agent_type)
        try:
            await redis_client.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    # Deadletter stream
    try:
        await redis_client.xgroup_create(
            DEADLETTER_STREAM, "deadletter:workers", id="0", mkstream=True
        )
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
