"""WhatsApp webhook schemas."""

from pydantic import BaseModel


class WhatsAppMessage(BaseModel):
    wa_message_id: str
    phone: str
    text: str
    message_type: str = "text"
    media_url: str | None = None
