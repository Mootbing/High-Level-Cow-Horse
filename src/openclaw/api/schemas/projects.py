"""Project schemas."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from .common import BaseSchema


class ProjectRead(BaseSchema):
    id: UUID
    name: str
    slug: str
    client_phone: str | None = None
    brief: str | None = None
    status: str = "intake"
    priority: int = 5
    prospect_id: UUID | None = None
    metadata_: dict[str, Any] = {}
    deployed_url: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    prospect_company: str | None = None
    task_count: int = 0
    email_count: int = 0


class ProjectStats(BaseSchema):
    total: int = 0
    by_status: dict[str, int] = {}


class ProjectUpdate(BaseSchema):
    name: str | None = None
    status: str | None = None
    priority: int | None = None
    brief: str | None = None
