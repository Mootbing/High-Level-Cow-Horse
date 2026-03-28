from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.worker import register_agent
from openclaw.config import settings

logger = structlog.get_logger()

ENGINEER_SYSTEM_PROMPT = """You are the Lead Engineer of OpenClaw, an AI-powered digital design agency.

You build premium scrolling websites using Next.js 15 with:
- GSAP + ScrollTrigger for scroll-driven animations
- Lenis for smooth scrolling
- Three.js for WebGL scenes (when appropriate)
- Tailwind CSS for styling
- TypeScript

Given design specs and keyframes, you:
1. Scaffold a new Next.js project from the template
2. Generate page components with fancy scroll animations
3. Integrate generated images and videos as assets
4. Run `next build` to verify it compiles
5. Deploy to Vercel and return the preview URL

Code quality requirements:
- Lighthouse performance score >= 90
- All images lazy-loaded with proper srcset
- Videos use poster images and lazy loading
- Scroll animations are GPU-accelerated (transform, opacity only)
- Mobile-first responsive design
- Proper semantic HTML and accessibility
"""

SCAFFOLD_TOOL = {
    "name": "scaffold_nextjs",
    "description": "Create a new Next.js project from the base template.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
        },
        "required": ["project_name"],
    },
}

GENERATE_CODE_TOOL = {
    "name": "generate_code",
    "description": "Generate code for a specific component or page using Claude.",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "What code to generate."},
            "file_path": {"type": "string", "description": "Where to write the generated code."},
            "project_name": {"type": "string"},
        },
        "required": ["description", "file_path", "project_name"],
    },
}

DEPLOY_TOOL = {
    "name": "vercel_deploy",
    "description": "Deploy the built Next.js site to Vercel.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
        },
        "required": ["project_name"],
    },
}


@register_agent("engineer")
class EngineerAgent(BaseAgent):
    agent_type = "engineer"
    system_prompt = ENGINEER_SYSTEM_PROMPT
    tools = [SCAFFOLD_TOOL, GENERATE_CODE_TOOL, DEPLOY_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_name = tool_input.get("project_name", "unnamed")
        project_dir = os.path.join(settings.STORAGE_PATH, project_name, "site")

        if tool_name == "scaffold_nextjs":
            template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "nextjs-base")
            template_dir = os.path.normpath(template_dir)
            if os.path.exists(template_dir):
                shutil.copytree(template_dir, project_dir, dirs_exist_ok=True)
            else:
                os.makedirs(project_dir, exist_ok=True)
            return {"status": "scaffolded", "path": project_dir}

        elif tool_name == "generate_code":
            filepath = os.path.join(project_dir, tool_input["file_path"])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # Use Claude to generate the actual code
            code = await self.run(
                f"Generate ONLY the code (no markdown, no explanation) for: {tool_input['description']}"
            )
            with open(filepath, "w") as f:
                f.write(code)
            return {"status": "written", "path": filepath}

        elif tool_name == "vercel_deploy":
            from openclaw.integrations.vercel_client import create_deployment
            # Collect all files in the project directory
            files = []
            for root, dirs, filenames in os.walk(project_dir):
                for fname in filenames:
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, project_dir)
                    with open(fpath, "r", errors="ignore") as f:
                        files.append({"file": rel_path, "data": f.read()})
            result = await create_deployment(project_name, files)
            return {"status": "deployed", "url": result.get("url"), "id": result.get("id")}

        return await super().handle_tool_call(tool_name, tool_input)
