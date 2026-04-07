"""Handler for website_audit tasks — shells out to Claude CLI with MCP tools."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import datetime, timezone, UTC
from typing import TYPE_CHECKING

import structlog

from openclaw.audit_worker.email_template import render_audit_email
from openclaw.integrations.gmail_client import send_email
from openclaw.models.email_log import EmailLog
from openclaw.services.prospect_service import get_or_create_prospect
from openclaw.services.website_audit import AuditResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from openclaw.models.task import Task

logger = structlog.get_logger()

AUDIT_PROMPT = """You are Clarmi Design Studio's website audit agent. A visitor submitted their website URL on clarmi.com for a free audit. Run the audit and return structured results.

Website URL: {url}
Visitor email: {email}

## Instructions

1. Call audit_prospect_website(url="{url}") to analyze the website
2. Review the returned scores, site_problems, tech_stack, and overall score
3. Based on the audit data, write personalized copy for the results email

Return ONLY valid JSON (no markdown fences, no explanation) with this exact structure:
{{
  "overall_score": <float 0-10>,
  "scores": {{"visual_design": <int>, "ux_navigation": <int>, "content_quality": <int>, "technical": <int>, "mobile_friendly": <int>}},
  "site_problems": ["problem 1", "problem 2"],
  "tech_stack": ["Tech1", "Tech2"],
  "brand_colors": ["#hex1"],
  "contact_emails": ["found@email.com"],
  "page_title": "Their Page Title",
  "final_url": "https://their-final-url.com",
  "personalized_subject": "Your site scores X/10 — here's what's holding it back",
  "personalized_intro": "2-3 sentences referencing something specific about their site — what it does, what stands out, what's broken. Warm and direct.",
  "personalized_cta": "1-2 sentences about what we'd specifically improve for them and why it matters."
}}

## Rules for personalized fields
- Reference SPECIFIC findings (their CMS, their missing H1, their 23 script tags — whatever you found)
- The subject line should include their score and reference one specific issue
- Never use "I hope this finds you well", "I came across your website", "in today's digital landscape"
- Be warm, direct, and specific — this is a real person who asked for this audit
- Keep personalized_intro under 50 words, personalized_cta under 40 words
"""


async def _call_claude_with_tools(prompt: str, timeout: int = 120) -> str:
    """Shell out to claude CLI with MCP tool access."""
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--allowedTools", "mcp__clarmi-tools__audit_prospect_website"]
    # Strip ANTHROPIC_API_KEY from env so Claude CLI uses stored OAuth credentials
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    proc = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
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


async def handle_website_audit(task: "Task", session: "AsyncSession") -> dict:
    """Run website audit via Claude CLI, store prospect, send personalized email."""
    url = task.input_data["url"]
    email = task.input_data["email"]

    # 1. Shell out to Claude — it calls audit_prospect_website via MCP and returns structured data
    prompt = AUDIT_PROMPT.format(url=url, email=email)
    raw = await _call_claude_with_tools(prompt)
    data = _parse_json_response(raw)

    # Validate required fields
    required = ("overall_score", "scores", "site_problems", "personalized_subject")
    for key in required:
        if key not in data:
            raise ValueError(f"Claude response missing '{key}': {raw[:300]}")

    # 2. Build AuditResult for the email template
    audit = AuditResult(
        url=url,
        final_url=data.get("final_url", url),
        page_title=data.get("page_title"),
        meta_description=None,
        is_https=data.get("final_url", url).startswith("https://"),
        tech_stack=data.get("tech_stack", []),
        scores=data["scores"],
        overall=float(data["overall_score"]),
        site_problems=data.get("site_problems", []),
        brand_colors=data.get("brand_colors", []),
        contact_emails=data.get("contact_emails", []),
    )

    # Use a fresh session for DB operations after the thread-based Claude CLI call
    # to avoid greenlet context issues with asyncio.to_thread
    from openclaw.db.session import async_session_factory

    async with async_session_factory() as db:
        # 3. Get or create prospect
        prospect, created = await get_or_create_prospect(
            db,
            url=audit.final_url,
            company_name=audit.page_title,
            contact_emails=[email] + audit.contact_emails,
            brand_colors=audit.brand_colors,
            tech_stack=audit.tech_stack,
            raw_data={
                "lead_source": "website_audit_form",
                "visitor_email": email,
                "website_scores": audit.scores,
                "website_overall": audit.overall,
                "site_problems": audit.site_problems,
                "audited_at": datetime.now(UTC).isoformat(),
                "personalized_intro": data.get("personalized_intro", ""),
                "personalized_cta": data.get("personalized_cta", ""),
            },
        )

        # 4. Render email with Claude's personalized copy + our reliable HTML template
        subject = data["personalized_subject"]
        html_body = render_audit_email(
            audit,
            email,
            personalized_intro=data.get("personalized_intro"),
            personalized_cta=data.get("personalized_cta"),
        )

        # 5. Send via Gmail
        gmail_result = await send_email(to=email, subject=subject, body=html_body)

        # 6. Log it
        email_log = EmailLog(
            prospect_id=prospect.id,
            to_email=email,
            subject=subject,
            body=html_body,
            status="sent",
            gmail_message_id=gmail_result.get("id"),
            sent_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(email_log)
        await db.commit()

    logger.info(
        "audit_email_sent",
        url=url,
        email=email,
        overall=audit.overall,
        problems=len(audit.site_problems),
    )

    return {
        "prospect_id": str(prospect.id),
        "prospect_created": created,
        "email_sent": True,
        "gmail_message_id": gmail_result.get("id"),
        "overall_score": audit.overall,
        "problem_count": len(audit.site_problems),
        "personalized": True,
    }
