"""Project model — top-level entity for client projects."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .agent_log import AgentLog
    from .asset import Asset
    from .deployment import Deployment
    from .email_log import EmailLog
    from .knowledge import KnowledgeBase
    from .message import Message
    from .prospect import Prospect
    from .task import Task


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a client project managed by Clarmi Design Studio agents."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(20))
    brief: Mapped[str | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), default="intake")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    prospect_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prospects.id"),
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict,
    )
    deployed_url: Mapped[str | None] = mapped_column(String(512))

    # Relationships
    prospect: Mapped[Prospect | None] = relationship(back_populates="projects")
    tasks: Mapped[list[Task]] = relationship(back_populates="project")
    messages: Mapped[list[Message]] = relationship(back_populates="project")
    email_logs: Mapped[list[EmailLog]] = relationship(back_populates="project")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
    agent_logs: Mapped[list[AgentLog]] = relationship(back_populates="project")
    deployments: Mapped[list[Deployment]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
    knowledge_entries: Mapped[list[KnowledgeBase]] = relationship(
        back_populates="project",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id!r}, slug={self.slug!r}, status={self.status!r})>"
