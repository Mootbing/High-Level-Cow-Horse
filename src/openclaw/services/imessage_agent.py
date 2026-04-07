"""iMessage agent service — routes incoming /clarmi messages to Claude with MCP tools."""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from typing import TYPE_CHECKING

import structlog

from openclaw.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Strip ANTHROPIC_API_KEY so Claude CLI uses stored OAuth credentials
_CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

# Owner system prompt — full admin access
OWNER_SYSTEM_PROMPT = """You are the Clarmi Design Studio assistant, responding via iMessage to the agency owner.

You have FULL admin access to all projects, prospects, emails, tasks, and tools.
The owner can ask you to:
- Check project status, list projects, view deployments
- Trigger builds, deploys, QA checks on any project
- View and manage leads, prospects, emails
- Query the dashboard API at http://localhost:{api_port}/api/v1/ for any data
- Run any MCP tool available in the Clarmi toolkit
- Manage client projects, run lead generation, send emails

Be concise — this is iMessage, not a document. Keep responses under 500 chars when possible.
Use short paragraphs, no markdown headers. Bullet points are fine for lists.

Current date: {{date}}
"""

# Client system prompt — scoped to their project
CLIENT_SYSTEM_PROMPT = """You are the Clarmi Design Studio assistant, responding via iMessage to a client.

You are helping a client with their project. Be warm, friendly, and professional.
You can ONLY access this client's project — never expose other client data.

Project details:
- Name: {project_name}
- Slug: {project_slug}
- Status: {project_status}
- Deployed URL: {deployed_url}

You can help the client:
- Check their project/deployment status
- Make code changes to their site (read_code, edit_code) — always use slug "{project_slug}"
- Rebuild and redeploy their site (verify_build, deploy) — always use slug "{project_slug}"
- Answer questions about their site

When calling any tool, always use project_name="{project_slug}".
For any changes, always deploy a preview first (deploy_preview), then ask for approval
before merging to production.

Be concise — this is iMessage. Keep responses under 500 chars when possible.
No markdown headers. Bullet points are fine.

Current date: {{date}}
"""


def normalize_phone(phone: str) -> str:
    """Normalize phone number for DB matching.

    Strips +, spaces, dashes. Removes leading country code '1' for US numbers
    if the result is 10 digits.
    """
    cleaned = re.sub(r"[+\s\-()]", "", phone)
    # If 11 digits starting with 1, strip the 1 (US country code)
    if len(cleaned) == 11 and cleaned.startswith("1"):
        cleaned = cleaned[1:]
    return cleaned


def _is_owner(phone: str) -> bool:
    """Check if the phone number belongs to the owner."""
    normalized = normalize_phone(phone)
    owner_normalized = normalize_phone(settings.OWNER_PHONE)
    return normalized == owner_normalized


async def _load_conversation_history(
    phone: str, session: "AsyncSession", limit: int = 10
) -> str:
    """Load recent messages for this phone number as conversation context."""
    from sqlalchemy import select
    from openclaw.models.message import Message

    stmt = (
        select(Message)
        .where(Message.phone_number == phone)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = list(reversed(result.scalars().all()))

    if not messages:
        return ""

    lines = []
    for m in messages:
        role = "User" if m.direction == "inbound" else "Clarmi"
        lines.append(f"{role}: {m.content or '[media]'}")

    return "\n".join(lines)


async def find_projects_for_phone(
    phone: str, session: "AsyncSession"
) -> list:
    """Find projects associated with a phone number."""
    from sqlalchemy import select
    from openclaw.models.project import Project

    normalized = normalize_phone(phone)

    # Try exact match first, then match with common phone format variants
    variants = {normalized}
    # If 10 digits, also match with leading 1
    if len(normalized) == 10:
        variants.add("1" + normalized)
        variants.add("+1" + normalized)
    # If 11+ digits starting with country code
    if len(normalized) == 11 and normalized.startswith("1"):
        variants.add(normalized[1:])
        variants.add("+" + normalized)

    stmt = select(Project).where(
        Project.client_phone.isnot(None),
        Project.client_phone.in_(variants),
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _call_claude(prompt: str, allowed_tools: str = "*", timeout: int = 120) -> str:
    """Shell out to claude CLI with tool access."""
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if allowed_tools:
        cmd.extend(["--allowedTools", allowed_tools])

    proc = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_CLEAN_ENV,
    )
    if proc.returncode != 0:
        detail = proc.stderr[:500] or proc.stdout[:500]
        logger.error("claude_cli_failed", exit_code=proc.returncode, detail=detail)
        raise RuntimeError(f"Claude CLI failed (exit {proc.returncode}): {detail}")

    try:
        claude_output = json.loads(proc.stdout)
        return claude_output.get("result", proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout


async def process_message(
    phone: str,
    text: str,
    session: "AsyncSession",
    projects: list | None = None,
) -> str:
    """Process an incoming /clarmi message and return a reply.

    Determines role (owner vs client) from phone number, builds context,
    and dispatches to Claude with appropriate tool access.

    Args:
        phone: Normalized phone number of the sender.
        text: Message text with /clarmi prefix already stripped.
        session: Database session for conversation history.
        projects: Pre-fetched projects for this phone (avoids double query).
    """
    from datetime import date

    today = date.today().isoformat()

    # Load conversation history
    history = await _load_conversation_history(phone, session)
    history_block = f"\n\nRecent conversation:\n{history}" if history else ""

    if _is_owner(phone):
        system = OWNER_SYSTEM_PROMPT.replace("{api_port}", str(settings.API_PORT)).replace("{{date}}", today)
        prompt = f"""{system}{history_block}

Owner's message: {text}"""

        try:
            return await _call_claude(prompt, allowed_tools="*", timeout=120)
        except Exception as e:
            logger.exception("owner_message_failed", phone=phone)
            return f"Something went wrong processing your request: {str(e)[:200]}"

    # Client flow — use pre-fetched projects or look them up
    if projects is None:
        projects = await find_projects_for_phone(phone, session)

    if not projects:
        return (
            "I don't recognize this number. "
            "If you're a Clarmi client, please contact us to link your number to your project."
        )

    if len(projects) == 1:
        project = projects[0]
        system = CLIENT_SYSTEM_PROMPT.format(
            project_name=project.name,
            project_slug=project.slug,
            project_status=project.status,
            deployed_url=project.deployed_url or "Not yet deployed",
        ).replace("{{date}}", today)

        # Scope tools to safe operations (MCP tool names use mcp__clarmi-tools__ prefix)
        safe_tools = [
            "mcp__clarmi-tools__get_project_status",
            "mcp__clarmi-tools__read_code",
            "mcp__clarmi-tools__edit_code",
            "mcp__clarmi-tools__list_files",
            "mcp__clarmi-tools__verify_build",
            "mcp__clarmi-tools__deploy",
            "mcp__clarmi-tools__deploy_preview",
            "mcp__clarmi-tools__approve_preview",
        ]
        allowed = ",".join(safe_tools)

        prompt = f"""{system}{history_block}

Client's message: {text}"""

        try:
            return await _call_claude(prompt, allowed_tools=allowed, timeout=120)
        except Exception as e:
            logger.exception("client_message_failed", phone=phone, project=project.slug)
            return "Something went wrong. Our team has been notified and will follow up shortly."

    # Multiple projects — ask for disambiguation
    project_list = "\n".join(f"- {p.name} ({p.status})" for p in projects)
    return (
        f"You have multiple projects with us:\n{project_list}\n\n"
        "Which project is this about? Reply with the project name."
    )
