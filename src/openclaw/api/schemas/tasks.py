"""Task schemas."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from .common import BaseSchema


class TaskRead(BaseSchema):
    id: UUID
    project_id: UUID | None = None
    parent_task_id: UUID | None = None
    agent_type: str
    title: str
    description: str | None = None
    status: str = "pending"
    priority: int = 5
    input_data: dict[str, Any] = {}
    output_data: dict[str, Any] = {}
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    project_name: str | None = None
