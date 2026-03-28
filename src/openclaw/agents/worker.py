"""Agent worker process. Run with: python -m openclaw.agents.worker --agent-type ceo"""

from __future__ import annotations

import argparse
import asyncio
import signal

import structlog
import redis.asyncio as redis

from openclaw.config import settings
from openclaw.queue.consumer import StreamConsumer
from openclaw.queue.streams import init_streams

logger = structlog.get_logger()

# Agent registry -- maps agent_type to its class
AGENT_REGISTRY: dict[str, type] = {}


def register_agent(agent_type: str):
    """Decorator to register an agent class."""

    def decorator(cls):
        AGENT_REGISTRY[agent_type] = cls
        cls.agent_type = agent_type
        return cls

    return decorator


def _load_agents():
    """Import all agent modules to trigger registration."""
    from openclaw.agents import (  # noqa: F401
        ceo,
        project_manager,
        inbound,
        designer,
        engineer,
        qa,
        outbound,
        client_comms,
        research,
        learning,
    )


async def _run_single_worker(agent_type: str, shutdown: asyncio.Event) -> None:
    """Worker loop for a single agent type."""
    agent_cls = AGENT_REGISTRY[agent_type]
    agent = agent_cls()
    consumer = StreamConsumer(agent_type)
    await consumer.connect()

    logger.info("worker_started", agent=agent_type, consumer=consumer.consumer_name)

    while not shutdown.is_set():
        try:
            messages = await consumer.read(count=1, block_ms=5000)

            if not messages:
                await consumer.heartbeat()
                continue

            for entry_id, data in messages:
                logger.info(
                    "processing_message", agent=agent_type, entry_id=entry_id
                )
                try:
                    result = await agent.process_task(data)
                    await consumer.ack(entry_id)
                    logger.info(
                        "message_processed", agent=agent_type, entry_id=entry_id
                    )
                except Exception as e:
                    retry_count = data.get("_retry_count", 0)
                    max_retries = data.get("_max_retries", 3)
                    if retry_count < max_retries:
                        data["_retry_count"] = retry_count + 1
                        from openclaw.queue.producer import publish

                        await publish(agent_type, data)
                        await consumer.ack(entry_id)
                        logger.warning(
                            "message_retried",
                            agent=agent_type,
                            retry=retry_count + 1,
                            error=str(e),
                        )
                    else:
                        await consumer.send_to_deadletter(entry_id, data, str(e))
                        logger.error(
                            "message_deadlettered",
                            agent=agent_type,
                            error=str(e),
                        )

                await consumer.heartbeat()

        except Exception as e:
            logger.error("worker_error", agent=agent_type, error=str(e))
            await asyncio.sleep(5)

    await consumer.close()
    logger.info("worker_stopped", agent=agent_type)


async def run_worker(agent_type: str) -> None:
    """Run a single agent worker."""
    _load_agents()

    if agent_type not in AGENT_REGISTRY:
        logger.error(
            "unknown_agent_type",
            agent_type=agent_type,
            available=list(AGENT_REGISTRY.keys()),
        )
        return

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_streams(r)
    await r.aclose()

    shutdown = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown.set())

    await _run_single_worker(agent_type, shutdown)


async def run_all_workers() -> None:
    """Run ALL agent workers in a single process (for Railway / single-container deploy)."""
    _load_agents()

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_streams(r)
    await r.aclose()

    shutdown = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown.set())

    logger.info("starting_all_workers", agents=list(AGENT_REGISTRY.keys()))

    tasks = [
        asyncio.create_task(_run_single_worker(agent_type, shutdown))
        for agent_type in AGENT_REGISTRY
    ]

    await asyncio.gather(*tasks)
    logger.info("all_workers_stopped")


async def run_tier(tier: str) -> None:
    """Run agents for a specific tier (light or heavy).

    Light tier: CEO, PM, Inbound, Outbound, Comms, Research, Learning + autoscaler
    Heavy tier: Designer, Engineer, QA (horizontally scalable)
    """
    from openclaw.queue.streams import LIGHT_AGENTS, HEAVY_AGENTS

    _load_agents()

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_streams(r)
    await r.aclose()

    shutdown = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown.set())

    if tier == "light":
        agent_types = [a for a in LIGHT_AGENTS if a in AGENT_REGISTRY]
        logger.info("starting_light_tier", agents=agent_types)
        tasks = [
            asyncio.create_task(_run_single_worker(at, shutdown))
            for at in agent_types
        ]
        # Run autoscaler alongside light workers
        from openclaw.autoscaler import autoscale_loop
        tasks.append(asyncio.create_task(autoscale_loop(shutdown)))

    elif tier == "heavy":
        agent_types = [a for a in HEAVY_AGENTS if a in AGENT_REGISTRY]
        logger.info("starting_heavy_tier", agents=agent_types)
        tasks = [
            asyncio.create_task(_run_single_worker(at, shutdown))
            for at in agent_types
        ]
    else:
        logger.error("unknown_tier", tier=tier, available=["light", "heavy"])
        return

    await asyncio.gather(*tasks)
    logger.info("tier_stopped", tier=tier)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Agent Worker")
    parser.add_argument("--agent-type", default=None, help="Single agent type to run")
    parser.add_argument("--all", action="store_true", help="Run all agents in one process")
    parser.add_argument(
        "--tier",
        choices=["light", "heavy"],
        default=None,
        help="Run a tier: 'light' (CEO,PM,Comms + autoscaler) or 'heavy' (Designer,Engineer,QA)",
    )
    args = parser.parse_args()

    if args.tier:
        asyncio.run(run_tier(args.tier))
    elif args.all or args.agent_type is None:
        asyncio.run(run_all_workers())
    else:
        asyncio.run(run_worker(args.agent_type))


if __name__ == "__main__":
    main()
