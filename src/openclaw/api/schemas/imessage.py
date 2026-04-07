"""iMessage webhook schemas."""

from __future__ import annotations

from pydantic import BaseModel


class IncomingIMessage(BaseModel):
    """Payload from the TypeScript iMessage listener."""

    phone_number: str
    message_text: str
    chat_guid: str
    message_guid: str
    timestamp: int


class IMessageReply(BaseModel):
    """Response sent back to the TypeScript listener."""

    reply_text: str
    status: str = "ok"
