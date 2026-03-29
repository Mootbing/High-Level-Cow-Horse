from __future__ import annotations

import json
import os
import uuid
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent
from openclaw.config import settings

logger = structlog.get_logger()

DESIGNER_SYSTEM_PROMPT = """You are a world-class creative technologist and Lead Designer of OpenClaw.

Your aesthetic is inspired by Apple, Anthropic, and Vercel marketing sites — cinematic motion,
smooth parallax, section-to-section transitions, and strong visual hierarchy.

DESIGN DIRECTION:
- Modern, minimal, AI-infrastructure aesthetic: black/white, neon accents (cyan, magenta, electric blue)
- Large typography (Inter, Söhne, or similar modern grotesk), fluid spacing
- Heavy use of whitespace, contrast, and motion
- Confident, technical, cinematic feel
- Inspired by AI agent runtimes, robotics infra, and developer tools

When using generate_keyframe, write DETAILED prompts like:
"High-end website hero section mockup, dark background (#0a0a0a), large bold white typography,
subtle cyan neon glow accents, volumetric lighting, abstract geometric shapes floating in depth,
cinematic composition, 16:9, ultra-modern AI company aesthetic, inspired by Anthropic.com"

When using generate_video, write prompts for CINEMATIC LOOPS:
"Seamless looping cinematic background video for a scroll-driven website.
Abstract volumetric lighting on dark background. Slow camera dolly-in with depth-layered elements.
Neon accents (cyan, magenta, electric blue). Subtle particle systems and flowing data streams.
No text, no logos. High contrast, futuristic AI infrastructure branding.
Smooth, loop-safe start and end frames. 16:9 aspect ratio."

WORKFLOW:
1. First generate_video for the hero background (cinematic loop, 6-8 seconds)
2. Then generate_keyframe for each major section (hero, features, how-it-works, CTA)
3. Describe the full design spec (colors, fonts, spacing, animations) in your response

IMPORTANT — ASSET DELIVERY:
Every generated asset is automatically uploaded to the project's GitHub repo under /public/assets/.
Vercel serves files in /public/ at the site root, so the engineer can reference them as:
  - /assets/hero-video.mp4
  - /assets/keyframe-hero.png
  - /assets/keyframe-features.png

In your final response, LIST ALL generated asset URLs clearly, e.g.:

GENERATED ASSETS:
- Hero video: /assets/hero-video-abc12345.mp4
- Hero keyframe: /assets/keyframe-hero-abc12345.png
- Features keyframe: /assets/keyframe-features-abc12345.png

The PM will pass these URLs to the engineer so they are embedded in the site.

SECTIONS TO DESIGN FOR:
- Hero with parallax + bold headline + video background
- Scrolling metrics counter
- Feature grid with staggered reveal
- Code example with syntax highlighting
- "How it works" with pinned scroll animation
- Use cases with horizontal scroll
- Performance benchmarks / integrations grid
- CTA + Footer
"""

GENERATE_KEYFRAME_TOOL = {
    "name": "generate_keyframe",
    "description": "Generate a keyframe image using Nano Banana (Google AI image generation). The image is automatically uploaded to the GitHub repo at /public/assets/ so Vercel serves it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Detailed image generation prompt."},
            "project_name": {"type": "string", "description": "Project name (must match the GitHub repo name)."},
            "section": {"type": "string", "description": "Which section this keyframe is for (hero, about, features, etc)."},
        },
        "required": ["prompt", "project_name", "section"],
    },
}

GENERATE_VIDEO_TOOL = {
    "name": "generate_video",
    "description": "Generate a hero video using Veo (Google AI video generation). The video is automatically uploaded to the GitHub repo at /public/assets/ so Vercel serves it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Video generation prompt describing the scene."},
            "project_name": {"type": "string", "description": "Project name (must match the GitHub repo name)."},
            "duration": {"type": "integer", "description": "Video duration in seconds (4, 6, or 8).", "default": 6},
        },
        "required": ["prompt", "project_name"],
    },
}


@register_agent("designer")
class DesignerAgent(BaseAgent):
    agent_type = "designer"
    system_prompt = DESIGNER_SYSTEM_PROMPT
    tools = [GENERATE_KEYFRAME_TOOL, GENERATE_VIDEO_TOOL]

    async def _upload_asset_to_repo(
        self, project_name: str, filename: str, content: bytes
    ) -> str:
        """Upload a generated asset to the GitHub repo's public/assets/ directory.

        Returns the public URL path (e.g., /assets/hero-video.mp4) that Vercel
        will serve after the next deploy.
        """
        from openclaw.integrations.github_client import get_authenticated_user, upload_file

        user = await get_authenticated_user()
        repo_full_name = f"{user}/{project_name}"
        repo_path = f"public/assets/{filename}"

        try:
            result = await upload_file(
                repo_full_name=repo_full_name,
                file_path_in_repo=repo_path,
                content=content,
                commit_message=f"Add generated asset: {filename}",
            )
            public_url = f"/assets/{filename}"
            self.log.info(
                "asset_uploaded_to_repo",
                repo=repo_full_name,
                path=repo_path,
                public_url=public_url,
                commit=result.get("commit_sha", "")[:8],
            )
            return public_url
        except Exception as e:
            self.log.error("asset_upload_failed", repo=repo_full_name, filename=filename, error=str(e))
            raise

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_name = tool_input.get("project_name", "unnamed")
        project_dir = os.path.join(settings.STORAGE_PATH, project_name)
        os.makedirs(project_dir, exist_ok=True)

        if tool_name == "generate_keyframe":
            from openclaw.integrations.google_ai import generate_image

            image_data = await generate_image(tool_input["prompt"])
            section = tool_input.get("section", "unknown")
            filename = f"keyframe-{section}-{uuid.uuid4().hex[:8]}.png"

            # Save locally as backup
            filepath = os.path.join(project_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)

            # Upload to GitHub repo so Vercel can serve it
            public_url = await self._upload_asset_to_repo(project_name, filename, image_data)

            return {
                "status": "generated",
                "local_path": filepath,
                "filename": filename,
                "public_url": public_url,
                "section": section,
            }

        elif tool_name == "generate_video":
            from openclaw.integrations.google_ai import generate_video, download_video

            video_uri = await generate_video(
                prompt=tool_input["prompt"],
                duration_seconds=tool_input.get("duration", 6),
            )
            video_data = await download_video(video_uri)
            filename = f"hero-video-{uuid.uuid4().hex[:8]}.mp4"

            # Save locally as backup
            filepath = os.path.join(project_dir, filename)
            with open(filepath, "wb") as f:
                f.write(video_data)

            # Upload to GitHub repo so Vercel can serve it
            public_url = await self._upload_asset_to_repo(project_name, filename, video_data)

            return {
                "status": "generated",
                "local_path": filepath,
                "filename": filename,
                "public_url": public_url,
            }

        return await super().handle_tool_call(tool_name, tool_input)
