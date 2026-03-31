"""Deployment schemas."""

from __future__ import annotations

import datetime
from uuid import UUID

from .common import BaseSchema


class DeploymentRead(BaseSchema):
    id: UUID
    project_id: UUID | None = None
    deployment_id: str | None = None
    url: str | None = None
    status: str = "pending"
    created_at: datetime.datetime | None = None
