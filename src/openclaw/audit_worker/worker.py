"""Audit-specific task worker — polls for website_audit tasks only."""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC

import structlog
from sqlalchemy import select

from openclaw.audit_worker.handler import handle_website_audit
from openclaw.db.session import async_session_factory
from openclaw.models.task import Task

logger = structlog.get_logger()

POLL_INTERVAL = 5  # seconds


async def _process_next() -> bool:
    """Find and process one pending website_audit task. Returns True if processed."""
    async with async_session_factory() as session:
        stmt = (
            select(Task)
            .where(Task.status == "pending", Task.agent_type == "website_audit")
            .order_by(Task.priority.asc(), Task.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return False

        # Mark in progress
        task.status = "in_progress"
        task.started_at = datetime.now(UTC).replace(tzinfo=None)
        await session.commit()

        logger.info("audit_task_start", task_id=str(task.id))

        try:
            output = await handle_website_audit(task, session)
            task.output_data = output or {}
            task.status = "completed"
            task.completed_at = datetime.now(UTC).replace(tzinfo=None)
            logger.info("audit_task_done", task_id=str(task.id))
        except Exception as exc:
            task.retry_count += 1
            error_msg = str(exc)[:500]
            if task.retry_count >= task.max_retries:
                task.status = "failed"
                task.error = error_msg
                task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                logger.error("audit_task_failed", task_id=str(task.id), error=error_msg)
            else:
                task.status = "pending"
                task.error = error_msg
                logger.warning(
                    "audit_task_retry",
                    task_id=str(task.id),
                    retry=task.retry_count,
                    error=error_msg,
                )

        await session.commit()
        return True


async def run_audit_worker():
    """Poll loop — runs until cancelled."""
    logger.info("audit_worker_started")
    while True:
        try:
            processed = await _process_next()
            if not processed:
                await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("audit_worker_stopped")
            return
        except Exception as exc:
            logger.error("audit_worker_error", error=str(exc)[:300])
            await asyncio.sleep(POLL_INTERVAL)
