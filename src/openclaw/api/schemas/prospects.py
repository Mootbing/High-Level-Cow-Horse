"""Prospect schemas."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from .common import BaseSchema


class ProspectRead(BaseSchema):
    id: UUID
    url: str
    company_name: str | None = None
    tagline: str | None = None
    contact_emails: list[Any] = []
    brand_colors: list[Any] = []
    fonts: list[Any] = []
    logo_url: str | None = None
    phone_number: str | None = None
    social_links: dict[str, Any] = {}
    industry: str | None = None
    tech_stack: list[Any] = []
    raw_data: dict[str, Any] = {}
    latitude: float | None = None
    longitude: float | None = None
    scraped_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    project_count: int = 0
    site_problems_count: int = 0


class ProspectGeo(BaseSchema):
    id: UUID
    company_name: str | None = None
    url: str
    latitude: float
    longitude: float
    industry: str | None = None
    project_status: str | None = None


class ProspectUpdate(BaseSchema):
    company_name: str | None = None
    tagline: str | None = None
    industry: str | None = None
    latitude: float | None = None
    longitude: float | None = None
