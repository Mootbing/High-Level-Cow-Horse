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

ENGINEER_SYSTEM_PROMPT = """You are a world-class creative technologist and Lead Engineer of Clarmi Design Studio.

You build fully responsive, scroll-driven landing pages with cinematic motion, smooth parallax,
and section-to-section transitions inspired by Apple, Anthropic, and Vercel marketing sites.

TECH STACK:
- Next.js (App Router, TypeScript)
- GSAP + ScrollTrigger for scroll-driven animations
- Lenis for smooth scrolling
- Tailwind CSS for styling

WORKFLOW (follow this EXACT order):
1. scaffold_nextjs — set up local template + push to repo (GitHub repo & Vercel project are pre-created)
2. generate_code — write EACH file one at a time. Start with layout.tsx, then page.tsx, then components (max 12 calls)
3. verify_build — run npm build locally to catch errors BEFORE deploying (1 call)
4. If build fails: generate_code to fix the errors, then verify_build again
5. commit_and_deploy — push to a FEATURE BRANCH on GitHub, Vercel auto-deploys (1 call)
6. get_deploy_url — return the live URL (1 call)

BRANCHING STRATEGY:
- Push directly to main. Vercel auto-deploys from main.
- commit_and_deploy pushes your code to the main branch.

CRITICAL RULES:
- You receive ONE comprehensive task with all sections and brand data. Build everything in this session.
- ALWAYS customize page.tsx and layout.tsx for the specific client — never leave generic template content.
- NEVER build a generic/template site. Every piece of text, heading, company name, and description must come DIRECTLY from the brand data or old site content provided in your task.
- If your task does NOT contain real brand data (company name, colors, actual content from the client's site), STOP and respond with an error: "ERROR: No brand data provided. Cannot build site without real client content." Do NOT invent fake company names, fake testimonials, or placeholder content.
- NEVER invent company names, product names, testimonials, team members, pricing, or any content. Use ONLY what was given to you.
- If your task is about fixing infrastructure issues (Vercel 401, deployment config, etc.) that you cannot fix with code, respond with a message explaining the issue is not code-related and requires manual infrastructure configuration. Do NOT rebuild the site.
- ALWAYS call verify_build before commit_and_deploy to catch syntax errors.
- ALWAYS call commit_and_deploy before your turn budget runs out.
- A deployed site with 5 good sections beats an undeployed site with 15 sections.
- Use 'use client' directive on components that use hooks, refs, or browser APIs.
- When generating code, output ONLY valid TypeScript/TSX — no markdown fences, no explanations.

DESIGNER ASSET INTEGRATION:
- If your task includes ASSET URLs from the designer (paths like /assets/hero-video-xxx.mp4 or /assets/keyframe-hero-xxx.png), you MUST use them in the site.
- These files are already committed to the repo's /public/assets/ directory and Vercel serves them at the root.
- Use the hero VIDEO as a background video in the Hero section:
    <video autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover">
      <source src="/assets/hero-video-xxx.mp4" type="video/mp4" />
    </video>
- Use KEYFRAME IMAGES as section backgrounds or decorative elements:
    <div style={{ backgroundImage: 'url(/assets/keyframe-features-xxx.png)' }} />
  Or as <img> tags in galleries, feature cards, etc.
- NEVER skip designer assets — if they are provided, they MUST appear in the deployed site.
- If no asset URLs are provided, use CSS gradients and abstract backgrounds instead.

CONTENT REUSE FROM OLD SITE:
- When given image URLs from the old site, USE THEM directly as src attributes (they're still hosted)
- Reuse the old site's actual copy/blurbs/descriptions — don't make up generic text
- Keep any important links, menu items, contact info, hours, addresses from the old site
- Recreate the same navigation structure but with better design
- If the old site had a menu/pricing page, include that exact content
- If the old site had team photos, testimonials, or gallery images, include those URLs

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

MERGE_TO_MAIN_TOOL = {
    "name": "merge_to_main",
    "description": "Merge the feature branch into main via a pull request. Use after QA passes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project name (used to resolve the repo)."},
            "branch": {"type": "string", "description": "The feature branch to merge into main."},
        },
        "required": ["project_name", "branch"],
    },
}


@register_agent("engineer")
class EngineerAgent(BaseAgent):
    agent_type = "engineer"
    system_prompt = ENGINEER_SYSTEM_PROMPT
    max_turns = 50
    tools = [SCAFFOLD_TOOL, GENERATE_CODE_TOOL, VERIFY_BUILD_TOOL, COMMIT_AND_DEPLOY_TOOL, GET_DEPLOY_URL_TOOL]

    async def process_task(self, message: dict) -> dict:
        self._current_project_id = message.get("project_id")
        payload = message.get("payload", {})
        if not self._current_project_id:
            self._current_project_id = payload.get("project_id")
        return await super().process_task(message)

    def _project_dir(self, project_name: str) -> str:
        return os.path.join(settings.STORAGE_PATH, project_name, "site")

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        project_name = tool_input.get("project_name", "unnamed")
        project_dir = self._project_dir(project_name)

        if tool_name == "scaffold_nextjs":
            # Guard: if we already have a repo + vercel for this project, skip re-scaffolding
            existing_repo = await self._get_project_metadata(project_name, "github_repo")
            existing_vercel = await self._get_project_metadata(project_name, "vercel_project")
            if existing_repo and existing_vercel:
                self.log.info("scaffold_skipped_already_exists", repo=existing_repo, vercel=existing_vercel)
                return {
                    "status": "already_scaffolded",
                    "path": project_dir,
                    "github_repo": existing_repo,
                    "github_url": f"https://github.com/{existing_repo}",
                    "vercel_project": existing_vercel,
                    "vercel_auto_deploy": True,
                    "note": "Project already scaffolded. Skipping to avoid duplicate repos. Proceed with generate_code.",
                }

            # 1. Create a clean Next.js app with proper package.json
            os.makedirs(project_dir, exist_ok=True)
            self.log.info("scaffold_creating_nextjs", project=project_name)

            # Write package.json with latest deps
            import json as _json
            pkg = {
                "name": project_name,
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint"
                },
                "dependencies": {
                    "next": "latest",
                    "react": "^19.0.0",
                    "react-dom": "^19.0.0",
                    "gsap": "^3.12.0",
                    "@studio-freight/lenis": "^1.0.0",
                    "framer-motion": "^11.0.0"
                },
                "devDependencies": {
                    "@types/node": "latest",
                    "@types/react": "latest",
                    "@types/react-dom": "latest",
                    "typescript": "latest",
                    "tailwindcss": "latest",
                    "postcss": "latest",
                    "autoprefixer": "latest",
                    "@tailwindcss/postcss": "latest"
                }
            }
            with open(os.path.join(project_dir, "package.json"), "w") as f:
                _json.dump(pkg, f, indent=2)

            # Write minimal config files
            with open(os.path.join(project_dir, "tsconfig.json"), "w") as f:
                _json.dump({
                    "compilerOptions": {
                        "target": "ES2017", "lib": ["dom", "dom.iterable", "esnext"],
                        "allowJs": True, "skipLibCheck": True, "strict": True,
                        "noEmit": True, "esModuleInterop": True, "module": "esnext",
                        "moduleResolution": "bundler", "resolveJsonModule": True,
                        "isolatedModules": True, "jsx": "preserve", "incremental": True,
                        "plugins": [{"name": "next"}],
                        "paths": {"@/*": ["./*"]}
                    },
                    "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
                    "exclude": ["node_modules"]
                }, f, indent=2)

            with open(os.path.join(project_dir, "next.config.ts"), "w") as f:
                f.write("import type { NextConfig } from 'next';\nconst nextConfig: NextConfig = {};\nexport default nextConfig;\n")

            with open(os.path.join(project_dir, "postcss.config.mjs"), "w") as f:
                f.write("const config = { plugins: { '@tailwindcss/postcss': {} } };\nexport default config;\n")

            with open(os.path.join(project_dir, "next-env.d.ts"), "w") as f:
                f.write('/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n')

            # Create app directory with minimal layout + page
            os.makedirs(os.path.join(project_dir, "app"), exist_ok=True)
            with open(os.path.join(project_dir, "app", "globals.css"), "w") as f:
                f.write("@import 'tailwindcss';\n")
            with open(os.path.join(project_dir, "app", "layout.tsx"), "w") as f:
                f.write("""import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: '%s', description: 'Built by Clarmi Design Studio' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
""" % project_name)
            with open(os.path.join(project_dir, "app", "page.tsx"), "w") as f:
                f.write("export default function Home() { return <main><h1>%s</h1></main> }\n" % project_name)

            os.makedirs(os.path.join(project_dir, "components"), exist_ok=True)

            # 2. Install deps
            try:
                subprocess.run(
                    ["npm", "install", "--legacy-peer-deps"],
                    cwd=project_dir, capture_output=True, text=True, timeout=120,
                )
                self.log.info("deps_installed")
            except Exception as e:
                self.log.warning("npm_install_failed", error=str(e)[:200])

            # 3. Resolve GitHub repo — reuse pre-created one from project metadata if available
            from openclaw.integrations.github_client import create_repo, push_directory
            repo_full_name = await self._get_project_metadata(project_name, "github_repo")
            if repo_full_name:
                self.log.info("reusing_pre_created_repo", repo=repo_full_name)
            else:
                repo_data = await create_repo(
                    name=project_name,
                    description=tool_input.get("description", f"Website for {project_name} — built by Clarmi Design Studio"),
                )
                repo_full_name = repo_data["full_name"]

            # 4. Resolve Vercel project — reuse pre-created one if available
            from openclaw.integrations.vercel_client import create_project_from_github
            vercel_name = await self._get_project_metadata(project_name, "vercel_project")
            if vercel_name:
                self.log.info("reusing_pre_created_vercel", vercel=vercel_name)
                vercel_linked = True
            else:
                vercel_project = await create_project_from_github(project_name, repo_full_name)
                vercel_name = vercel_project.get("name")
                vercel_linked = bool(vercel_project.get("link"))

            # 5. Save repo + vercel back to Project metadata so subsequent calls reuse them
            #    This prevents duplicate repos/vercel projects on retries
            await self._save_project_metadata(project_name, {
                "github_repo": repo_full_name,
                "vercel_project": vercel_name,
            })

            # 6. Push initial scaffold to main
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
                "vercel_project": vercel_name,
                "vercel_auto_deploy": vercel_linked,
                "commit": push_result.get("commit_sha", "")[:8],
                "note": "Clean Next.js + Tailwind + GSAP + Lenis + Framer Motion. Customize with generate_code.",
            }

        elif tool_name == "generate_code":
            filepath = os.path.join(project_dir, tool_input["file_path"])
            # Prevent path traversal — resolved path must stay inside project_dir
            real_filepath = os.path.realpath(filepath)
            real_project_dir = os.path.realpath(project_dir)
            if not real_filepath.startswith(real_project_dir + os.sep):
                return {"status": "error", "message": f"Path traversal blocked: {tool_input['file_path']}"}
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Single API call — no multi-turn loop, no tools
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system="You are a code generator. Output ONLY valid TypeScript/TSX code. No markdown fences. No explanations. No comments about what you're doing. Just the raw code that goes in the file.",
                messages=[{
                    "role": "user",
                    "content": f"Generate the code for: {tool_input['file_path']}\n\nDescription: {tool_input['description']}",
                }],
            )

            code = response.content[0].text.strip()

            # Strip markdown fences
            if code.startswith("```"):
                lines = code.split("\n")
                lines = lines[1:]
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
            from openclaw.integrations.github_client import (
                get_authenticated_user,
                push_directory,
            )

            # Resolve the repo — prefer pre-created metadata
            repo_full_name = await self._get_project_metadata(project_name, "github_repo")
            if not repo_full_name:
                user = await get_authenticated_user()
                repo_full_name = f"{user}/{project_name}"

            # Push directly to main — Vercel auto-deploys from main
            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message=tool_input["commit_message"],
                branch="main",
            )

            return {
                "status": "committed_and_deploying",
                "commit": push_result.get("commit_sha", "")[:8],
                "commit_url": push_result.get("url"),
                "files_pushed": push_result.get("files_pushed"),
                "branch": "main",
                "note": "Pushed to main. Vercel auto-deploys from GitHub push. Use get_deploy_url to check.",
            }

        elif tool_name == "get_deploy_url":
            from openclaw.integrations.vercel_client import get_latest_deployment, ensure_protection_disabled
            # Resolve vercel project name — prefer pre-created metadata
            vercel_name = await self._get_project_metadata(project_name, "vercel_project")
            effective_name = vercel_name or project_name

            # Ensure protection is off before QA runs
            protection_warning = None
            try:
                await ensure_protection_disabled(effective_name)
            except Exception as e:
                protection_warning = f"Could not disable deployment protection: {e}"
                self.log.warning("protection_disable_failed_at_deploy", error=str(e)[:200])

            deployment = await get_latest_deployment(effective_name)
            if deployment:
                live_url = f"https://{deployment.get('url', '')}"

                # Save deployed URL to project record
                pid = getattr(self, "_current_project_id", None)
                if pid and live_url:
                    try:
                        from openclaw.db.session import async_session_factory
                        from openclaw.models.project import Project
                        async with async_session_factory() as session:
                            project = await session.get(Project, pid)
                            if project:
                                project.deployed_url = live_url
                                await session.commit()
                    except Exception as e:
                        self.log.warning("deployed_url_save_failed", error=str(e)[:200])

                result = {
                    "url": live_url,
                    "state": deployment.get("readyState"),
                }
                if protection_warning:
                    result["protection_warning"] = protection_warning
                return result
            return {"error": "No deployments found yet. Vercel may still be building."}

        return await super().handle_tool_call(tool_name, tool_input)

    async def _save_project_metadata(self, project_name: str, data: dict) -> None:
        """Save metadata keys to the Project record so subsequent calls find them.

        Prevents duplicate GitHub repos and Vercel projects on retries.
        """
        try:
            from openclaw.db.session import async_session_factory
            from openclaw.models.project import Project
            from slugify import slugify
            from sqlalchemy import select

            async with async_session_factory() as session:
                project = None

                pid = getattr(self, "_current_project_id", None)
                if pid:
                    project = await session.get(Project, pid)

                if not project:
                    slug_prefix = slugify(project_name)
                    stmt = select(Project).where(Project.slug.startswith(slug_prefix))
                    result = await session.execute(stmt)
                    project = result.scalars().first()

                if not project:
                    stmt = select(Project).where(
                        Project.name.ilike(f"%{project_name}%")
                    ).limit(1)
                    result = await session.execute(stmt)
                    project = result.scalars().first()

                if project:
                    existing = project.metadata_ or {}
                    project.metadata_ = {**existing, **data}
                    await session.commit()
                    self.log.info("project_metadata_saved", project=project_name, keys=list(data.keys()))
                else:
                    self.log.warning("project_metadata_save_skipped_no_project", project=project_name)
        except Exception as exc:
            self.log.warning("project_metadata_save_failed", project=project_name, error=str(exc)[:200])

    async def _get_project_metadata(self, project_name: str, key: str) -> str | None:
        """Look up a metadata value from the Project record.

        Tries project_id first, then slug prefix, then name search.
        Returns None if the project or key is not found.
        """
        try:
            from openclaw.db.session import async_session_factory
            from openclaw.models.project import Project
            from slugify import slugify
            from sqlalchemy import select

            async with async_session_factory() as session:
                project = None

                # Primary: look up by project_id if available
                pid = getattr(self, "_current_project_id", None)
                if pid:
                    project = await session.get(Project, pid)

                # Fallback: slug prefix match
                if not project:
                    slug_prefix = slugify(project_name)
                    stmt = select(Project).where(Project.slug.startswith(slug_prefix))
                    result = await session.execute(stmt)
                    project = result.scalars().first()

                # Fallback: name search
                if not project:
                    stmt = select(Project).where(
                        Project.name.ilike(f"%{project_name}%")
                    ).limit(1)
                    result = await session.execute(stmt)
                    project = result.scalars().first()

                if project and project.metadata_:
                    return project.metadata_.get(key)
        except Exception as exc:
            self.log.warning("metadata_lookup_failed", project=project_name, key=key, error=str(exc)[:200])
        return None
