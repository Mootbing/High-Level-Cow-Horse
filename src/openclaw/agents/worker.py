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

# Pipeline stage auto-advancement: when a task for a specific agent starts/completes,
# advance the project to the corresponding pipeline stage (never backward).
_PIPELINE_ORDER = ["intake", "design", "build", "qa", "deployed"]
_ADVANCE_ON_START = {"designer": "design", "engineer": "build", "qa": "qa"}
_ADVANCE_ON_COMPLETE = {"qa": "deployed"}


async def _advance_pipeline(project_id: str, new_status: str) -> None:
    """Advance project pipeline status forward (never backward)."""
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.services.project_service import get_project, update_project_status
        async with async_session_factory() as session:
            project = await get_project(session, project_id)
            if not project:
                return
            current_idx = _PIPELINE_ORDER.index(project.status) if project.status in _PIPELINE_ORDER else -1
            new_idx = _PIPELINE_ORDER.index(new_status) if new_status in _PIPELINE_ORDER else -1
            if new_idx > current_idx:
                await update_project_status(session, project_id, new_status)
                logger.info("pipeline_advanced", project_id=project_id, old=project.status, new=new_status)
    except Exception as e:
        logger.warning("pipeline_advance_failed", project_id=project_id, error=str(e)[:200])


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

                    # Create a Task record in DB so dashboard can track progress
                    db_task_id = None
                    msg_type_check = data.get("type", "")
                    project_id = data.get("project_id")
                    if msg_type_check == "task" and project_id and agent_type not in ("reviewer",):
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import create_task
                            prompt_text = data.get("payload", {}).get("prompt", "")
                            # Build a short title from the prompt
                            title = prompt_text[:100].split("\n")[0] if prompt_text else f"{agent_type} task"
                            async with async_session_factory() as session:
                                db_task = await create_task(
                                    session=session,
                                    project_id=project_id,
                                    agent_type=agent_type,
                                    title=title,
                                    description=prompt_text[:2000] if prompt_text else None,
                                    input_data={"entry_id": entry_id, "task_id": task_id, "source_agent": data.get("source_agent")},
                                )
                                db_task_id = str(db_task.id)
                                # Mark as in_progress
                                from openclaw.services.task_service import update_task_status
                                await update_task_status(session, db_task_id, "in_progress")
                            logger.info("db_task_created", agent=agent_type, db_task_id=db_task_id)
                            # Advance pipeline when specific agents start work
                            if agent_type in _ADVANCE_ON_START:
                                await _advance_pipeline(project_id, _ADVANCE_ON_START[agent_type])
                        except Exception as te:
                            logger.warning("db_task_create_failed", agent=agent_type, error=str(te)[:200])

                    # Fresh agent instance per task to prevent cross-task state bleed
                    agent = agent_cls()
                    from openclaw.queue.streams import HEAVY_AGENTS
                    timeout = settings.HEAVY_TASK_TIMEOUT_S if agent_type in HEAVY_AGENTS else settings.TASK_TIMEOUT_S
                    result = await asyncio.wait_for(
                        agent.process_task(data),
                        timeout=timeout,
                    )
                    await consumer.ack(entry_id)
                    logger.info(
                        "message_processed", agent=agent_type, entry_id=entry_id
                    )

                    # Update Task record to completed
                    if db_task_id:
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import update_task_status
                            result_full = ""
                            if isinstance(result, dict):
                                result_full = result.get("result", str(result))
                            else:
                                result_full = str(result)
                            async with async_session_factory() as session:
                                await update_task_status(
                                    session, db_task_id, "completed",
                                    output_data={"result": result_full},
                                )
                            logger.info("db_task_completed", agent=agent_type, db_task_id=db_task_id)
                            # Advance pipeline on completion (e.g., QA passed → deployed)
                            if agent_type in _ADVANCE_ON_COMPLETE and project_id:
                                await _advance_pipeline(project_id, _ADVANCE_ON_COMPLETE[agent_type])
                        except Exception as te:
                            logger.warning("db_task_update_failed", agent=agent_type, error=str(te)[:200])

                    # Auto-report results back to the source agent
                    # IMPORTANT: reviewer results should NOT auto-report back to avoid infinite loops
                    # (reviewer reviews inbound -> reports back to inbound -> inbound re-processes -> reviewer reviews again)
                    source = data.get("source_agent")
                    msg_type = data.get("type", "")
                    logger.info("auto_report_check", agent=agent_type, source=source, msg_type=msg_type)
                    if source and source != agent_type and msg_type == "task" and (agent_type != "reviewer" or source == "project_manager"):
                        try:
                            from openclaw.queue.producer import publish as _publish
                            # Truncate result to prevent huge messages
                            result_str = ""
                            if isinstance(result, dict):
                                result_str = result.get("result", str(result))
                            else:
                                result_str = str(result)
                            result_str = result_str[:6000]  # Cap at 6KB (must preserve asset URLs)

                            await _publish(source, {
                                "type": "result",
                                "source_agent": agent_type,
                                "target_agent": source,
                                "project_id": data.get("project_id"),
                                "task_id": data.get("task_id"),
                                "payload": {
                                    "result": result_str,
                                    "original_prompt": data.get("payload", {}).get("prompt", "")[:200],
                                    "db_task_id": db_task_id,
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

                    # Reviewer results are logged only — NOT forwarded to PM stream.
                    # Forwarding caused late-arriving failures to re-trigger pipeline
                    # steps the PM had already advanced past, wasting tokens.
                    if agent_type == "reviewer":
                        reviewed_agent = data.get("payload", {}).get("source", "")
                        logger.info("reviewer_completed", reviewed_agent=reviewed_agent)

                    # Send to reviewer for validation
                    # Skip: reviewer itself, CEO, learning, research, tasks from reviewer (avoid loops),
                    # and PM-delegated pipeline steps (PM already has QA as quality gate —
                    # async reviewer feedback arrives too late and causes duplicate work)
                    is_from_reviewer = data.get("source_agent") == "reviewer" or data.get("type") == "result"
                    is_pm_pipeline = data.get("source_agent") == "project_manager"
                    if agent_type not in ("reviewer", "ceo", "learning", "research") and not is_from_reviewer and not is_pm_pipeline:
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
                except asyncio.TimeoutError:
                    logger.error(
                        "task_timed_out",
                        agent=agent_type,
                        entry_id=entry_id,
                        timeout_s=settings.TASK_TIMEOUT_S,
                    )
                    await consumer.send_to_deadletter(
                        entry_id, data, f"Task timed out after {settings.TASK_TIMEOUT_S}s"
                    )
                    # Mark DB task as failed if we created one
                    if db_task_id:
                        try:
                            async with async_session_factory() as session:
                                await update_task_status(session, db_task_id, "failed")
                        except Exception:
                            pass
                    continue
                except Exception as e:
                    # Mark DB task as failed
                    if db_task_id:
                        try:
                            async with async_session_factory() as session:
                                await update_task_status(
                                    session, db_task_id, "failed",
                                    error=str(e)[:1000],
                                )
                        except Exception:
                            pass

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
