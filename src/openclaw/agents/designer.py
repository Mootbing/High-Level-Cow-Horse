from __future__ import annotations

import json
import os
import uuid
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent
from openclaw.config import settings

logger = structlog.get_logger()

DESIGNER_SYSTEM_PROMPT = """You are the Lead Designer of OpenClaw, an AI-powered digital design agency.

You create world-class web designs. Given a brief, you:
1. Generate keyframe images for each website section using the generate_keyframe tool
2. Generate hero videos using the generate_video tool
3. Create a comprehensive design spec (colors, fonts, spacing, layout)

Design principles:
- Modern, premium aesthetic
- Dark themes with accent colors are popular
- Generous whitespace and typography hierarchy
- Scroll-driven reveal animations
- Mobile-first responsive design

When generating keyframes, be specific with prompts:
- Include color palette references
- Specify lighting and mood
- Describe composition and layout
- Reference specific design styles (glassmorphism, neubrutalism, etc.)

Always check the knowledge base for current trends before designing.
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
