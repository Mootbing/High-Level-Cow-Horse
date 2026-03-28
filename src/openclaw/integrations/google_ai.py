"""Unified Google GenAI client for image generation (Nano Banana) and video generation (Veo)."""

from __future__ import annotations

import asyncio
import base64

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

GENAI_BASE = "https://generativelanguage.googleapis.com/v1beta"


async def generate_image(
    prompt: str, model: str = "gemini-2.0-flash-exp"
) -> bytes:
    """Generate an image using Nano Banana (Google GenAI image generation).

    Returns raw image bytes (PNG).
    """
    url = f"{GENAI_BASE}/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url,
            json=payload,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        response.raise_for_status()
        data = response.json()

    # Extract image data from response
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])

    raise ValueError("No image data in response")


async def generate_video(
    prompt: str,
    reference_image: bytes | None = None,
    duration_seconds: int = 6,
    model: str = "veo-2.0-generate-001",
) -> str:
    """Generate a video using Veo. Returns the video URI for download."""
    url = f"{GENAI_BASE}/models/{model}:predictLongRunning"

    contents: list[dict] = [{"parts": [{"text": prompt}]}]
    if reference_image:
        contents[0]["parts"].insert(0, {
            "inlineData": {
                "mimeType": "image/png",
                "data": base64.b64encode(reference_image).decode(),
            }
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "videoDurationSeconds": duration_seconds,
        },
    }

    async with httpx.AsyncClient(timeout=300) as client:
        # Start generation
        response = await client.post(
            url,
            json=payload,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        response.raise_for_status()
        operation = response.json()
        operation_name = operation.get("name", "")

        # Poll for completion
        poll_url = f"{GENAI_BASE}/{operation_name}"
        for _ in range(60):  # Max ~5 minutes
            await asyncio.sleep(5)
            poll_response = await client.get(
                poll_url,
                params={"key": settings.GOOGLE_AI_API_KEY},
            )
            poll_data = poll_response.json()
            if poll_data.get("done"):
                # Extract video URI
                result = poll_data.get("response", {})
                videos = result.get("generatedVideos", [])
                if videos:
                    return videos[0].get("uri", "")
                raise ValueError("No video generated")

    raise TimeoutError("Video generation timed out")


async def download_video(uri: str) -> bytes:
    """Download a generated video from its URI."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(uri, params={"key": settings.GOOGLE_AI_API_KEY})
        response.raise_for_status()
        return response.content
