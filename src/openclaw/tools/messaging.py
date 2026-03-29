"""Channel-agnostic messaging — routes replies to dashboard or WhatsApp."""

from __future__ import annotations

import json

import redis.asyncio as redis
import structlog

from openclaw.config import settings
from openclaw.integrations.whatsapp_client import send_text_message, send_media_message

logger = structlog.get_logger()

DASHBOARD_REPLIES_CHANNEL = "dashboard:replies"
DASHBOARD_EVENTS_CHANNEL = "dashboard:events"
CLAWDBOT_REPLIES_CHANNEL = "clawdbot:replies"


async def _get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def send_reply(
    message: str,
    channel: str = "whatsapp",
    fallback_phone: str | None = None,
) -> dict:
    """Send a text reply through the appropriate channel."""
    if channel == "dashboard":
        r = await _get_redis()
        payload = json.dumps({"type": "chat", "content": message})
        await r.publish(DASHBOARD_REPLIES_CHANNEL, payload)
        await r.aclose()
        logger.info("reply_sent_dashboard", length=len(message))
        return {"status": "sent", "channel": "dashboard"}
    elif channel == "clawdbot":
        r = await _get_redis()
        payload = json.dumps({"type": "chat", "content": message})
        await r.publish(CLAWDBOT_REPLIES_CHANNEL, payload)
        await r.aclose()
        logger.info("reply_sent_clawdbot", length=len(message))
        return {"status": "sent", "channel": "clawdbot"}
    else:
        phone = fallback_phone or settings.OWNER_PHONE
        await send_text_message(phone, message)
        logger.info("reply_sent_whatsapp", to=phone)
        return {"status": "sent", "channel": "whatsapp", "to": phone}


async def send_media_reply(
    media_url: str,
    caption: str = "",
    channel: str = "whatsapp",
    fallback_phone: str | None = None,
) -> dict:
    """Send a media reply through the appropriate channel."""
    if channel in ("dashboard", "clawdbot"):
        r = await _get_redis()
        ch = DASHBOARD_REPLIES_CHANNEL if channel == "dashboard" else CLAWDBOT_REPLIES_CHANNEL
        payload = json.dumps({
            "type": "chat",
            "content": caption or "Sent media",
            "media_url": media_url,
        })
        await r.publish(ch, payload)
        await r.aclose()
        return {"status": "sent", "channel": channel}
    else:
        phone = fallback_phone or settings.OWNER_PHONE
        await send_media_message(phone, media_url, caption)
        return {"status": "sent", "channel": "whatsapp", "to": phone}


async def publish_dashboard_event(event: dict) -> None:
    """Publish a real-time event to the dashboard (agent status, task updates)."""
    r = await _get_redis()
    await r.publish(DASHBOARD_EVENTS_CHANNEL, json.dumps(event))
    await r.aclose()
