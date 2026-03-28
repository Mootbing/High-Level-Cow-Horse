"""Knowledge models — knowledge_base, prompt_versions, improvement_metrics."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .project import Project


class KnowledgeBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores reusable knowledge entries (code patterns, design rules, lessons learned)."""

    __tablename__ = "knowledge_base"

    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512))
    source_type: Mapped[str | None] = mapped_column(String(32))
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list[Any]] = mapped_column(JSON, default=list)
    code_snippet: Mapped[str | None] = mapped_column()
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    expires_at: Mapped[datetime.datetime | None] = mapped_column()

    # Relationships
    project: Mapped[Project | None] = relationship(
        back_populates="knowledge_entries",
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeBase(id={self.id!r}, category={self.category!r}, "
            f"title={self.title!r})>"
        )


class PromptVersion(UUIDPrimaryKeyMixin, Base):
    """Tracks versioned prompt templates with quality metrics."""

    __tablename__ = "prompt_versions"

    template_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column()
    avg_qa_score: Mapped[float | None] = mapped_column(Float)
    projects_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    def __repr__(self) -> str:
        return (
            f"<PromptVersion(id={self.id!r}, template_name={self.template_name!r}, "
            f"version={self.version!r})>"
        )


class ImprovementMetric(UUIDPrimaryKeyMixin, Base):
    """Daily aggregate metrics tracking system improvement over time."""

    __tablename__ = "improvement_metrics"

    metric_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    avg_lighthouse: Mapped[float | None] = mapped_column(Float)
    avg_fix_loops: Mapped[float | None] = mapped_column(Float)
    avg_project_hours: Mapped[float | None] = mapped_column(Float)
    total_projects: Mapped[int | None] = mapped_column(Integer)
    knowledge_entries: Mapped[int | None] = mapped_column(Integer)
    prompt_version: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    def __repr__(self) -> str:
        return (
            f"<ImprovementMetric(id={self.id!r}, metric_date={self.metric_date!r})>"
        )
