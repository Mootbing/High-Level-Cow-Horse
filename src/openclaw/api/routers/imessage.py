"""iMessage webhook router — receives messages from the TypeScript listener."""

from __future__ import annotations

import hmac
import re

import structlog
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select

from openclaw.api.schemas.imessage import IMessageReply, IncomingIMessage
from openclaw.config import settings
from openclaw.db.deps import DBSession
from openclaw.models.message import Message
from openclaw.services.imessage_agent import (
    find_projects_for_phone,
    normalize_phone,
    process_message,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/imessage", tags=["imessage"])

# Control characters to strip (keep \n=0x0a, \t=0x09, \r=0x0d)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0e-\x1f]")


@router.post("/incoming", response_model=IMessageReply)
async def handle_incoming(
    payload: IncomingIMessage,
    session: DBSession,
    x_webhook_secret: str = Header(...),
):
    """Handle an incoming /clarmi iMessage forwarded by the TS listener."""
    # Fix 1: Timing-constant webhook secret comparison
    if not settings.IMESSAGE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="IMESSAGE_WEBHOOK_SECRET not configured")
    if not hmac.compare_digest(x_webhook_secret, settings.IMESSAGE_WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    phone = normalize_phone(payload.phone_number)
    text = payload.message_text

    # Strip /clarmi prefix (the TS listener already filtered for it)
    if text.lower().startswith("/clarmi"):
        text = text[7:].strip()

    if not text:
        return IMessageReply(reply_text="Send /clarmi followed by your request.")

    # Limit message length to prevent abuse
    if len(text) > 2000:
        text = text[:2000]

    # Fix 4: Strip control characters (keep newlines/tabs)
    text = _CONTROL_CHAR_RE.sub("", text)

    logger.info(
        "imessage_incoming",
        phone=phone,
        text_preview=text[:80],
        chat_guid=payload.chat_guid,
    )

    # Fix 2: Deduplication — skip if this message_guid was already processed
    if payload.message_guid:
        existing = await session.execute(
            select(Message).where(
                Message.external_message_id == payload.message_guid
            ).limit(1)
        )
        if existing.scalar_one_or_none():
            logger.info("imessage_duplicate", guid=payload.message_guid, phone=phone)
            return IMessageReply(reply_text="Message already processed.")

    # Try to find associated project for message linking
    projects = await find_projects_for_phone(phone, session)
    project_id = projects[0].id if len(projects) == 1 else None

    # Log inbound message
    inbound = Message(
        channel="imessage",
        direction="inbound",
        external_message_id=payload.message_guid,
        phone_number=phone,
        message_type="text",
        content=text,
        status="received",
        project_id=project_id,
    )
    session.add(inbound)
    await session.flush()

    # Process with Claude
    try:
        reply_text = await process_message(phone, text, session, projects=projects)
    except Exception:
        logger.exception("imessage_process_error", phone=phone)
        reply_text = "Something went wrong. Please try again in a moment."

    # Fix 3: Resilient reply logging — always return reply even if DB commit fails
    outbound = Message(
        channel="imessage",
        direction="outbound",
        phone_number=phone,
        message_type="text",
        content=reply_text,
        status="sent",
        project_id=project_id,
    )
    try:
        session.add(outbound)
        await session.commit()
    except Exception:
        logger.exception(
            "outbound_commit_failed",
            phone=phone,
            reply_preview=reply_text[:200],
        )
        # Rollback so the session is usable, but still return the reply
        await session.rollback()

    return IMessageReply(reply_text=reply_text)
