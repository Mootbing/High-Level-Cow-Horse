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
    "description": "Generate a keyframe image using Nano Banana (Google AI image generation).",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Detailed image generation prompt."},
            "project_name": {"type": "string", "description": "Project name for file organization."},
            "section": {"type": "string", "description": "Which section this keyframe is for (hero, about, features, etc)."},
        },
        "required": ["prompt", "project_name", "section"],
    },
}

GENERATE_VIDEO_TOOL = {
    "name": "generate_video",
    "description": "Generate a hero video using Veo (Google AI video generation).",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Video generation prompt describing the scene."},
            "project_name": {"type": "string", "description": "Project name."},
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

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_dir = os.path.join(settings.STORAGE_PATH, tool_input.get("project_name", "unnamed"))
        os.makedirs(project_dir, exist_ok=True)

        if tool_name == "generate_keyframe":
            from openclaw.integrations.google_ai import generate_image
            image_data = await generate_image(tool_input["prompt"])
            filename = f"keyframe-{tool_input.get('section', 'unknown')}-{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(project_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            return {"status": "generated", "path": filepath, "filename": filename}

        elif tool_name == "generate_video":
            from openclaw.integrations.google_ai import generate_video, download_video
            video_uri = await generate_video(
                prompt=tool_input["prompt"],
                duration_seconds=tool_input.get("duration", 6),
            )
            video_data = await download_video(video_uri)
            filename = f"hero-video-{uuid.uuid4().hex[:8]}.mp4"
            filepath = os.path.join(project_dir, filename)
            with open(filepath, "wb") as f:
                f.write(video_data)
            return {"status": "generated", "path": filepath, "filename": filename}

        return await super().handle_tool_call(tool_name, tool_input)
