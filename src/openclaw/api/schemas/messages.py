"""Message schemas."""

from __future__ import annotations

import datetime
from uuid import UUID

from .common import BaseSchema


class MessageRead(BaseSchema):
    id: UUID
    project_id: UUID | None = None
    channel: str = "imessage"
    direction: str
    external_message_id: str | None = None
    phone_number: str
    message_type: str
    content: str | None = None
    media_url: str | None = None
    status: str = "received"
    created_at: datetime.datetime | None = None
    project_name: str | None = None
