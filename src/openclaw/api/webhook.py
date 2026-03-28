"""WhatsApp webhook endpoint for receiving and routing messages."""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
import structlog

from openclaw.config import settings
from openclaw.db.session import async_session_factory
from openclaw.integrations.whatsapp_client import verify_signature, extract_messages
from openclaw.models.message import Message
from openclaw.queue.producer import publish
from sqlalchemy import select

logger = structlog.get_logger()
router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Meta webhook verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WA_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request):
    """Receive WhatsApp messages and route to CEO agent."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    messages = extract_messages(payload)

    for msg in messages:
        # Deduplicate
        async with async_session_factory() as session:
            existing = await session.execute(
                select(Message).where(Message.wa_message_id == msg["wa_message_id"])
            )
            if existing.scalar_one_or_none():
                continue

            # Store message
            db_message = Message(
                direction="inbound",
                wa_message_id=msg["wa_message_id"],
                phone_number=msg["phone"],
                message_type=msg["message_type"],
                content=msg["text"],
                media_url=msg.get("media_url"),
            )
            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)

        # Queue for CEO agent
        await publish("ceo", {
            "type": "whatsapp_message",
            "message_id": str(db_message.id),
            "phone": msg["phone"],
            "content": msg["text"],
            "message_type": msg["message_type"],
        })

    return {"status": "ok"}
