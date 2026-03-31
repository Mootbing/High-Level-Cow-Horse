"""Knowledge schemas."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from .common import BaseSchema


class KnowledgeRead(BaseSchema):
    id: UUID
    category: str
    title: str
    content: str
    source_url: str | None = None
    tags: list[Any] = []
    code_snippet: str | None = None
    relevance_score: float = 1.0
    project_id: UUID | None = None
    expires_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
