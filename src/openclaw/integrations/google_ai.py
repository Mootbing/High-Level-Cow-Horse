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
NANO_BANANA_MODEL = "gemini-2.5-flash-image"  # Nano Banana image generation
VEO_MODEL = "veo-3.0-generate-001"  # Veo 3 video generation (fallback)
VEO_3_1_MODEL = "veo-3.1-fast-generate-preview"  # Veo 3.1 Fast — supports first+last frame mode


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
    last_frame_image: bytes | None = None,
    duration_seconds: int = 8,
    resolution: str = "1080p",
    aspect_ratio: str = "16:9",
    model: str | None = None,
) -> str:
    """Generate a video using Veo. Returns the operation name for polling.

    Supports Veo 3.1's first+last frame mode: pass reference_image as the first frame
    and last_frame_image as the last frame to generate a smooth transition between them.
    This is ideal for scroll-controlled section transitions.

    If both reference_image and last_frame_image are provided, Veo 3.1 Fast is used
    automatically (Veo 3.0 does not support last_frame).
    """
    # Use Veo 3.1 when last_frame is needed, otherwise try 3.1 with 3.0 fallback
    if model is None:
        model = VEO_3_1_MODEL if last_frame_image else VEO_MODEL

    url = f"{GENAI_BASE}/models/{model}:predictLongRunning"

    # Build request per Veo API (uses instances/parameters format)
    request_body: dict = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "durationSeconds": duration_seconds,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
        },
    }

    if reference_image:
        request_body["instances"][0]["image"] = {
            "bytesBase64Encoded": base64.b64encode(reference_image).decode(),
            "mimeType": "image/png",
        }

    if last_frame_image:
        request_body["instances"][0]["lastFrame"] = {
            "bytesBase64Encoded": base64.b64encode(last_frame_image).decode(),
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
                response_data = poll_data.get("response", {})
                logger.info("veo3_done_response", keys=list(response_data.keys()))

                # Try all known response formats
                for key in ["generatedVideos", "generateVideoResponse", "videos"]:
                    videos = response_data.get(key, [])
                    if isinstance(videos, dict):
                        videos = [videos]
                    if isinstance(videos, list) and videos:
                        video = videos[0]
                        uri = video.get("uri", video.get("video", {}).get("uri", ""))
                        if uri:
                            logger.info("veo3_complete", uri=uri[:100])
                            return uri

                # Try nested generateVideoResponse.generatedSamples
                gvr = response_data.get("generateVideoResponse", {})
                if isinstance(gvr, dict):
                    samples = gvr.get("generatedSamples", [])
                    if samples:
                        uri = samples[0].get("video", {}).get("uri", "")
                        if uri:
                            logger.info("veo3_complete", uri=uri[:100])
                            return uri

                raise ValueError(f"No video in Veo 3 response: {list(response_data.keys())}")

            if i % 12 == 0:
                logger.info("veo3_polling", attempt=i + 1, elapsed_s=(i + 1) * 5)

    raise TimeoutError("Veo 3 video generation timed out after 10 minutes")


async def download_video(uri: str) -> bytes:
    """Download a generated video from its URI."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(uri)
        response.raise_for_status()
        return response.content
