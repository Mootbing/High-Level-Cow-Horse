"""Prospect model — scraped prospect data."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .email_log import EmailLog
    from .project import Project


class Prospect(UUIDPrimaryKeyMixin, Base):
    """Stores scraped prospect/company data."""

    __tablename__ = "prospects"

    url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    tagline: Mapped[str | None] = mapped_column()
    contact_emails: Mapped[list[Any]] = mapped_column(JSON, default=list)
    brand_colors: Mapped[list[Any]] = mapped_column(JSON, default=list)
    fonts: Mapped[list[Any]] = mapped_column(JSON, default=list)
    logo_url: Mapped[str | None] = mapped_column(String(512))
    social_links: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    industry: Mapped[str | None] = mapped_column(String(128))
    tech_stack: Mapped[list[Any]] = mapped_column(JSON, default=list)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    scraped_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    projects: Mapped[list[Project]] = relationship(back_populates="prospect")
    email_logs: Mapped[list[EmailLog]] = relationship(back_populates="prospect")

    def __repr__(self) -> str:
        return f"<Prospect(id={self.id!r}, company_name={self.company_name!r}, url={self.url!r})>"
