#!/usr/bin/env python3
"""Health check script — runs via cron, alerts owner on WhatsApp if issues detected."""
import asyncio
import sys
import httpx
import redis.asyncio as redis

# Try to import settings, fall back to env vars
try:
    from openclaw.config import settings
    REDIS_URL = settings.REDIS_URL
    OWNER_PHONE = settings.OWNER_PHONE
    WA_ACCESS_TOKEN = settings.WA_ACCESS_TOKEN
    WA_PHONE_NUMBER_ID = settings.WA_PHONE_NUMBER_ID
except ImportError:
    import os
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    OWNER_PHONE = os.environ.get("OWNER_PHONE", "")
    WA_ACCESS_TOKEN = os.environ.get("WA_ACCESS_TOKEN", "")
    WA_PHONE_NUMBER_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")

AGENT_TYPES = [
    "ceo", "project_manager", "inbound", "designer",
    "engineer", "qa", "outbound", "client_comms",
    "research", "learning",
]


async def send_alert(message: str) -> None:
    """Send alert to owner via WhatsApp."""
    if not all([OWNER_PHONE, WA_ACCESS_TOKEN, WA_PHONE_NUMBER_ID]):
        print(f"ALERT (no WhatsApp configured): {message}")
        return
    url = f"https://graph.facebook.com/v21.0/{WA_PHONE_NUMBER_ID}/messages"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "messaging_product": "whatsapp",
            "to": OWNER_PHONE,
            "type": "text",
            "text": {"body": f"🚨 Clarmi Design Studio Alert:\n{message}"},
        }, headers={"Authorization": f"Bearer {WA_ACCESS_TOKEN}"})


async def check_health() -> None:
    issues = []

    # Check API
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("http://localhost:8000/api/health")
            if r.status_code != 200:
                issues.append(f"API returned {r.status_code}")
            else:
                data = r.json()
                for check, status in data.get("checks", {}).items():
                    if status != "ok":
                        issues.append(f"{check}: {status}")
    except Exception as e:
        issues.append(f"API unreachable: {e}")

    # Check agent heartbeats
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        for agent_type in AGENT_TYPES:
            keys = await r.keys(f"health:{agent_type}:*")
            if not keys:
                issues.append(f"Agent '{agent_type}' has no heartbeat")
        await r.aclose()
    except Exception as e:
        issues.append(f"Redis check failed: {e}")

    if issues:
        await send_alert("\n".join(issues))
        print(f"UNHEALTHY: {'; '.join(issues)}")
        sys.exit(1)
    else:
        print("OK: All checks passed")


if __name__ == "__main__":
    asyncio.run(check_health())
