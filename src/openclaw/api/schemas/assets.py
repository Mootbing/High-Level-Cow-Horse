"""Asset schemas."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from .common import BaseSchema


class AssetRead(BaseSchema):
    id: UUID
    project_id: UUID | None = None
    task_id: UUID | None = None
    asset_type: str
    filename: str
    storage_path: str
    mime_type: str | None = None
    metadata_: dict[str, Any] = {}
    created_at: datetime.datetime | None = None
