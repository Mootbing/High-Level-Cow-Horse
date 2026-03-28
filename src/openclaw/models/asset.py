"""Asset model — generated assets (images, HTML, code, etc.)."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project
    from .task import Task


class Asset(UUIDPrimaryKeyMixin, Base):
    """Tracks generated assets (HTML files, images, code) linked to projects and tasks."""

    __tablename__ = "assets"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id"),
    )
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="assets")
    task: Mapped[Task | None] = relationship(back_populates="assets")

    def __repr__(self) -> str:
        return (
            f"<Asset(id={self.id!r}, asset_type={self.asset_type!r}, "
            f"filename={self.filename!r})>"
        )
