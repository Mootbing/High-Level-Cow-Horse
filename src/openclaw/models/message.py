"""Message model — inbound/outbound message log (iMessage, WhatsApp)."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project


class Message(UUIDPrimaryKeyMixin, Base):
    """Stores inbound and outbound messages across channels."""

    __tablename__ = "messages"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    channel: Mapped[str] = mapped_column(String(16), default="imessage")
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(128))
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    message_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str | None] = mapped_column()
    media_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="received")
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id!r}, channel={self.channel!r}, "
            f"direction={self.direction!r}, phone_number={self.phone_number!r})>"
        )
