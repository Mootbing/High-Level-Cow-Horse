"""Task handler registry — each agent_type maps to a handler function.

A handler is: async def handle(task: Task, session: AsyncSession) -> dict
It reads from task.input_data, does work, applies side effects, and returns output_data.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import TYPE_CHECKING, Any, Callable, Awaitable
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from openclaw.models.task import Task

logger = structlog.get_logger()

REGEN_PROMPT_TEMPLATE = """Rewrite this cold outreach email. Output ONLY valid JSON with two keys: "subject" and "body". No markdown, no explanation, no code fences.

Rules:
- Under 100 words for the body
- Warm, direct, no fluff
- Never use "I hope this email finds you well", "I came across your website", "in today's digital landscape", "take your brand to the next level"
- No exclamation marks in subject line
- Keep the same prospect/company context
- Do NOT include a calendar booking link — it gets appended automatically

Original subject: {subject}

Original body:
{body}

{instructions}

Respond with ONLY the JSON object, nothing else."""


async def _call_claude(prompt: str) -> str:
    """Shell out to claude CLI and return raw stdout."""
    proc = await asyncio.to_thread(
        subprocess.run,
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {proc.stderr[:300]}")

    # Parse claude JSON wrapper
    try:
        claude_output = json.loads(proc.stdout)
        return claude_output.get("result", proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout


def _parse_json_response(text: str) -> dict:
    """Extract JSON from Claude's response, handling possible markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0].strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def handle_email_regen(task: "Task", session: "AsyncSession") -> dict:
    """Rewrite an email draft via Claude CLI."""
    from openclaw.models.email_log import EmailLog

    email_id = task.input_data.get("email_id")
    instructions = task.input_data.get("instructions", "")

    email = await session.get(EmailLog, UUID(email_id))
    if not email:
        raise ValueError(f"EmailLog {email_id} not found")

    prompt = REGEN_PROMPT_TEMPLATE.format(
        subject=email.edited_subject or email.subject or "",
        body=email.body or "",
        instructions=f"Additional instructions: {instructions}" if instructions else "",
    )

    try:
        raw = await _call_claude(prompt)
        rewritten = _parse_json_response(raw)
        if "subject" not in rewritten or "body" not in rewritten:
            raise ValueError(f"Missing subject/body in response: {raw[:200]}")
        email.edited_subject = rewritten["subject"]
        email.edited_body = rewritten["body"]
        email.status = "draft"
        return rewritten
    except Exception:
        email.edited_body = None
        email.status = "draft"
        raise


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

HANDLERS: dict[str, Callable[..., Awaitable[dict]]] = {
    "email_regen": handle_email_regen,
}
