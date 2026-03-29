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

from openclaw.agents.registry import AGENT_REGISTRY, register_agent  # noqa: F401

logger = structlog.get_logger()


def _load_agents():
    """Import all agent modules to trigger registration."""
    import importlib
    agent_modules = [
        "ceo", "project_manager", "inbound", "designer", "engineer",
        "qa", "reviewer", "outbound", "client_comms", "research", "learning",
    ]
    for mod_name in agent_modules:
        try:
            importlib.import_module(f"openclaw.agents.{mod_name}")
        except Exception as e:
            logger.error("agent_import_failed", module=mod_name, error=str(e))
    logger.info("agents_loaded", registry=list(AGENT_REGISTRY.keys()))


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
                    # Dedup: skip if this task_id was already processed
                    task_id = data.get("task_id")
                    if task_id:
                        dedup_key = f"openclaw:dedup:{agent_type}:{task_id}"
                        is_new = await consumer.redis.set(dedup_key, "1", nx=True, ex=3600)
                        if not is_new:
                            logger.info("duplicate_task_skipped", agent=agent_type, task_id=task_id)
                            await consumer.ack(entry_id)
                            continue

                    result = await agent.process_task(data)
                    await consumer.ack(entry_id)
                    logger.info(
                        "message_processed", agent=agent_type, entry_id=entry_id
                    )

                    # Auto-report results back to the source agent
                    # IMPORTANT: reviewer results should NOT auto-report back to avoid infinite loops
                    # (reviewer reviews inbound -> reports back to inbound -> inbound re-processes -> reviewer reviews again)
                    source = data.get("source_agent")
                    msg_type = data.get("type", "")
                    logger.info("auto_report_check", agent=agent_type, source=source, msg_type=msg_type)
                    if source and source != agent_type and msg_type == "task" and agent_type != "reviewer":
                        try:
                            from openclaw.queue.producer import publish as _publish
                            # Truncate result to prevent huge messages
                            result_str = ""
                            if isinstance(result, dict):
                                result_str = result.get("result", str(result))
                            else:
                                result_str = str(result)
                            result_str = result_str[:3000]  # Cap at 3KB

                            await _publish(source, {
                                "type": "result",
                                "source_agent": agent_type,
                                "target_agent": source,
                                "project_id": data.get("project_id"),
                                "task_id": data.get("task_id"),
                                "payload": {
                                    "result": result_str,
                                    "original_prompt": data.get("payload", {}).get("prompt", "")[:200],
                                },
                            })
                            logger.info(
                                "auto_reported_result",
                                agent=agent_type,
                                target=source,
                                result_len=len(result_str),
                            )
                        except Exception as re:
                            logger.error("auto_report_failed", agent=agent_type, error=str(re))

                    # Send to reviewer for validation
                    # Skip: reviewer itself, CEO, learning, research, and tasks that came FROM the reviewer (avoid loops)
                    is_from_reviewer = data.get("source_agent") == "reviewer" or data.get("type") == "result"
                    if agent_type not in ("reviewer", "ceo", "learning", "research") and not is_from_reviewer:
                        try:
                            result_preview = ""
                            if isinstance(result, dict):
                                result_preview = str(result)[:2000]
                            else:
                                result_preview = str(result)[:2000]
                            await _publish("reviewer", {
                                "type": "task",
                                "source_agent": agent_type,
                                "target_agent": "reviewer",
                                "payload": {
                                    "prompt": (
                                        f"Review the output of the {agent_type} agent.\n"
                                        f"Original task: {data.get('payload', {}).get('prompt', '')[:300]}\n\n"
                                        f"Result:\n{result_preview}\n\n"
                                        f"Verify this step completed correctly. Use verify_url or verify_file tools if needed."
                                    ),
                                    "source": agent_type,
                                },
                            })
                            logger.info("sent_to_reviewer", agent=agent_type)
                        except Exception as re:
                            logger.warning("reviewer_send_failed", error=str(re))

                    # Publish event for dashboard
                    try:
                        from openclaw.tools.messaging import publish_dashboard_event
                        await publish_dashboard_event({
                            "type": "task_update",
                            "agent_type": agent_type,
                            "status": "completed",
                            "entry_id": entry_id,
                        })
                    except Exception as de:
                        logger.warning("dashboard_event_failed", error=str(de))
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
    parser = argparse.ArgumentParser(description="Clarmi Design Studio Agent Worker")
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
