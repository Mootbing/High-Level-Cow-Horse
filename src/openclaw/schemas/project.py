"""Project schemas for API request/response validation."""

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    brief: str
    client_phone: str | None = None
    priority: int = 5


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    deployed_url: str | None = None

    model_config = {"from_attributes": True}
