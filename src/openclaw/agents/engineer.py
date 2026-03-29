from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent
from openclaw.config import settings

logger = structlog.get_logger()

ENGINEER_SYSTEM_PROMPT = """You are a world-class creative technologist and Lead Engineer of OpenClaw.

You build fully responsive, scroll-driven landing pages with cinematic motion, smooth parallax,
and section-to-section transitions inspired by Apple, Anthropic, and Vercel marketing sites.

TECH STACK:
- Next.js 15 (App Router, TypeScript)
- GSAP + ScrollTrigger for scroll-driven animations
- Lenis for smooth scrolling
- Three.js for WebGL scenes (when appropriate)
- Tailwind CSS for styling
- Framer Motion for component animations

STYLE:
- Modern, minimal, AI-infrastructure aesthetic
- Black/white base with neon accents (cyan, magenta, electric blue)
- Large typography (Inter or similar modern grotesk), fluid spacing
- Heavy whitespace, contrast, and motion
- Confident, technical, cinematic

SECTIONS TO BUILD:
- Hero with parallax + bold headline + video background
- Scrolling metrics counter (numbers animate on scroll)
- Feature grid with staggered reveal
- Code example with syntax highlighting
- "How it works" with pinned scroll animation
- Use cases with horizontal scroll
- Performance benchmarks
- Integrations grid
- Pricing teaser / CTA
- Footer

WORKFLOW:
1. scaffold_nextjs — create repo + push template
2. generate_code — for each section component with full GSAP animations
3. commit_and_deploy — push to GitHub, Vercel auto-deploys
4. get_deploy_url — return the live URL

CODE QUALITY:
- Lighthouse >= 90
- All images lazy-loaded
- Videos use poster images
- Scroll animations GPU-accelerated (transform, opacity only)
- Mobile-first responsive
- Proper semantic HTML and accessibility
- Clean, modular components
"""

SCAFFOLD_TOOL = {
    "name": "scaffold_nextjs",
    "description": "Create a new Next.js project from the base template and initialize a GitHub repo for it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project name (used for repo name and Vercel URL)."},
            "description": {"type": "string", "description": "Short project description for the GitHub repo."},
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
            "file_path": {"type": "string", "description": "Where to write the generated code (relative to project root)."},
            "project_name": {"type": "string"},
        },
        "required": ["description", "file_path", "project_name"],
    },
}

COMMIT_AND_DEPLOY_TOOL = {
    "name": "commit_and_deploy",
    "description": "Commit all current changes to GitHub and trigger a Vercel deploy. Use after generating/modifying code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "commit_message": {"type": "string", "description": "Descriptive commit message for this change."},
        },
        "required": ["project_name", "commit_message"],
    },
}

GET_DEPLOY_URL_TOOL = {
    "name": "get_deploy_url",
    "description": "Get the live Vercel URL for a project.",
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
    tools = [SCAFFOLD_TOOL, GENERATE_CODE_TOOL, COMMIT_AND_DEPLOY_TOOL, GET_DEPLOY_URL_TOOL]

    def _project_dir(self, project_name: str) -> str:
        return os.path.join(settings.STORAGE_PATH, project_name, "site")

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_name = tool_input.get("project_name", "unnamed")
        project_dir = self._project_dir(project_name)

        if tool_name == "scaffold_nextjs":
            # 1. Copy template
            template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "nextjs-base")
            template_dir = os.path.normpath(template_dir)
            if os.path.exists(template_dir):
                shutil.copytree(template_dir, project_dir, dirs_exist_ok=True)
            else:
                os.makedirs(project_dir, exist_ok=True)

            # 2. Create GitHub repo
            from openclaw.integrations.github_client import create_repo, get_authenticated_user, push_directory
            repo_data = await create_repo(
                name=project_name,
                description=tool_input.get("description", f"Website for {project_name} — built by OpenClaw"),
            )
            repo_full_name = repo_data["full_name"]

            # 3. Push initial scaffold
            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message="Initial scaffold: Next.js 15 + GSAP + Lenis + Tailwind",
            )

            # 4. Create Vercel project linked to GitHub (auto-deploys on push)
            from openclaw.integrations.vercel_client import create_project_from_github
            vercel_project = await create_project_from_github(project_name, repo_full_name)
            vercel_linked = bool(vercel_project.get("link"))

            return {
                "status": "scaffolded",
                "path": project_dir,
                "github_repo": repo_full_name,
                "github_url": f"https://github.com/{repo_full_name}",
                "vercel_project": vercel_project.get("name"),
                "vercel_auto_deploy": vercel_linked,
                "commit": push_result.get("commit_sha", "")[:8],
                "note": "Vercel auto-deploys on every GitHub push" if vercel_linked else "Vercel created but not linked to GitHub",
            }

        elif tool_name == "generate_code":
            filepath = os.path.join(project_dir, tool_input["file_path"])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            code = await self.run(
                f"Generate ONLY the code (no markdown, no explanation) for: {tool_input['description']}"
            )
            with open(filepath, "w") as f:
                f.write(code)
            return {"status": "written", "path": tool_input["file_path"]}

        elif tool_name == "commit_and_deploy":
            from openclaw.integrations.github_client import get_authenticated_user, push_directory

            # Push to GitHub — Vercel auto-deploys from the push
            user = await get_authenticated_user()
            repo_full_name = f"{user}/{project_name}"

            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message=tool_input["commit_message"],
            )

            return {
                "status": "committed_and_deploying",
                "commit": push_result.get("commit_sha", "")[:8],
                "commit_url": push_result.get("url"),
                "files_pushed": push_result.get("files_pushed"),
                "note": "Vercel auto-deploys from GitHub push",
            }

        elif tool_name == "get_deploy_url":
            from openclaw.integrations.vercel_client import get_latest_deployment
            deployment = await get_latest_deployment(project_name)
            if deployment:
                return {
                    "url": f"https://{deployment.get('url', '')}",
                    "state": deployment.get("readyState"),
                    "created": deployment.get("created"),
                }
            return {"error": "No deployments found"}

        return await super().handle_tool_call(tool_name, tool_input)
