"""Generic background task worker — polls the tasks table and dispatches to handlers."""

from __future__ import annotations

import asyncio
from datetime import datetime

import structlog
from sqlalchemy import select

from openclaw.db.session import async_session_factory
from openclaw.models.task import Task
from openclaw.workers.handlers import HANDLERS

logger = structlog.get_logger()

POLL_INTERVAL = 5  # seconds


async def _process_next() -> bool:
    """Find and process one pending task. Returns True if a task was processed."""
    async with async_session_factory() as session:
        stmt = (
            select(Task)
            .where(Task.status == "pending", Task.agent_type.in_(list(HANDLERS.keys())))
            .order_by(Task.priority.asc(), Task.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return False

        handler = HANDLERS.get(task.agent_type)
        if not handler:
            task.status = "failed"
            task.error = f"Unknown agent_type: {task.agent_type}"
            task.completed_at = datetime.utcnow()
            await session.commit()
            logger.error("task_unknown_type", task_id=str(task.id), agent_type=task.agent_type)
            return True

        # Mark in progress
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        await session.commit()

        logger.info("task_start", task_id=str(task.id), agent_type=task.agent_type)

        try:
            output = await handler(task, session)
            task.output_data = output or {}
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            logger.info("task_done", task_id=str(task.id), agent_type=task.agent_type)
        except Exception as exc:
            task.retry_count += 1
            error_msg = str(exc)[:500]
            if task.retry_count >= task.max_retries:
                task.status = "failed"
                task.error = error_msg
                task.completed_at = datetime.utcnow()
                logger.error("task_failed", task_id=str(task.id), error=error_msg)
            else:
                task.status = "pending"
                task.error = error_msg
                logger.warning("task_retry", task_id=str(task.id), retry=task.retry_count, error=error_msg)

        await session.commit()
        return True


async def run_task_worker():
    """Poll loop — runs until cancelled."""
    logger.info("task_worker_started")
    while True:
        try:
            processed = await _process_next()
            if not processed:
                await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("task_worker_stopped")
            return
        except Exception as exc:
            logger.error("task_worker_loop_error", error=str(exc)[:300])
            await asyncio.sleep(POLL_INTERVAL)
