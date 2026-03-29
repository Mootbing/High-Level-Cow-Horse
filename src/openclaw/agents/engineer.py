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
- Next.js (App Router, TypeScript)
- GSAP + ScrollTrigger for scroll-driven animations
- Lenis for smooth scrolling
- Tailwind CSS for styling

WORKFLOW (follow this EXACT order):
1. scaffold_nextjs — create repo + Vercel project + push template (1 call)
2. generate_code — write EACH file one at a time. Start with layout.tsx, then page.tsx, then components (max 12 calls)
3. verify_build — run npm build locally to catch errors BEFORE deploying (1 call)
4. If build fails: generate_code to fix the errors, then verify_build again
5. commit_and_deploy — push to GitHub, Vercel auto-deploys (1 call)
6. get_deploy_url — return the live URL (1 call)

CRITICAL RULES:
- You receive ONE comprehensive task with all sections and brand data. Build everything in this session.
- ALWAYS customize page.tsx and layout.tsx for the specific client — never leave generic template content.
- ALWAYS call verify_build before commit_and_deploy to catch syntax errors.
- ALWAYS call commit_and_deploy before your turn budget runs out.
- A deployed site with 5 good sections beats an undeployed site with 15 sections.
- Use 'use client' directive on components that use hooks, refs, or browser APIs.
- When generating code, output ONLY valid TypeScript/TSX — no markdown fences, no explanations.

CODE QUALITY:
- GPU-accelerated animations only (transform, opacity)
- Mobile-first responsive
- Proper semantic HTML
- All components in /components/ directory
- Clean imports with @/ alias
"""

SCAFFOLD_TOOL = {
    "name": "scaffold_nextjs",
    "description": "Create a new Next.js project from the base template and initialize a GitHub repo + Vercel project.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project name (used for repo name and Vercel URL)."},
            "description": {"type": "string", "description": "Short project description."},
        },
        "required": ["project_name"],
    },
}

GENERATE_CODE_TOOL = {
    "name": "generate_code",
    "description": "Write code to a file in the project. Output ONLY valid code — no markdown, no explanation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "What code to generate. Be specific about the client, brand, and section."},
            "file_path": {"type": "string", "description": "File path relative to project root (e.g., app/page.tsx, components/Hero.tsx)."},
            "project_name": {"type": "string"},
        },
        "required": ["description", "file_path", "project_name"],
    },
}

VERIFY_BUILD_TOOL = {
    "name": "verify_build",
    "description": "Run 'npm run build' locally to check for errors BEFORE deploying. Always call this before commit_and_deploy.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
        },
        "required": ["project_name"],
    },
}

COMMIT_AND_DEPLOY_TOOL = {
    "name": "commit_and_deploy",
    "description": "Push all code to GitHub. Vercel auto-deploys from the push. Only call AFTER verify_build passes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "commit_message": {"type": "string"},
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
    max_turns = 50
    tools = [SCAFFOLD_TOOL, GENERATE_CODE_TOOL, VERIFY_BUILD_TOOL, COMMIT_AND_DEPLOY_TOOL, GET_DEPLOY_URL_TOOL]

    def _project_dir(self, project_name: str) -> str:
        return os.path.join(settings.STORAGE_PATH, project_name, "site")

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_name = tool_input.get("project_name", "unnamed")
        project_dir = self._project_dir(project_name)

        if tool_name == "scaffold_nextjs":
            # 1. Create Next.js app with create-next-app (clean, working base)
            parent_dir = os.path.dirname(project_dir)
            os.makedirs(parent_dir, exist_ok=True)

            self.log.info("scaffold_creating_nextjs", project=project_name)
            scaffold_result = subprocess.run(
                [
                    "npx", "create-next-app@latest", "site",
                    "--typescript", "--tailwind", "--eslint",
                    "--app", "--src-dir=false",
                    "--import-alias=@/*",
                    "--no-turbopack",
                ],
                cwd=parent_dir,
                capture_output=True, text=True, timeout=120,
                input="n\n",  # No to any prompts
            )
            if scaffold_result.returncode != 0 and not os.path.exists(project_dir):
                # Fallback: create manually
                os.makedirs(project_dir, exist_ok=True)
                self.log.warning("create_next_app_failed", error=scaffold_result.stderr[:300])

            # 2. Install animation libraries on top
            if os.path.exists(os.path.join(project_dir, "package.json")):
                subprocess.run(
                    ["npm", "install", "--legacy-peer-deps",
                     "gsap", "@studio-freight/lenis", "framer-motion"],
                    cwd=project_dir,
                    capture_output=True, text=True, timeout=120,
                )
                self.log.info("animation_libs_installed")

            # 3. Create GitHub repo
            from openclaw.integrations.github_client import create_repo, push_directory
            repo_data = await create_repo(
                name=project_name,
                description=tool_input.get("description", f"Website for {project_name} — built by OpenClaw"),
            )
            repo_full_name = repo_data["full_name"]

            # 4. Create Vercel project linked to GitHub BEFORE push
            from openclaw.integrations.vercel_client import create_project_from_github
            vercel_project = await create_project_from_github(project_name, repo_full_name)
            vercel_linked = bool(vercel_project.get("link"))

            # 5. Push initial scaffold
            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message="Initial scaffold: create-next-app + GSAP + Lenis + Framer Motion",
            )

            return {
                "status": "scaffolded",
                "path": project_dir,
                "github_repo": repo_full_name,
                "github_url": f"https://github.com/{repo_full_name}",
                "vercel_project": vercel_project.get("name"),
                "vercel_auto_deploy": vercel_linked,
                "commit": push_result.get("commit_sha", "")[:8],
                "note": "Clean Next.js + Tailwind + GSAP + Lenis + Framer Motion. Customize with generate_code.",
            }

        elif tool_name == "generate_code":
            filepath = os.path.join(project_dir, tool_input["file_path"])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Generate code with project context
            existing_files = []
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
                for f in files:
                    if f.endswith((".tsx", ".ts", ".css", ".json")) and "lock" not in f:
                        existing_files.append(os.path.relpath(os.path.join(root, f), project_dir))

            code = await self.run(
                f"Generate ONLY valid TypeScript/TSX code for this file. No markdown fences. No explanations. Just the code.\n\n"
                f"File: {tool_input['file_path']}\n"
                f"Task: {tool_input['description']}\n"
                f"Existing files in project: {', '.join(existing_files[:20])}\n"
            )

            # Strip markdown fences if the model wrapped them
            code = code.strip()
            if code.startswith("```"):
                lines = code.split("\n")
                lines = lines[1:]  # Remove opening fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)

            with open(filepath, "w") as f:
                f.write(code)

            self.log.info("code_written", path=tool_input["file_path"], size=len(code))
            return {"status": "written", "path": tool_input["file_path"], "size": len(code)}

        elif tool_name == "verify_build":
            # Run npm install + build locally to catch errors
            try:
                # Install deps first
                install_result = subprocess.run(
                    ["npm", "install", "--legacy-peer-deps"],
                    cwd=project_dir,
                    capture_output=True, text=True, timeout=120,
                )

                # Run build
                build_result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=project_dir,
                    capture_output=True, text=True, timeout=120,
                )

                if build_result.returncode == 0:
                    self.log.info("build_passed", project=project_name)
                    return {
                        "status": "pass",
                        "message": "Build succeeded. Safe to commit_and_deploy.",
                    }
                else:
                    # Extract the error
                    error_output = build_result.stderr + build_result.stdout
                    # Get last 2000 chars of error
                    error_tail = error_output[-2000:] if len(error_output) > 2000 else error_output
                    self.log.warning("build_failed", project=project_name, error=error_tail[:200])
                    return {
                        "status": "fail",
                        "error": error_tail,
                        "message": "Build failed. Fix the errors with generate_code, then verify_build again.",
                    }
            except subprocess.TimeoutExpired:
                return {"status": "timeout", "message": "Build timed out after 120s."}
            except FileNotFoundError:
                return {"status": "skip", "message": "npm not available — skip verification and deploy."}

        elif tool_name == "commit_and_deploy":
            from openclaw.integrations.github_client import get_authenticated_user, push_directory

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
                "note": "Vercel auto-deploys from GitHub push. Use get_deploy_url to check.",
            }

        elif tool_name == "get_deploy_url":
            from openclaw.integrations.vercel_client import get_latest_deployment
            deployment = await get_latest_deployment(project_name)
            if deployment:
                return {
                    "url": f"https://{deployment.get('url', '')}",
                    "state": deployment.get("readyState"),
                }
            return {"error": "No deployments found yet. Vercel may still be building."}

        return await super().handle_tool_call(tool_name, tool_input)
