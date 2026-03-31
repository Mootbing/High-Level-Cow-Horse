"""Metrics schemas."""

from __future__ import annotations

import datetime
from uuid import UUID

from .common import BaseSchema


class MetricRead(BaseSchema):
    id: UUID
    metric_date: datetime.date
    avg_lighthouse: float | None = None
    avg_fix_loops: float | None = None
    avg_project_hours: float | None = None
    total_projects: int | None = None
    knowledge_entries: int | None = None
    prompt_version: int | None = None
    notes: str | None = None
    created_at: datetime.datetime | None = None


class DashboardStats(BaseSchema):
    total_prospects: int = 0
    total_projects: int = 0
    active_projects: int = 0
    deployed_projects: int = 0
    emails_sent: int = 0
    emails_draft: int = 0
    tasks_in_progress: int = 0
    tasks_completed: int = 0
    avg_lighthouse: float | None = None
    projects_by_status: dict[str, int] = {}
