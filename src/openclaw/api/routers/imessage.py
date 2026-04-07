"""iMessage webhook router — receives messages from the TypeScript listener."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Header, HTTPException

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


@router.post("/incoming", response_model=IMessageReply)
async def handle_incoming(
    payload: IncomingIMessage,
    session: DBSession,
    x_webhook_secret: str = Header(...),
):
    """Handle an incoming /clarmi iMessage forwarded by the TS listener."""
    # Verify webhook secret
    if not settings.IMESSAGE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="IMESSAGE_WEBHOOK_SECRET not configured")
    if x_webhook_secret != settings.IMESSAGE_WEBHOOK_SECRET:
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

    logger.info(
        "imessage_incoming",
        phone=phone,
        text_preview=text[:80],
        chat_guid=payload.chat_guid,
    )

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
        content=payload.message_text,
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

    # Log outbound reply
    outbound = Message(
        channel="imessage",
        direction="outbound",
        phone_number=phone,
        message_type="text",
        content=reply_text,
        status="sent",
        project_id=project_id,
    )
    session.add(outbound)
    await session.commit()

    return IMessageReply(reply_text=reply_text)
