"""EmailLog model — outbound email log."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project
    from .prospect import Prospect


class EmailLog(UUIDPrimaryKeyMixin, Base):
    """Tracks outbound emails sent to prospects and clients."""

    __tablename__ = "email_log"

    prospect_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prospects.id"),
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), default="sent")
    gmail_message_id: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    prospect: Mapped[Prospect | None] = relationship(back_populates="email_logs")
    project: Mapped[Project | None] = relationship(back_populates="email_logs")

    def __repr__(self) -> str:
        return (
            f"<EmailLog(id={self.id!r}, to_email={self.to_email!r}, "
            f"status={self.status!r})>"
        )
