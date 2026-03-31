"""Skill runner — replaces the old agent worker process.

Discovers skills dynamically via :mod:`~openclaw.runtime.skill_loader`,
creates Redis Streams infrastructure for each, and runs a consumer loop
per skill.  The runner creates one ``AsyncAnthropic`` client at startup
and injects it into every skill instance.

Run with::

    python -m openclaw.runtime.skill_runner --all
    python -m openclaw.runtime.skill_runner --skill designer
"""

from __future__ import annotations

import argparse
import asyncio
import signal
from typing import Any

import structlog
import redis.asyncio as aioredis

from openclaw.config import settings
from openclaw.queue.consumer import StreamConsumer
from openclaw.queue.streams import DEADLETTER_STREAM, HEAVY_AGENTS, stream_name, group_name
from openclaw.runtime.skill_base import BaseSkill, SkillContext, SkillResult
from openclaw.runtime.skill_loader import load_all_skills, load_skill

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Pipeline stage auto-advancement (ported from worker.py)
# ---------------------------------------------------------------------------
_PIPELINE_ORDER = ["intake", "design", "build", "qa", "deployed"]
_ADVANCE_ON_START: dict[str, str] = {"designer": "design", "engineer": "build", "qa": "qa"}
_ADVANCE_ON_COMPLETE: dict[str, str] = {"qa": "deployed"}


async def _advance_pipeline(project_id: str, new_status: str) -> None:
    """Advance project pipeline status forward (never backward)."""
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.services.project_service import get_project, update_project_status

        async with async_session_factory() as session:
            project = await get_project(session, project_id)
            if not project:
                return
            current_idx = (
                _PIPELINE_ORDER.index(project.status)
                if project.status in _PIPELINE_ORDER
                else -1
            )
            new_idx = (
                _PIPELINE_ORDER.index(new_status)
                if new_status in _PIPELINE_ORDER
                else -1
            )
            if new_idx > current_idx:
                await update_project_status(session, project_id, new_status)
                logger.info(
                    "pipeline_advanced",
                    project_id=project_id,
                    old=project.status,
                    new=new_status,
                )
    except Exception as e:
        logger.warning(
            "pipeline_advance_failed", project_id=project_id, error=str(e)[:200]
        )


# ---------------------------------------------------------------------------
# Dynamic stream initialisation
# ---------------------------------------------------------------------------

async def _init_skill_streams(
    redis_client: aioredis.Redis,
    skill_names: list[str],
) -> None:
    """Create Redis Streams and consumer groups for every loaded skill.

    Mirrors the old ``init_streams()`` but operates on the dynamic set of
    discovered skills rather than a hardcoded list.
    """
    for name in skill_names:
        stream = stream_name(name)
        group = group_name(name)
        try:
            await redis_client.xgroup_create(stream, group, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    # Deadletter stream (shared across all skills)
    try:
        await redis_client.xgroup_create(
            DEADLETTER_STREAM, "deadletter:workers", id="0", mkstream=True
        )
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    logger.info("skill_streams_initialised", skills=skill_names)


# ---------------------------------------------------------------------------
# Per-skill consumer loop
# ---------------------------------------------------------------------------

async def _run_skill_loop(
    skill_name: str,
    skill_cls: type[BaseSkill],
    claude_client: Any,
    shutdown: asyncio.Event,
) -> None:
    """Consumer loop for a single skill type.

    Faithfully reproduces the dedup, retry, deadletter, timeout, auto-report,
    reviewer-send, pipeline-advancement, and dashboard-event logic from the
    old ``worker.py._run_single_worker``.
    """
    consumer = StreamConsumer(skill_name)
    await consumer.connect()

    logger.info("skill_loop_started", skill=skill_name, consumer=consumer.consumer_name)

    while not shutdown.is_set():
        try:
            messages = await consumer.read(count=1, block_ms=5000)

            if not messages:
                await consumer.heartbeat()
                continue

            for entry_id, data in messages:
                logger.info("processing_message", skill=skill_name, entry_id=entry_id)

                # Track the DB task id so we can update it on success / failure
                db_task_id: str | None = None

                try:
                    # -- Dedup ------------------------------------------------
                    task_id = data.get("task_id")
                    if task_id:
                        dedup_key = f"openclaw:dedup:{skill_name}:{task_id}"
                        is_new = await consumer.redis.set(
                            dedup_key, "1", nx=True, ex=3600
                        )
                        if not is_new:
                            logger.info(
                                "duplicate_task_skipped",
                                skill=skill_name,
                                task_id=task_id,
                            )
                            await consumer.ack(entry_id)
                            continue

                    # -- Create DB Task record --------------------------------
                    msg_type_check = data.get("type", "")
                    project_id = data.get("project_id")
                    if (
                        msg_type_check == "task"
                        and project_id
                        and skill_name not in ("reviewer",)
                    ):
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import (
                                create_task,
                                update_task_status,
                            )

                            prompt_text = data.get("payload", {}).get("prompt", "")
                            title = (
                                prompt_text[:100].split("\n")[0]
                                if prompt_text
                                else f"{skill_name} task"
                            )

                            async with async_session_factory() as session:
                                db_task = await create_task(
                                    session=session,
                                    project_id=project_id,
                                    agent_type=skill_name,
                                    title=title,
                                    description=(
                                        prompt_text[:2000] if prompt_text else None
                                    ),
                                    input_data={
                                        "entry_id": entry_id,
                                        "task_id": task_id,
                                        "source_agent": data.get("source_agent"),
                                    },
                                )
                                db_task_id = str(db_task.id)
                                await update_task_status(
                                    session, db_task_id, "in_progress"
                                )

                            logger.info(
                                "db_task_created",
                                skill=skill_name,
                                db_task_id=db_task_id,
                            )

                            # Advance pipeline when specific skills start work
                            if skill_name in _ADVANCE_ON_START:
                                await _advance_pipeline(
                                    project_id, _ADVANCE_ON_START[skill_name]
                                )
                        except Exception as te:
                            logger.warning(
                                "db_task_create_failed",
                                skill=skill_name,
                                error=str(te)[:200],
                            )

                    # -- Instantiate skill and execute ------------------------
                    skill = skill_cls(claude_client=claude_client)

                    context = SkillContext(
                        project_id=data.get("project_id"),
                        task_id=data.get("task_id"),
                        payload=data.get("payload", {}),
                        source_skill=data.get("source_agent"),
                        message=data,
                    )

                    timeout = (
                        settings.HEAVY_TASK_TIMEOUT_S
                        if skill_name in HEAVY_AGENTS
                        else skill_cls.timeout
                    )
                    skill_result: SkillResult = await asyncio.wait_for(
                        skill.execute(context),
                        timeout=timeout,
                    )

                    await consumer.ack(entry_id)
                    logger.info(
                        "message_processed",
                        skill=skill_name,
                        entry_id=entry_id,
                        success=skill_result.success,
                    )

                    # Build a legacy-compatible result dict for downstream use
                    result: dict[str, Any] = {
                        "status": "completed" if skill_result.success else "failed",
                        "result": skill_result.result,
                        **skill_result.data,
                    }

                    # -- Update DB Task to completed --------------------------
                    if db_task_id:
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import (
                                update_task_status,
                            )

                            result_full = skill_result.result or str(result)

                            async with async_session_factory() as session:
                                await update_task_status(
                                    session,
                                    db_task_id,
                                    "completed",
                                    output_data={"result": result_full},
                                )
                            logger.info(
                                "db_task_completed",
                                skill=skill_name,
                                db_task_id=db_task_id,
                            )

                            # Advance pipeline on completion
                            if skill_name in _ADVANCE_ON_COMPLETE and project_id:
                                await _advance_pipeline(
                                    project_id, _ADVANCE_ON_COMPLETE[skill_name]
                                )
                        except Exception as te:
                            logger.warning(
                                "db_task_update_failed",
                                skill=skill_name,
                                error=str(te)[:200],
                            )

                    # -- Auto-report results back to the source skill ---------
                    source = data.get("source_agent")
                    msg_type = data.get("type", "")
                    logger.info(
                        "auto_report_check",
                        skill=skill_name,
                        source=source,
                        msg_type=msg_type,
                    )
                    if (
                        source
                        and source != skill_name
                        and msg_type == "task"
                        and (skill_name != "reviewer" or source == "project_manager")
                    ):
                        try:
                            from openclaw.queue.producer import publish as _publish

                            result_str = skill_result.result or str(result)
                            result_str = result_str[:6000]  # Cap at 6 KB

                            await _publish(
                                source,
                                {
                                    "type": "result",
                                    "source_agent": skill_name,
                                    "target_agent": source,
                                    "project_id": data.get("project_id"),
                                    "task_id": data.get("task_id"),
                                    "payload": {
                                        "result": result_str,
                                        "original_prompt": data.get("payload", {})
                                        .get("prompt", "")[:200],
                                        "db_task_id": db_task_id,
                                    },
                                },
                            )
                            logger.info(
                                "auto_reported_result",
                                skill=skill_name,
                                target=source,
                                result_len=len(result_str),
                            )
                        except Exception as re:
                            logger.error(
                                "auto_report_failed",
                                skill=skill_name,
                                error=str(re),
                            )

                    # -- Reviewer result logging (no forwarding to PM) --------
                    if skill_name == "reviewer":
                        reviewed_skill = data.get("payload", {}).get("source", "")
                        logger.info(
                            "reviewer_completed", reviewed_skill=reviewed_skill
                        )

                    # -- Send to reviewer for validation ----------------------
                    is_from_reviewer = (
                        data.get("source_agent") == "reviewer"
                        or data.get("type") == "result"
                    )
                    is_pm_pipeline = data.get("source_agent") == "project_manager"
                    if (
                        skill_name
                        not in ("reviewer", "ceo", "learning", "research")
                        and not is_from_reviewer
                        and not is_pm_pipeline
                    ):
                        try:
                            from openclaw.queue.producer import publish as _publish

                            result_preview = (
                                skill_result.result[:2000]
                                if skill_result.result
                                else str(result)[:2000]
                            )
                            await _publish(
                                "reviewer",
                                {
                                    "type": "task",
                                    "source_agent": skill_name,
                                    "target_agent": "reviewer",
                                    "payload": {
                                        "prompt": (
                                            f"Review the output of the {skill_name} skill.\n"
                                            f"Original task: {data.get('payload', {}).get('prompt', '')[:300]}\n\n"
                                            f"Result:\n{result_preview}\n\n"
                                            f"Verify this step completed correctly. "
                                            f"Use verify_url or verify_file tools if needed."
                                        ),
                                        "source": skill_name,
                                    },
                                },
                            )
                            logger.info("sent_to_reviewer", skill=skill_name)
                        except Exception as re:
                            logger.warning(
                                "reviewer_send_failed", error=str(re)
                            )

                    # -- Dashboard event --------------------------------------
                    try:
                        from openclaw.tools.messaging import publish_dashboard_event

                        await publish_dashboard_event(
                            {
                                "type": "task_update",
                                "agent_type": skill_name,
                                "status": "completed",
                                "entry_id": entry_id,
                            }
                        )
                    except Exception as de:
                        logger.warning("dashboard_event_failed", error=str(de))

                except asyncio.TimeoutError:
                    timeout_val = (
                        settings.HEAVY_TASK_TIMEOUT_S
                        if skill_name in HEAVY_AGENTS
                        else skill_cls.timeout
                    )
                    logger.error(
                        "task_timed_out",
                        skill=skill_name,
                        entry_id=entry_id,
                        timeout_s=timeout_val,
                    )
                    await consumer.send_to_deadletter(
                        entry_id, data, f"Task timed out after {timeout_val}s"
                    )
                    # Mark DB task as failed
                    if db_task_id:
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import (
                                update_task_status,
                            )

                            async with async_session_factory() as session:
                                await update_task_status(
                                    session, db_task_id, "failed"
                                )
                        except Exception:
                            pass
                    continue

                except Exception as e:
                    # Mark DB task as failed
                    if db_task_id:
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import (
                                update_task_status,
                            )

                            async with async_session_factory() as session:
                                await update_task_status(
                                    session,
                                    db_task_id,
                                    "failed",
                                    error=str(e)[:1000],
                                )
                        except Exception:
                            pass

                    # Retry logic
                    retry_count = data.get("_retry_count", 0)
                    max_retries = data.get("_max_retries", 3)
                    if retry_count < max_retries:
                        data["_retry_count"] = retry_count + 1
                        from openclaw.queue.producer import publish as _publish

                        await _publish(skill_name, data)
                        await consumer.ack(entry_id)
                        logger.warning(
                            "message_retried",
                            skill=skill_name,
                            retry=retry_count + 1,
                            error=str(e),
                        )
                    else:
                        await consumer.send_to_deadletter(
                            entry_id, data, str(e)
                        )
                        logger.error(
                            "message_deadlettered",
                            skill=skill_name,
                            error=str(e),
                        )

                await consumer.heartbeat()

        except Exception as e:
            logger.error("skill_loop_error", skill=skill_name, error=str(e))
            await asyncio.sleep(5)

    await consumer.close()
    logger.info("skill_loop_stopped", skill=skill_name)


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------

async def _get_claude_client() -> Any:
    """Obtain a shared AsyncAnthropic client.

    Tries the project's ``claude_login`` helper first; falls back to a
    plain ``AsyncAnthropic`` constructed from settings if the auth module
    is not available.
    """
    try:
        from openclaw.auth.claude_login import get_claude_client

        return await get_claude_client()
    except (ImportError, ModuleNotFoundError):
        logger.info("claude_login_unavailable_using_api_key")
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def run_skill(name: str, shutdown: asyncio.Event) -> None:
    """Load and run a single skill by name."""
    skill_cls = load_skill(name)
    claude_client = await _get_claude_client()

    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _init_skill_streams(r, [skill_cls.name])
    await r.aclose()

    await _run_skill_loop(skill_cls.name, skill_cls, claude_client, shutdown)


async def run_all_skills(shutdown: asyncio.Event) -> None:
    """Discover all skills and run consumer loops concurrently."""
    registry = load_all_skills()
    if not registry:
        logger.error("no_skills_found")
        return

    claude_client = await _get_claude_client()

    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _init_skill_streams(r, list(registry.keys()))
    await r.aclose()

    logger.info("starting_all_skills", skills=list(registry.keys()))

    tasks = [
        asyncio.create_task(
            _run_skill_loop(skill_name, skill_cls, claude_client, shutdown)
        )
        for skill_name, skill_cls in registry.items()
    ]

    await asyncio.gather(*tasks)
    logger.info("all_skills_stopped")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point: ``python -m openclaw.runtime.skill_runner``."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Skill Runner — dynamic skill-based worker process"
    )
    parser.add_argument(
        "--skill",
        default=None,
        help="Run a single skill by name (must match a skills/<name>/ directory)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all discovered skills in one process",
    )
    args = parser.parse_args()

    shutdown = asyncio.Event()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown.set())

    if args.skill:
        loop.run_until_complete(run_skill(args.skill, shutdown))
    else:
        # Default: run all skills (--all flag is optional)
        loop.run_until_complete(run_all_skills(shutdown))


if __name__ == "__main__":
    main()
