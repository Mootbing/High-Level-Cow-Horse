"""Task handler registry — each agent_type maps to a handler function.

A handler is: async def handle(task: Task, session: AsyncSession) -> dict
It reads from task.input_data, does work, applies side effects, and returns output_data.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import TYPE_CHECKING, Any, Callable, Awaitable

# Strip ANTHROPIC_API_KEY so Claude CLI uses stored OAuth credentials
_CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
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


async def _call_claude(prompt: str, timeout: int = 60) -> str:
    """Shell out to claude CLI and return raw stdout."""
    proc = await asyncio.to_thread(
        subprocess.run,
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_CLEAN_ENV,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {proc.stderr[:300]}")

    # Parse claude JSON wrapper
    try:
        claude_output = json.loads(proc.stdout)
        return claude_output.get("result", proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout


async def _call_claude_with_tools(prompt: str, cwd: str | None = None, timeout: int = 300) -> str:
    """Shell out to claude CLI with full tool access (for build tasks)."""
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--allowedTools", "*"]
    proc = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        env=_CLEAN_ENV,
    )
    if proc.returncode != 0:
        detail = proc.stderr[:500] or proc.stdout[:500]
        raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {detail}")

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


async def _load_project_context(project_id, session: "AsyncSession") -> dict:
    """Load project + superprompt for build tasks."""
    from openclaw.models.project import Project
    from openclaw.config import settings
    import os

    project = await session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    meta = project.metadata_ or {}
    superprompt_path = meta.get("superprompt_path") or os.path.join(
        settings.STORAGE_PATH, project.slug, "superprompt.md"
    )

    superprompt = ""
    if os.path.exists(superprompt_path):
        with open(superprompt_path) as f:
            superprompt = f.read()

    return {
        "project": project,
        "superprompt": superprompt,
        "section_plan": meta.get("section_plan", []),
    }


async def handle_section_builder(task: "Task", session: "AsyncSession") -> dict:
    """Build a single website section via Claude CLI with MCP tools."""
    ctx = await _load_project_context(task.project_id, session)
    project = ctx["project"]
    superprompt = ctx["superprompt"]

    section_id = task.input_data.get("section_id", "unknown")
    component_files = task.input_data.get("component_files", [])
    description = task.input_data.get("description", "")

    prompt = f"""You are a section builder for Clarmi Design Studio. Build the "{section_id}" section for the "{project.name}" project.

## Assignment
- Section: {section_id}
- Component files (write ONLY these): {json.dumps(component_files)}
- Description: {description}

## Project Context (Superprompt)
{superprompt}

## Instructions
1. Use write_code("{project.slug}", "<file_path>", <code>) to write each component file
2. Use CSS custom properties: var(--color-primary), var(--color-secondary), etc.
3. Use clamp() for font sizes, GSAP ScrollTrigger with cleanup
4. Search ReactBits for components before writing custom effects
5. NEVER invent content — use only data from the superprompt
6. When done, call mark_section_complete("{project.slug}", "{section_id}", {json.dumps(component_files)})
"""

    result = await _call_claude_with_tools(prompt, timeout=300)
    return {"section_id": section_id, "result": result[:2000]}


async def handle_orchestrator(task: "Task", session: "AsyncSession") -> dict:
    """Orchestrate a full website build — assemble page.tsx from completed sections."""
    ctx = await _load_project_context(task.project_id, session)
    project = ctx["project"]
    superprompt = ctx["superprompt"]
    section_plan = task.input_data.get("section_plan", ctx["section_plan"])

    sections_str = json.dumps(section_plan, indent=2)

    prompt = f"""You are the build orchestrator for Clarmi Design Studio. Assemble the "{project.name}" website.

## Section Plan
{sections_str}

## Project Context (Superprompt)
{superprompt}

## Instructions
1. Check build status with get_build_status("{project.slug}")
2. Read each completed section component with read_code("{project.slug}", "<file>")
3. Write app/page.tsx that imports and composes all sections in order
4. Write any missing shared infrastructure (globals.css, layout.tsx, SmoothScroller.tsx) if not present
5. Run verify_build("{project.slug}") — fix any errors
6. Deploy with deploy("{project.slug}", "Build {project.name} website")
7. ALWAYS deploy what you have, even if some sections are imperfect
"""

    result = await _call_claude_with_tools(prompt, timeout=600)
    return {"result": result[:2000]}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

HANDLERS: dict[str, Callable[..., Awaitable[dict]]] = {
    "email_regen": handle_email_regen,
    "section_builder": handle_section_builder,
    "orchestrator": handle_orchestrator,
}
