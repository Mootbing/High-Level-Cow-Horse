"""Design tools — generate images (Nano Banana) and videos (Veo 3.1), upload to GitHub repo."""

import json
import os
import uuid

import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


async def _get_project_repo(project_name: str) -> str:
    """Look up the GitHub repo full name from project metadata.

    Raises RuntimeError if no repo is found — never guesses.
    """
    from openclaw.db.session import async_session_factory
    from openclaw.services.project_service import find_project_by_name

    async with async_session_factory() as session:
        project = await find_project_by_name(session, project_name)
        if project and project.metadata_:
            repo = project.metadata_.get("github_repo")
            if repo:
                return repo

    raise RuntimeError(
        f"No GitHub repo found for project '{project_name}'. "
        "Run create_project first — GitHub repo must be provisioned before uploading assets."
    )


async def _upload_asset(project_name: str, filename: str, content: bytes) -> str:
    """Upload asset to GitHub repo /public/assets/ and return the public URL path."""
    from openclaw.integrations.github_client import upload_file

    repo = await _get_project_repo(project_name)
    repo_path = f"public/assets/{filename}"

    try:
        result = await upload_file(
            repo_full_name=repo,
            file_path_in_repo=repo_path,
            content=content,
            commit_message=f"Add generated asset: {filename}",
        )
        public_url = f"/assets/{filename}"
        logger.info("asset_uploaded", repo=repo, path=repo_path, public_url=public_url)
        return public_url
    except Exception as e:
        logger.error("asset_upload_failed", repo=repo, filename=filename, error=str(e))
        return f"UPLOAD_FAILED:/assets/{filename} — error: {str(e)[:200]}"


@mcp.tool()
async def generate_image(prompt: str, project_name: str, section: str) -> str:
    """Generate a keyframe image using Nano Banana (Google AI) and upload to the project's GitHub repo.

    The image is uploaded to /public/assets/ so Vercel serves it at the site root.
    Returns the public URL path (e.g. /assets/keyframe-hero-abc123.png).

    IMPORTANT: Never include text, words, or logos in the prompt. Images should be purely visual/abstract.
    """
    from openclaw.integrations.google_ai import generate_image as _generate

    try:
        image_data = await _generate(prompt)
    except Exception as exc:
        logger.warning("image_generation_failed", error=str(exc)[:300])
        return json.dumps({
            "status": "failed",
            "error": f"Image generation failed: {str(exc)[:200]}",
            "section": section,
        })

    filename = f"keyframe-{section}-{uuid.uuid4().hex[:8]}.png"

    # Save locally as backup (sanitize project_name for filesystem)
    safe_name = os.path.basename(project_name.replace("..", "").strip("/")) or "unnamed"
    project_dir = os.path.join(settings.STORAGE_PATH, safe_name)
    os.makedirs(project_dir, exist_ok=True)
    with open(os.path.join(project_dir, filename), "wb") as f:
        f.write(image_data)

    public_url = await _upload_asset(project_name, filename, image_data)

    return json.dumps({
        "status": "generated",
        "filename": filename,
        "public_url": public_url,
        "section": section,
    })


@mcp.tool()
async def generate_transition_video(
    prompt: str,
    project_name: str,
    section: str,
    keyframe_a_prompt: str,
    keyframe_b_prompt: str,
    duration: int = 3,
) -> str:
    """Generate a scroll-controlled transition video: keyframe A (image) → Veo transition → keyframe B (image).

    Pipeline:
    1. Generates keyframe A image using Nano Banana
    2. Generates keyframe B image using Nano Banana
    3. Uses Veo 3.1 with keyframe A as first frame AND keyframe B as last frame
       to generate a smooth transition video (first+last frame mode)
    4. Uploads all three assets (keyframe A, keyframe B, transition video)

    The resulting video is designed for scroll-controlled playback — the user scrolls
    through the section and the video plays as a morphing transition between two states.

    Returns paths to all three assets so the build step can:
    - Show keyframe A as the initial static state
    - Play the transition video mapped to scroll position
    - Show keyframe B as the final static state

    Use this for cinematic section transitions, hero → content morphs, and
    storytelling sequences where one visual state smoothly becomes another.

    IMPORTANT: Never include text, words, or logos in prompts. Images should be purely visual.
    """
    from openclaw.integrations.google_ai import generate_image as _generate_image
    from openclaw.integrations.google_ai import generate_video as _generate_video
    from openclaw.integrations.google_ai import download_video

    results = {"section": section, "status": "partial"}

    # Step 1: Generate keyframe A
    try:
        image_a_data = await _generate_image(keyframe_a_prompt)
        filename_a = f"keyframe-{section}-a-{uuid.uuid4().hex[:8]}.png"
        safe_name = os.path.basename(project_name.replace("..", "").strip("/")) or "unnamed"
        project_dir = os.path.join(settings.STORAGE_PATH, safe_name)
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, filename_a), "wb") as f:
            f.write(image_a_data)
        url_a = await _upload_asset(project_name, filename_a, image_a_data)
        results["keyframe_a"] = url_a
        logger.info("transition_keyframe_a_generated", section=section, url=url_a)
    except Exception as exc:
        logger.warning("transition_keyframe_a_failed", error=str(exc)[:300])
        results["keyframe_a_error"] = str(exc)[:200]
        return json.dumps(results)

    # Step 2: Generate keyframe B
    try:
        image_b_data = await _generate_image(keyframe_b_prompt)
        filename_b = f"keyframe-{section}-b-{uuid.uuid4().hex[:8]}.png"
        with open(os.path.join(project_dir, filename_b), "wb") as f:
            f.write(image_b_data)
        url_b = await _upload_asset(project_name, filename_b, image_b_data)
        results["keyframe_b"] = url_b
        logger.info("transition_keyframe_b_generated", section=section, url=url_b)
    except Exception as exc:
        logger.warning("transition_keyframe_b_failed", error=str(exc)[:300])
        results["keyframe_b_error"] = str(exc)[:200]
        # Still usable — can fall back to crossfade between two images
        return json.dumps(results)

    # Step 3: Generate transition video using Veo 3.1 with first+last frame mode
    try:
        transition_prompt = (
            f"{prompt}. Smooth cinematic transition. Camera movement is slow and deliberate. "
            f"Duration: {duration} seconds. No text or logos."
        )
        video_uri = await _generate_video(
            prompt=transition_prompt,
            reference_image=image_a_data,
            last_frame_image=image_b_data,
            duration_seconds=duration,
        )
        video_data = await download_video(video_uri)
        filename_video = f"transition-{section}-{uuid.uuid4().hex[:8]}.mp4"
        with open(os.path.join(project_dir, filename_video), "wb") as f:
            f.write(video_data)
        url_video = await _upload_asset(project_name, filename_video, video_data)
        results["transition_video"] = url_video
        results["status"] = "complete"
        logger.info("transition_video_generated", section=section, url=url_video)
    except Exception as exc:
        logger.warning("transition_video_failed", error=str(exc)[:300])
        results["transition_video_error"] = str(exc)[:200]
        results["status"] = "images_only"
        results["fallback_note"] = (
            "Video generation failed. Use CSS/JS crossfade between keyframe A and B "
            "on scroll instead of video playback."
        )

    return json.dumps(results)


@mcp.tool()
async def generate_scene_assets(
    project_name: str,
    sections: str,
) -> str:
    """Generate a complete set of visual assets for an immersive website build.

    sections is a JSON string: a list of objects, each with:
    - section: name (e.g. "hero", "about", "services", "cta")
    - type: "video" | "transition" | "image" | "hero_video"
    - prompt: the generation prompt
    - keyframe_a_prompt: (for hero_video and transitions) starting visual state prompt
    - keyframe_b_prompt: (for hero_video and transitions) ending visual state prompt

    This is a batch orchestrator — it calls generate_image, generate_video, or
    generate_transition_video for each section and returns all asset paths.

    Use this instead of calling individual generation tools one by one.

    For hero_video: ALWAYS provide keyframe_a_prompt (scroll start state) and
    keyframe_b_prompt (scroll end state). These are generated as images with Nano Banana,
    then Veo 3.1 creates a smooth transition video between them using first+last frame mode.
    The resulting video is designed for scroll-controlled frame-by-frame playback.

    Example sections JSON:
    [
      {"section": "hero", "type": "hero_video", "prompt": "Smooth cinematic morph from opening to closing state",
       "keyframe_a_prompt": "Opening visual state matching brand. No text.",
       "keyframe_b_prompt": "Ending visual state after scroll. No text."},
      {"section": "hero-to-about", "type": "transition", "prompt": "Morph from aerial to...",
       "keyframe_a_prompt": "Aerial city view...", "keyframe_b_prompt": "Close-up workspace..."},
      {"section": "features", "type": "image", "prompt": "Abstract geometric..."},
      {"section": "cta", "type": "image", "prompt": "Warm golden hour..."}
    ]
    """
    try:
        section_list = json.loads(sections)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid JSON: {str(e)[:200]}"})

    all_results = []
    for item in section_list:
        section_name = item.get("section", "unknown")
        asset_type = item.get("type", "image")
        prompt = item.get("prompt", "")

        if asset_type == "hero_video":
            # Hero videos use the keyframe pipeline: generate start + end frames
            # with Nano Banana, then Veo 3.1 first+last frame for scroll-controlled video
            kf_a_prompt = item.get("keyframe_a_prompt", "")
            kf_b_prompt = item.get("keyframe_b_prompt", "")

            if kf_a_prompt and kf_b_prompt:
                # Preferred: two-keyframe approach via Veo 3.1 first+last frame
                result_str = await generate_transition_video(
                    prompt=prompt,
                    project_name=project_name,
                    section=section_name,
                    keyframe_a_prompt=kf_a_prompt,
                    keyframe_b_prompt=kf_b_prompt,
                    duration=item.get("duration", 3),
                )
                result = json.loads(result_str)
                result["asset_type"] = "hero_video"
                all_results.append(result)
            else:
                # Fallback: raw prompt-only video (no keyframe control)
                result_str = await generate_video(prompt, project_name)
                result = json.loads(result_str)
                result["section"] = section_name
                result["asset_type"] = "hero_video"
                all_results.append(result)

        elif asset_type == "transition":
            result_str = await generate_transition_video(
                prompt=prompt,
                project_name=project_name,
                section=section_name,
                keyframe_a_prompt=item.get("keyframe_a_prompt", prompt),
                keyframe_b_prompt=item.get("keyframe_b_prompt", prompt),
                duration=item.get("duration", 3),
            )
            result = json.loads(result_str)
            result["asset_type"] = "transition"
            all_results.append(result)

        else:  # image
            result_str = await generate_image(prompt, project_name, section_name)
            result = json.loads(result_str)
            result["asset_type"] = "image"
            all_results.append(result)

    # Summary
    succeeded = sum(1 for r in all_results if r.get("status") in ("generated", "complete"))
    failed = sum(1 for r in all_results if r.get("status") == "failed")

    return json.dumps({
        "status": "batch_complete",
        "total": len(all_results),
        "succeeded": succeeded,
        "failed": failed,
        "assets": all_results,
    })


@mcp.tool()
async def generate_video(prompt: str, project_name: str, duration: int = 3) -> str:
    """Generate a hero video using Veo 3.1 (Google AI) and upload to the project's GitHub repo.

    The video is uploaded to /public/assets/ so Vercel serves it at the site root.
    Returns the public URL path (e.g. /assets/hero-video-abc123.mp4).

    If video generation fails (quota/rate limit), returns an error — use generate_image for a fallback hero keyframe.
    """
    from openclaw.integrations.google_ai import generate_video as _generate_video
    from openclaw.integrations.google_ai import download_video

    try:
        video_uri = await _generate_video(prompt=prompt, duration_seconds=duration)
        video_data = await download_video(video_uri)
        filename = f"hero-video-{uuid.uuid4().hex[:8]}.mp4"

        # Save locally as backup (sanitize project_name for filesystem)
        safe_name = os.path.basename(project_name.replace("..", "").strip("/")) or "unnamed"
        project_dir = os.path.join(settings.STORAGE_PATH, safe_name)
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, filename), "wb") as f:
            f.write(video_data)

        public_url = await _upload_asset(project_name, filename, video_data)

        return json.dumps({
            "status": "generated",
            "filename": filename,
            "public_url": public_url,
        })
    except Exception as exc:
        logger.warning("video_generation_failed", error=str(exc)[:300])
        return json.dumps({
            "status": "failed",
            "error": f"Video generation failed: {str(exc)[:200]}",
            "suggestion": "Use generate_image to create a hero keyframe image instead.",
        })
