"""Email tools — draft and send emails via Gmail."""

import json
import uuid as _uuid
from datetime import datetime

from openclaw.mcp_server.server import mcp

CALENDAR_CTA = "\n\nLet's talk for 15 minutes: https://calendar.app.google/1R6HGErUx6kvbgSa9"


@mcp.tool()
async def draft_email(
    to: str,
    subject: str,
    body: str,
    project_id: str | None = None,
) -> str:
    """Save an email draft for review before sending.

    The draft is stored in the database. Use send_email with the returned email_id to send it.
    Emails should be under 150 words, personalized, reference specific site problems, and avoid aggressive sales language.
    """
    from openclaw.db.session import async_session_factory
    from openclaw.models.email_log import EmailLog
    from openclaw.models.prospect import Prospect
    from sqlalchemy import select

    # Coerce project_id to UUID
    pid = None
    if project_id:
        try:
            pid = _uuid.UUID(project_id)
        except ValueError:
            return json.dumps({"error": f"Invalid project_id: {project_id}"})

    async with async_session_factory() as session:
        # Try to link to prospect by email
        prospect_id = None
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        stmt = select(Prospect).where(
            Prospect.contact_emails.op("@>")(cast([to], JSONB))
        )
        result = await session.execute(stmt)
        prospect = result.scalar_one_or_none()
        if prospect:
            prospect_id = prospect.id

        # Append calendar booking link if not already present
        if "calendar.app.google" not in body:
            body = body.rstrip() + CALENDAR_CTA

        email_log = EmailLog(
            to_email=to,
            subject=subject,
            body=body,
            project_id=pid,
            prospect_id=prospect_id,
            status="draft",
        )
        session.add(email_log)
        await session.commit()
        await session.refresh(email_log)

        return json.dumps({
            "email_id": str(email_log.id),
            "status": "draft",
            "to": to,
            "subject": subject,
            "note": "Draft saved. Use send_email to send it after owner review.",
        })


@mcp.tool()
async def send_email(email_id: str) -> str:
    """Send a previously drafted email via Gmail. Only call after the owner has reviewed and approved."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.email_log import EmailLog
    from openclaw.integrations.gmail_client import send_email as _send

    try:
        eid = _uuid.UUID(email_id)
    except ValueError:
        return json.dumps({"error": f"Invalid email_id: {email_id}"})

    async with async_session_factory() as session:
        email_log = await session.get(EmailLog, eid)
        if not email_log:
            return json.dumps({"error": f"Email {email_id} not found"})
        if email_log.status == "sent":
            return json.dumps({"error": "Email already sent", "sent_at": email_log.sent_at.isoformat() if email_log.sent_at else None})

        # Use edited versions if available
        subject = email_log.edited_subject or email_log.subject
        body = email_log.edited_body or email_log.body

        try:
            result = await _send(to=email_log.to_email, subject=subject, body=body)
        except Exception as exc:
            email_log.status = "failed"
            await session.commit()
            return json.dumps({"error": f"Gmail send failed: {str(exc)[:200]}"})

        email_log.status = "sent"
        email_log.gmail_message_id = result.get("id")
        email_log.sent_at = datetime.utcnow()
        await session.commit()

        return json.dumps({
            "status": "sent",
            "to": email_log.to_email,
            "gmail_message_id": result.get("id"),
        })
