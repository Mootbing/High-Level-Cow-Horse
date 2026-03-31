"""Design tools — generate images (Nano Banana) and videos (Veo 3), upload to GitHub repo."""

import json
import os
import uuid

import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


async def _get_project_repo(project_name: str) -> str:
    """Look up the GitHub repo full name from project metadata."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from slugify import slugify
    from sqlalchemy import select

    async with async_session_factory() as session:
        slug_prefix = slugify(project_name)
        stmt = select(Project).where(Project.slug.startswith(slug_prefix))
        result = await session.execute(stmt)
        project = result.scalars().first()

        if not project:
            stmt = select(Project).where(Project.name.ilike(f"%{project_name}%")).limit(1)
            result = await session.execute(stmt)
            project = result.scalars().first()

        if project and project.metadata_:
            repo = project.metadata_.get("github_repo")
            if repo:
                return repo

    from openclaw.integrations.github_client import get_authenticated_user
    user = await get_authenticated_user()
    return f"{user}/{project_name}"


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
async def generate_video(prompt: str, project_name: str, duration: int = 8) -> str:
    """Generate a hero video using Veo 3 (Google AI) and upload to the project's GitHub repo.

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
