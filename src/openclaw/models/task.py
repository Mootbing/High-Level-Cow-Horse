"""Task model — individual work items executed by agents."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .agent_log import AgentLog
    from .asset import Asset
    from .project import Project


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an agent task within a project, supporting hierarchical sub-tasks."""

    __tablename__ = "tasks"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id"),
    )
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column()
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime.datetime | None] = mapped_column()
    completed_at: Mapped[datetime.datetime | None] = mapped_column()

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="tasks")
    parent_task: Mapped[Task | None] = relationship(
        back_populates="sub_tasks", remote_side="Task.id",
    )
    sub_tasks: Mapped[list[Task]] = relationship(back_populates="parent_task")
    assets: Mapped[list[Asset]] = relationship(back_populates="task")
    agent_logs: Mapped[list[AgentLog]] = relationship(back_populates="task")

    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id!r}, agent_type={self.agent_type!r}, "
            f"status={self.status!r})>"
        )
