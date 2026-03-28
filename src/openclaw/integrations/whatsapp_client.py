"""WhatsApp Cloud API client for sending and receiving messages."""

from __future__ import annotations

import hashlib
import hmac
import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

BASE_URL = "https://graph.facebook.com/v21.0"


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from Meta."""
    if not settings.WA_APP_SECRET:
        return True  # Skip in dev
    expected = hmac.new(
        settings.WA_APP_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def send_text_message(to: str, text: str) -> dict:
    """Send a text message via WhatsApp Cloud API."""
    url = f"{BASE_URL}/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


async def send_media_message(to: str, media_url: str, caption: str = "") -> dict:
    """Send an image message via WhatsApp Cloud API."""
    url = f"{BASE_URL}/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": media_url, "caption": caption},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def extract_messages(webhook_payload: dict) -> list[dict]:
    """Extract messages from Meta's nested webhook payload."""
    messages = []
    for entry in webhook_payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                extracted = {
                    "wa_message_id": msg.get("id", ""),
                    "phone": msg.get("from", ""),
                    "message_type": msg.get("type", "text"),
                    "text": "",
                    "media_url": None,
                }
                if msg.get("type") == "text":
                    extracted["text"] = msg.get("text", {}).get("body", "")
                elif msg.get("type") in ("image", "video", "document"):
                    media = msg.get(msg["type"], {})
                    extracted["media_url"] = media.get("id", "")
                    extracted["text"] = media.get("caption", "")
                messages.append(extracted)
    return messages
