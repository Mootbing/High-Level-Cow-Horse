"""Auto-scales Railway heavy worker replicas based on Redis queue depth.

Runs as a background task in the light worker process. Every AUTOSCALE_POLL_SECONDS,
checks how many pending messages are in the heavy agent streams (designer, engineer, qa).
If total pending > threshold, scales up. If queues are drained, scales back down.

Scaling formula:
  desired_replicas = clamp(ceil(total_pending / threshold), min, max)

This means:
  0 pending   → 1 replica  (min)
  3 pending   → 1 replica
  4 pending   → 2 replicas
  9 pending   → 3 replicas
  15+ pending → 5 replicas (max)
"""

from __future__ import annotations

import asyncio
import math

import httpx
import redis.asyncio as redis
import structlog

from openclaw.config import settings
from openclaw.queue.streams import HEAVY_AGENTS, stream_name, group_name

logger = structlog.get_logger()

RAILWAY_GQL_URL = "https://backboard.railway.app/graphql/v2"


async def get_queue_depths() -> dict[str, int]:
    """Get pending message count for each heavy agent stream."""
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    depths = {}
    try:
        for agent_type in HEAVY_AGENTS:
            stream = stream_name(agent_type)
            group = group_name(agent_type)
            try:
                info = await r.xinfo_groups(stream)
                for g in info:
                    if g.get("name") == group:
                        depths[agent_type] = g.get("lag", 0) or 0
                        break
                else:
                    # Fallback: count stream length
                    depths[agent_type] = await r.xlen(stream)
            except redis.ResponseError:
                depths[agent_type] = 0
    finally:
        await r.aclose()
    return depths


def compute_desired_replicas(total_pending: int) -> int:
    """Compute desired replica count from total pending messages."""
    if total_pending <= 0:
        return settings.AUTOSCALE_MIN_REPLICAS
    desired = math.ceil(total_pending / max(settings.AUTOSCALE_QUEUE_THRESHOLD, 1))
    return max(settings.AUTOSCALE_MIN_REPLICAS, min(desired, settings.AUTOSCALE_MAX_REPLICAS))


async def get_current_replicas() -> int | None:
    """Get current replica count from Railway API."""
    if not settings.RAILWAY_API_TOKEN or not settings.RAILWAY_HEAVY_SERVICE_ID:
        return None

    query = """
    query($serviceId: String!) {
        service(id: $serviceId) {
            serviceInstances {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            RAILWAY_GQL_URL,
            json={"query": query, "variables": {"serviceId": settings.RAILWAY_HEAVY_SERVICE_ID}},
            headers={
                "Authorization": f"Bearer {settings.RAILWAY_API_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code != 200:
            logger.warning("railway_api_error", status=resp.status_code, body=resp.text[:200])
            return None
        data = resp.json()
        edges = (
            data.get("data", {})
            .get("service", {})
            .get("serviceInstances", {})
            .get("edges", [])
        )
        return len(edges)


async def set_replicas(count: int) -> bool:
    """Set replica count for the heavy worker service via Railway API."""
    if not settings.RAILWAY_API_TOKEN or not settings.RAILWAY_HEAVY_SERVICE_ID:
        return False

    mutation = """
    mutation($serviceId: String!, $input: ServiceInstanceUpdateInput!) {
        serviceInstanceUpdate(serviceId: $serviceId, input: $input)
    }
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            RAILWAY_GQL_URL,
            json={
                "query": mutation,
                "variables": {
                    "serviceId": settings.RAILWAY_HEAVY_SERVICE_ID,
                    "input": {"numReplicas": count},
                },
            },
            headers={
                "Authorization": f"Bearer {settings.RAILWAY_API_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code == 200 and "errors" not in resp.json():
            logger.info("replicas_set", count=count)
            return True
        logger.warning("set_replicas_failed", status=resp.status_code, body=resp.text[:200])
        return False


async def autoscale_loop(shutdown: asyncio.Event) -> None:
    """Main autoscaler loop. Runs until shutdown is set."""
    if not settings.AUTOSCALE_ENABLED:
        logger.info("autoscaler_disabled")
        return

    if not settings.RAILWAY_API_TOKEN or not settings.RAILWAY_HEAVY_SERVICE_ID:
        logger.info("autoscaler_skipped", reason="RAILWAY_API_TOKEN or RAILWAY_HEAVY_SERVICE_ID not set")
        return

    logger.info(
        "autoscaler_started",
        poll_seconds=settings.AUTOSCALE_POLL_SECONDS,
        min=settings.AUTOSCALE_MIN_REPLICAS,
        max=settings.AUTOSCALE_MAX_REPLICAS,
        threshold=settings.AUTOSCALE_QUEUE_THRESHOLD,
    )

    last_desired = settings.AUTOSCALE_MIN_REPLICAS

    while not shutdown.is_set():
        try:
            depths = await get_queue_depths()
            total_pending = sum(depths.values())
            desired = compute_desired_replicas(total_pending)

            if desired != last_desired:
                logger.info(
                    "scaling",
                    depths=depths,
                    total_pending=total_pending,
                    current=last_desired,
                    desired=desired,
                )
                success = await set_replicas(desired)
                if success:
                    last_desired = desired
            else:
                logger.debug("autoscaler_check", depths=depths, total=total_pending, replicas=desired)

        except Exception as e:
            logger.error("autoscaler_error", error=str(e))

        # Wait for next poll, but break early on shutdown
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=settings.AUTOSCALE_POLL_SECONDS)
            break  # shutdown was set
        except asyncio.TimeoutError:
            pass  # Normal — poll again
