"""Response schemas for dashboard API endpoints."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel


# --- Overview ---

class OverviewResponse(BaseModel):
    active_projects: int
    total_projects: int
    pending_tasks: int
    completed_tasks: int
    total_prospects: int
    total_emails_sent: int
    knowledge_entries: int


# --- Projects ---

class ProjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    priority: int
    deployed_url: str | None
    task_count: int
    completed_task_count: int
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    id: uuid.UUID
    agent_type: str
    title: str
    status: str
    priority: int
    parent_task_id: uuid.UUID | None
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    created_at: datetime.datetime | None

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    brief: str | None
    status: str
    priority: int
    deployed_url: str | None
    metadata_: dict[str, Any]
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None
    tasks: list[TaskSummary]

    model_config = {"from_attributes": True}


# --- Agents ---

class AgentStatus(BaseModel):
    agent_type: str
    tier: str
    status: str  # "alive" or "dead"
    queue_depth: int
    last_heartbeat: str | None


class AgentsStatusResponse(BaseModel):
    agents: list[AgentStatus]
    total_pending: int


# --- Prospects ---

class ProspectSummary(BaseModel):
    id: uuid.UUID
    url: str
    company_name: str | None
    industry: str | None
    contact_emails: list[Any]
    brand_colors: list[Any]
    tech_stack: list[Any]
    scraped_at: datetime.datetime | None

    model_config = {"from_attributes": True}


# --- Emails ---

class EmailLogSummary(BaseModel):
    id: uuid.UUID
    to_email: str
    subject: str | None
    status: str
    sent_at: datetime.datetime | None
    prospect_id: uuid.UUID | None
    project_id: uuid.UUID | None

    model_config = {"from_attributes": True}


# --- Knowledge ---

class KnowledgeEntrySummary(BaseModel):
    id: uuid.UUID
    category: str
    title: str
    content: str
    relevance_score: float
    tags: list[Any]
    source_url: str | None
    created_at: datetime.datetime | None

    model_config = {"from_attributes": True}


# --- Messages (chat history) ---

class MessageSummary(BaseModel):
    id: uuid.UUID
    direction: str
    content: str | None
    media_url: str | None
    created_at: datetime.datetime | None

    model_config = {"from_attributes": True}
