"""Inter-agent message schema."""

from datetime import datetime, timezone
from typing import Literal
import uuid

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    type: Literal["task", "result", "query", "error"]
    source_agent: str
    target_agent: str
    project_id: str | None = None
    task_id: str | None = None
    payload: dict = Field(default_factory=dict)
    priority: int = 5
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_publish_dict(self) -> dict:
        return self.model_dump(mode="json")
