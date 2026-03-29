"""Unified Google GenAI client for image generation (Imagen) and video generation (Veo)."""

from __future__ import annotations

import asyncio
import base64

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

GENAI_BASE = "https://generativelanguage.googleapis.com/v1beta"


async def generate_image(
    prompt: str, model: str = "imagen-3.0-generate-002"
) -> bytes:
    """Generate an image using Google Imagen.

    Returns raw image bytes (PNG).
    """
    url = f"{GENAI_BASE}/models/{model}:predict"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url,
            json=payload,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        if response.status_code != 200:
            logger.error("imagen_error", status=response.status_code, body=response.text[:500])
            # Fallback: try gemini with image generation
            return await _generate_image_gemini(prompt)

        data = response.json()

    predictions = data.get("predictions", [])
    if predictions and "bytesBase64Encoded" in predictions[0]:
        return base64.b64decode(predictions[0]["bytesBase64Encoded"])

    raise ValueError("No image data in Imagen response")


async def _generate_image_gemini(prompt: str) -> bytes:
    """Fallback: generate image using Gemini's native image generation."""
    url = f"{GENAI_BASE}/models/gemini-2.0-flash-exp:generateContent"
    payload = {
        "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url,
            json=payload,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        response.raise_for_status()
        data = response.json()

    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])

    raise ValueError("No image data in Gemini response")


async def generate_video(
    prompt: str,
    reference_image: bytes | None = None,
    duration_seconds: int = 6,
    model: str = "veo-2.0-generate-001",
) -> str:
    """Generate a video using Veo 2. Returns the video URI for download."""
    url = f"{GENAI_BASE}/models/{model}:predictLongRunning"

    # Build the request per Veo 2 API spec
    instances: list[dict] = [{"prompt": prompt}]
    if reference_image:
        instances[0]["image"] = {
            "bytesBase64Encoded": base64.b64encode(reference_image).decode(),
        }

    payload = {
        "instances": instances,
        "parameters": {
            "videoDuration": f"{duration_seconds}s",
            "sampleCount": 1,
        },
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            url,
            json=payload,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        if response.status_code != 200:
            logger.error("veo_start_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()

        operation = response.json()
        operation_name = operation.get("name", "")
        logger.info("veo_operation_started", operation=operation_name)

        # Poll for completion
        poll_url = f"{GENAI_BASE}/{operation_name}"
        for i in range(60):  # Max ~5 minutes
            await asyncio.sleep(5)
            poll_response = await client.get(
                poll_url,
                params={"key": settings.GOOGLE_AI_API_KEY},
            )
            poll_data = poll_response.json()
            if poll_data.get("done"):
                result = poll_data.get("response", {})
                videos = result.get("generateVideoResponses", result.get("generatedVideos", []))
                if videos:
                    video = videos[0] if isinstance(videos, list) else videos
                    uri = video.get("uri", video.get("video", {}).get("uri", ""))
                    if uri:
                        logger.info("veo_complete", uri=uri[:100])
                        return uri
                raise ValueError(f"No video in Veo response: {result}")
            logger.debug("veo_polling", attempt=i + 1)

    raise TimeoutError("Video generation timed out after 5 minutes")


async def download_video(uri: str) -> bytes:
    """Download a generated video from its URI."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(uri, params={"key": settings.GOOGLE_AI_API_KEY})
        response.raise_for_status()
        return response.content
