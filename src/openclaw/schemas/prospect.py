"""Prospect schemas for API request/response validation."""

from pydantic import BaseModel


class ProspectCreate(BaseModel):
    url: str
    company_name: str | None = None


class ProspectResponse(BaseModel):
    id: str
    url: str
    company_name: str | None = None
    contact_emails: list = []
    brand_colors: list = []
    fonts: list = []
    industry: str | None = None

    model_config = {"from_attributes": True}
