"""Gmail API client for sending emails via OAuth2 refresh token flow."""

from __future__ import annotations

import base64
from email.mime.text import MIMEText

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


async def _get_access_token() -> str:
    """Get a fresh access token using the refresh token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data={
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "refresh_token": settings.GMAIL_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        })
        response.raise_for_status()
        return response.json()["access_token"]


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email via Gmail API."""
    access_token = await _get_access_token()

    message = MIMEText(body, "html")
    message["to"] = to
    message["from"] = settings.GMAIL_SENDER_EMAIL
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GMAIL_API_URL,
            json={"raw": raw},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        result = response.json()
        logger.info("email_sent", to=to, message_id=result.get("id"))
        return result
