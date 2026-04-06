"""Deployment model — deployment records."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project


class Deployment(UUIDPrimaryKeyMixin, Base):
    """Tracks deployment attempts and their status for each project."""

    __tablename__ = "deployments"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    vercel_deployment_id: Mapped[str | None] = mapped_column(String(128))
    url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="deployments")

    def __repr__(self) -> str:
        return (
            f"<Deployment(id={self.id!r}, status={self.status!r}, "
            f"url={self.url!r})>"
        )
