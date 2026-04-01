"""Google GenAI client — Nano Banana (Gemini 2.5 Flash Image) + Veo 3.1."""

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
VEO_MODEL = "veo-3.1-generate-001"  # Veo 3.1 — all video generation


async def generate_image(
    prompt: str,
    model: str = NANO_BANANA_MODEL,
    aspect_ratio: str = "16:9",
) -> bytes:
    """Generate an image using Nano Banana (Gemini 2.5 Flash Image Preview).

    Uses the generateContent endpoint with image output.
    Returns raw image bytes (PNG). Default aspect ratio is 16:9 to match
    video output and ensure consistent full-viewport coverage.
    """
    url = f"{GENAI_BASE}/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "aspectRatio": aspect_ratio,
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
    duration_seconds: int = 3,
    resolution: str = "1080p",
    aspect_ratio: str = "16:9",
    model: str | None = None,
) -> str:
    """Generate a video using Veo 3.1. Returns the video URI.

    Supports first+last frame mode: pass reference_image as the first frame
    and last_frame_image as the last frame to generate a smooth transition.

    Duration defaults to 3 seconds to minimize cost. Audio is always disabled.
    """
    if model is None:
        model = VEO_MODEL

    url = f"{GENAI_BASE}/models/{model}:predictLongRunning"

    # Build request per Veo API (uses instances/parameters format)
    request_body: dict = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "durationSeconds": duration_seconds,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
            "includeAudio": False,
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
        # Start generation — retry up to 3 times for transient errors (429, 400, 503)
        response = None
        for attempt in range(3):
            response = await client.post(
                url,
                json=request_body,
                params={"key": settings.GOOGLE_AI_API_KEY},
            )
            if response.status_code == 200:
                break
            if response.status_code in (429, 503) or (response.status_code == 400 and attempt < 2):
                wait = (attempt + 1) * 15  # 15s, 30s, 45s
                logger.warning(
                    "veo3_retry",
                    status=response.status_code,
                    attempt=attempt + 1,
                    wait=wait,
                    body=response.text[:300],
                )
                await asyncio.sleep(wait)
            else:
                break

        if response is None or response.status_code != 200:
            body = response.text[:500] if response else "no response"
            logger.error("veo3_start_error", status=getattr(response, "status_code", None), body=body)
            if response is not None:
                response.raise_for_status()
            raise RuntimeError("Veo 3 video generation failed — no response after retries")

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
    """Download a generated video from its URI.

    Google's file API returns a 302 redirect to the actual download URL.
    We need follow_redirects=True and must pass the API key on every request.
    """
    # Ensure the API key is in the URI (some URIs already have it, some don't)
    separator = "&" if "?" in uri else "?"
    authenticated_uri = f"{uri}{separator}key={settings.GOOGLE_AI_API_KEY}" if "key=" not in uri else uri

    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
        response = await client.get(authenticated_uri)
        if response.status_code != 200:
            logger.error("video_download_error", status=response.status_code, url=uri[:100])
        response.raise_for_status()
        logger.info("video_downloaded", size_bytes=len(response.content))
        return response.content
