"""WebSocket endpoint for real-time CEO chat + dashboard events."""

from __future__ import annotations

import asyncio
import json
import uuid

import redis.asyncio as redis
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from openclaw.config import settings
from openclaw.db.session import async_session_factory
from openclaw.models.message import Message
from openclaw.queue.producer import publish
from openclaw.tools.messaging import DASHBOARD_REPLIES_CHANNEL, DASHBOARD_EVENTS_CHANNEL

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """Multiplexed WebSocket: CEO chat + real-time dashboard events."""
    # Authenticate via query param
    token = websocket.query_params.get("token", "")
    if token != settings.DASHBOARD_SECRET:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info("dashboard_ws_connected")

    # Subscribe to Redis pubsub for agent replies and events
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(DASHBOARD_REPLIES_CHANNEL, DASHBOARD_EVENTS_CHANNEL)

    async def _relay_from_redis():
        """Read from Redis pubsub and push to WebSocket."""
        try:
            while True:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if msg and msg["type"] == "message":
                    await websocket.send_text(msg["data"])
                else:
                    await asyncio.sleep(0.1)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    async def _relay_from_client():
        """Read from WebSocket and queue for CEO agent."""
        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                content = data.get("content", "").strip()
                if not content:
                    continue

                # Store as inbound message
                async with async_session_factory() as session:
                    db_msg = Message(
                        direction="inbound",
                        phone_number="dashboard",
                        message_type="text",
                        content=content,
                    )
                    session.add(db_msg)
                    await session.commit()
                    await session.refresh(db_msg)

                # Queue for CEO agent
                await publish("ceo", {
                    "type": "dashboard_message",
                    "message_id": str(db_msg.id),
                    "content": content,
                    "reply_channel": "dashboard",
                })
                logger.info("dashboard_message_queued", message_id=str(db_msg.id))
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    # Run both loops concurrently
    redis_task = asyncio.create_task(_relay_from_redis())
    client_task = asyncio.create_task(_relay_from_client())

    try:
        done, pending = await asyncio.wait(
            [redis_task, client_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await r.aclose()
        logger.info("dashboard_ws_disconnected")
