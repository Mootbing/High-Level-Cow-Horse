"""Task schemas for API request/response validation."""

from pydantic import BaseModel


class TaskCreate(BaseModel):
    project_id: str
    agent_type: str
    title: str
    description: str | None = None
    priority: int = 5
    input_data: dict = {}


class TaskResponse(BaseModel):
    id: str
    project_id: str
    agent_type: str
    title: str
    status: str

    model_config = {"from_attributes": True}
