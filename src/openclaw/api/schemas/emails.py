"""Email log schemas."""

from __future__ import annotations

import datetime
from uuid import UUID

from .common import BaseSchema


class EmailLogRead(BaseSchema):
    id: UUID
    prospect_id: UUID | None = None
    project_id: UUID | None = None
    to_email: str
    subject: str | None = None
    body: str | None = None
    edited_subject: str | None = None
    edited_body: str | None = None
    status: str = "draft"
    gmail_message_id: str | None = None
    created_at: datetime.datetime | None = None
    sent_at: datetime.datetime | None = None
    prospect_company: str | None = None
    project_name: str | None = None
