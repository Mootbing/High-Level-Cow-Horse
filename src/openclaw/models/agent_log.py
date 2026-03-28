"""AgentLog model — agent conversation log."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project
    from .task import Task


class AgentLog(UUIDPrimaryKeyMixin, Base):
    """Records individual messages in agent conversations for audit and debugging."""

    __tablename__ = "agent_logs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id"),
    )
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="agent_logs")
    task: Mapped[Task | None] = relationship(back_populates="agent_logs")

    def __repr__(self) -> str:
        return (
            f"<AgentLog(id={self.id!r}, agent_type={self.agent_type!r}, "
            f"role={self.role!r})>"
        )
