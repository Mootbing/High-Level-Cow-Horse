"""Google GenAI client — Nano Banana (Gemini 2.5 Flash Image) + Veo 3."""

from __future__ import annotations

import asyncio
import base64

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

GENAI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Model names per the official quickstart:
# https://github.com/google-gemini/veo-3-nano-banana-gemini-api-quickstart
NANO_BANANA_MODEL = "gemini-2.5-flash-image-preview"  # Image generation
VEO_MODEL = "veo-3.0-generate-001"  # Video generation


async def generate_image(
    prompt: str, model: str = NANO_BANANA_MODEL
) -> bytes:
    """Generate an image using Nano Banana (Gemini 2.5 Flash Image Preview).

    Uses the generateContent endpoint with image output.
    Returns raw image bytes (PNG).
    """
    url = f"{GENAI_BASE}/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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
        if response.status_code != 200:
            logger.error("nano_banana_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()
        data = response.json()

    # Extract image from response
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])

    raise ValueError("No image data in Nano Banana response")


async def generate_video(
    prompt: str,
    reference_image: bytes | None = None,
    duration_seconds: int = 8,
    model: str = VEO_MODEL,
) -> str:
    """Generate a video using Veo 3. Returns the operation name for polling."""
    url = f"{GENAI_BASE}/models/{model}:generateVideos"

    # Build request per Veo 3 API
    request_body: dict = {
        "prompt": prompt,
        "config": {},
    }

    if reference_image:
        request_body["image"] = {
            "imageBytes": base64.b64encode(reference_image).decode(),
            "mimeType": "image/png",
        }

    async with httpx.AsyncClient(timeout=600) as client:
        # Start generation
        response = await client.post(
            url,
            json=request_body,
            params={"key": settings.GOOGLE_AI_API_KEY},
        )
        if response.status_code != 200:
            logger.error("veo3_start_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()

        operation = response.json()
        operation_name = operation.get("name", "")
        logger.info("veo3_operation_started", operation=operation_name)

        # Poll for completion — Veo 3 can take a few minutes
        poll_url = f"{GENAI_BASE}/{operation_name}"
        for i in range(120):  # Max ~10 minutes
            await asyncio.sleep(5)
            poll_response = await client.get(
                poll_url,
                params={"key": settings.GOOGLE_AI_API_KEY},
            )
            poll_data = poll_response.json()

            if poll_data.get("done"):
                # Extract video from response
                response_data = poll_data.get("response", {})
                videos = response_data.get("generatedVideos", [])
                if videos:
                    video = videos[0]
                    uri = video.get("uri", "")
                    if uri:
                        logger.info("veo3_complete", uri=uri[:100])
                        return uri

                # Check alternative response format
                if "video" in response_data:
                    uri = response_data["video"].get("uri", "")
                    if uri:
                        return uri

                raise ValueError(f"No video in Veo 3 response: {list(response_data.keys())}")

            if i % 12 == 0:
                logger.info("veo3_polling", attempt=i + 1, elapsed_s=(i + 1) * 5)

    raise TimeoutError("Veo 3 video generation timed out after 10 minutes")


async def download_video(uri: str) -> bytes:
    """Download a generated video from its URI."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(uri, params={"key": settings.GOOGLE_AI_API_KEY})
        response.raise_for_status()
        return response.content
