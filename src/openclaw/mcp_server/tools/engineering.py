"""Engineering tools — scaffold, write code, build, and deploy Next.js projects."""

import asyncio
import json
import os
import shutil
import subprocess

import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


def _project_dir(project_name: str) -> str:
    # Sanitize project_name to prevent path traversal
    safe_name = os.path.basename(project_name.replace("..", "").strip("/"))
    if not safe_name:
        safe_name = "unnamed"
    return os.path.join(settings.STORAGE_PATH, safe_name, "site")


async def _get_project_metadata(project_name: str, key: str) -> str | None:
    """Look up a metadata value from the Project record."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from slugify import slugify
    from sqlalchemy import select

    try:
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
                return project.metadata_.get(key)
    except Exception as exc:
        logger.warning("metadata_lookup_failed", project=project_name, key=key, error=str(exc)[:200])
    return None


async def _save_project_metadata(project_name: str, data: dict) -> None:
    """Save metadata keys to the Project record."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from slugify import slugify
    from sqlalchemy import select

    try:
        async with async_session_factory() as session:
            slug_prefix = slugify(project_name)
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                stmt = select(Project).where(Project.name.ilike(f"%{project_name}%")).limit(1)
                result = await session.execute(stmt)
                project = result.scalars().first()

            if project:
                existing = project.metadata_ or {}
                project.metadata_ = {**existing, **data}
                await session.commit()
    except Exception as exc:
        logger.warning("metadata_save_failed", project=project_name, error=str(exc)[:200])


@mcp.tool()
async def scaffold_nextjs(project_name: str, description: str | None = None) -> str:
    """Create a Next.js project from template and push to the pre-provisioned GitHub repo.

    Sets up: package.json (Next.js + GSAP + Lenis + Framer Motion + Tailwind), tsconfig,
    PostCSS config, minimal layout.tsx and page.tsx. Runs npm install and pushes to GitHub.

    Skip this if the project is already scaffolded (check the response).
    """
    project_dir = _project_dir(project_name)

    # Check if already scaffolded
    existing_repo = await _get_project_metadata(project_name, "github_repo")
    existing_vercel = await _get_project_metadata(project_name, "vercel_project")
    if existing_repo and existing_vercel and os.path.exists(os.path.join(project_dir, "package.json")):
        return json.dumps({
            "status": "already_scaffolded",
            "path": project_dir,
            "github_repo": existing_repo,
            "vercel_project": existing_vercel,
            "note": "Already scaffolded. Proceed with write_code.",
        })

    os.makedirs(project_dir, exist_ok=True)

    # package.json
    pkg = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"},
        "dependencies": {
            "next": "latest", "react": "^19.0.0", "react-dom": "^19.0.0",
            "gsap": "^3.12.0", "lenis": "^1.1.0", "framer-motion": "^11.0.0",
            "three": "^0.172.0", "@react-three/fiber": "^9.0.0",
            "@react-three/drei": "^9.0.0", "@react-three/postprocessing": "^3.0.0",
            "postprocessing": "^6.36.0",
        },
        "devDependencies": {
            "@types/node": "latest", "@types/react": "latest", "@types/react-dom": "latest",
            "@types/three": "latest",
            "typescript": "latest", "tailwindcss": "latest", "postcss": "latest",
            "autoprefixer": "latest", "@tailwindcss/postcss": "latest",
        },
    }
    with open(os.path.join(project_dir, "package.json"), "w") as f:
        json.dump(pkg, f, indent=2)

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2017", "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True, "skipLibCheck": True, "strict": True, "noEmit": True,
            "esModuleInterop": True, "module": "esnext", "moduleResolution": "bundler",
            "resolveJsonModule": True, "isolatedModules": True, "jsx": "preserve",
            "incremental": True, "plugins": [{"name": "next"}], "paths": {"@/*": ["./*"]},
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
        "exclude": ["node_modules"],
    }
    with open(os.path.join(project_dir, "tsconfig.json"), "w") as f:
        json.dump(tsconfig, f, indent=2)

    # Config files
    with open(os.path.join(project_dir, "next.config.ts"), "w") as f:
        f.write("import type { NextConfig } from 'next';\nconst nextConfig: NextConfig = {};\nexport default nextConfig;\n")
    with open(os.path.join(project_dir, "postcss.config.mjs"), "w") as f:
        f.write("const config = { plugins: { '@tailwindcss/postcss': {} } };\nexport default config;\n")
    with open(os.path.join(project_dir, "next-env.d.ts"), "w") as f:
        f.write('/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n')

    # .npmrc for peer dependency resolution (R3F ecosystem has conflicts)
    with open(os.path.join(project_dir, ".npmrc"), "w") as f:
        f.write("legacy-peer-deps=true\n")

    # App directory
    os.makedirs(os.path.join(project_dir, "app"), exist_ok=True)
    with open(os.path.join(project_dir, "app", "globals.css"), "w") as f:
        f.write("@import 'tailwindcss';\n")
    with open(os.path.join(project_dir, "app", "layout.tsx"), "w") as f:
        f.write(f"""import type {{ Metadata }} from 'next'
import './globals.css'

export const metadata: Metadata = {{ title: '{project_name}', description: 'Built by Clarmi Design Studio' }}

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  )
}}
""")
    with open(os.path.join(project_dir, "app", "page.tsx"), "w") as f:
        f.write(f"export default function Home() {{ return <main><h1>{project_name}</h1></main> }}\n")
    os.makedirs(os.path.join(project_dir, "components"), exist_ok=True)

    # npm install (run in thread to avoid blocking event loop)
    try:
        await asyncio.to_thread(
            subprocess.run,
            ["npm", "install", "--legacy-peer-deps"],
            cwd=project_dir, capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        logger.warning("npm_install_failed", error=str(e)[:200])

    # Resolve GitHub repo
    from openclaw.integrations.github_client import create_repo, push_directory
    repo_full_name = existing_repo
    if not repo_full_name:
        repo_data = await create_repo(
            name=project_name,
            description=description or f"Website for {project_name} — built by Clarmi Design Studio",
        )
        repo_full_name = repo_data["full_name"]

    # Resolve Vercel project
    from openclaw.integrations.vercel_client import create_project_from_github
    vercel_name = existing_vercel
    if not vercel_name:
        vercel_data = await create_project_from_github(project_name, repo_full_name)
        vercel_name = vercel_data.get("name")

    # Save metadata
    await _save_project_metadata(project_name, {
        "github_repo": repo_full_name,
        "vercel_project": vercel_name,
    })

    # Push initial scaffold
    push_result = await push_directory(
        repo_full_name, project_dir,
        commit_message="Initial scaffold: Next.js + GSAP + Lenis + Framer Motion + Tailwind",
    )

    return json.dumps({
        "status": "scaffolded",
        "path": project_dir,
        "github_repo": repo_full_name,
        "github_url": f"https://github.com/{repo_full_name}",
        "vercel_project": vercel_name,
        "commit": push_result.get("commit_sha", "")[:8],
        "note": "Scaffold complete. Use write_code to add components.",
    })


@mcp.tool()
async def list_files(project_name: str, directory: str = ".") -> str:
    """List files in a project directory.

    directory is relative to the project root (e.g. ".", "app", "components").
    Returns a tree of files with sizes. Use this before read_code or edit_code
    to understand the project structure.
    """
    project_dir = _project_dir(project_name)
    target = os.path.join(project_dir, directory)

    real_target = os.path.realpath(target)
    real_project_dir = os.path.realpath(project_dir)
    if not real_target.startswith(real_project_dir):
        return json.dumps({"status": "error", "message": f"Path traversal blocked: {directory}"})

    if not os.path.isdir(target):
        return json.dumps({"status": "error", "message": f"Directory not found: {directory}"})

    files = []
    for root, dirs, filenames in os.walk(target):
        # Skip node_modules and .next
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for name in filenames:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, project_dir)
            size = os.path.getsize(full)
            files.append({"path": rel, "size": size})

    files.sort(key=lambda f: f["path"])
    return json.dumps({"directory": directory, "files": files, "count": len(files)})


@mcp.tool()
async def read_code(project_name: str, file_path: str) -> str:
    """Read a file from the project directory and return its contents.

    file_path is relative to the project root (e.g. app/page.tsx, components/Hero.tsx).
    Use this before edit_code to see the current state of a file.
    """
    project_dir = _project_dir(project_name)
    filepath = os.path.join(project_dir, file_path)

    real_filepath = os.path.realpath(filepath)
    real_project_dir = os.path.realpath(project_dir)
    if not real_filepath.startswith(real_project_dir + os.sep):
        return json.dumps({"status": "error", "message": f"Path traversal blocked: {file_path}"})

    if not os.path.isfile(filepath):
        return json.dumps({"status": "error", "message": f"File not found: {file_path}"})

    with open(filepath, "r") as f:
        content = f.read()

    return json.dumps({"path": file_path, "size": len(content), "content": content})


@mcp.tool()
async def edit_code(
    project_name: str, file_path: str, old_string: str, new_string: str
) -> str:
    """Edit a file by replacing a specific string with new content.

    Use this for targeted changes instead of rewriting entire files with write_code.
    The old_string must appear exactly once in the file (including whitespace/indentation).

    Workflow: read_code → find the section to change → edit_code with old/new strings.
    """
    project_dir = _project_dir(project_name)
    filepath = os.path.join(project_dir, file_path)

    real_filepath = os.path.realpath(filepath)
    real_project_dir = os.path.realpath(project_dir)
    if not real_filepath.startswith(real_project_dir + os.sep):
        return json.dumps({"status": "error", "message": f"Path traversal blocked: {file_path}"})

    if not os.path.isfile(filepath):
        return json.dumps({"status": "error", "message": f"File not found: {file_path}"})

    with open(filepath, "r") as f:
        content = f.read()

    count = content.count(old_string)
    if count == 0:
        return json.dumps({
            "status": "error",
            "message": "old_string not found in file. Use read_code to check the current contents.",
        })
    if count > 1:
        return json.dumps({
            "status": "error",
            "message": f"old_string found {count} times — must be unique. Include more surrounding context.",
        })

    new_content = content.replace(old_string, new_string, 1)
    with open(filepath, "w") as f:
        f.write(new_content)

    logger.info("code_edited", path=file_path, old_len=len(old_string), new_len=len(new_string))
    return json.dumps({"status": "edited", "path": file_path, "size": len(new_content)})


@mcp.tool()
async def write_code(project_name: str, file_path: str, code: str) -> str:
    """Write a code file to the project directory.

    file_path is relative to the project root (e.g. app/page.tsx, components/Hero.tsx).
    code should be valid TypeScript/TSX — no markdown fences.
    """
    project_dir = _project_dir(project_name)
    filepath = os.path.join(project_dir, file_path)

    # Path traversal protection
    real_filepath = os.path.realpath(filepath)
    real_project_dir = os.path.realpath(project_dir)
    if not real_filepath.startswith(real_project_dir + os.sep):
        return json.dumps({"status": "error", "message": f"Path traversal blocked: {file_path}"})

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(code)

    logger.info("code_written", path=file_path, size=len(code))
    return json.dumps({"status": "written", "path": file_path, "size": len(code)})


@mcp.tool()
async def verify_build(project_name: str) -> str:
    """Run a clean build that mirrors Vercel: delete node_modules → npm install → tsc → npm run build.

    Always call this before deploy(). If it fails, fix the code with write_code and try again.
    """
    project_dir = _project_dir(project_name)

    if not os.path.isdir(project_dir):
        return json.dumps({"status": "error", "message": f"Project directory not found: {project_dir}"})

    # ── Step 1: Clean slate (simulate fresh Vercel environment) ──
    for dirname in ("node_modules", ".next"):
        target = os.path.join(project_dir, dirname)
        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)
    logger.info("verify_build_clean", project=project_name)

    # ── Step 2: npm install ──
    try:
        install_result = await asyncio.to_thread(
            subprocess.run,
            ["npm", "install", "--legacy-peer-deps"],
            cwd=project_dir, capture_output=True, text=True, timeout=180,
        )
        if install_result.returncode != 0:
            error_output = (install_result.stderr + install_result.stdout)[-2000:]
            return json.dumps({
                "status": "fail",
                "step": "npm install",
                "error": error_output,
                "message": "npm install failed. Check package.json for dependency conflicts.",
            })
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "timeout", "step": "npm install", "message": "npm install timed out after 180s."})
    except FileNotFoundError:
        return json.dumps({"status": "skip", "message": "npm not available — skip and deploy."})
    except Exception as e:
        logger.error("verify_build_install_crash", project=project_name, error=str(e)[:300])
        return json.dumps({"status": "error", "step": "npm install", "message": f"Unexpected error: {str(e)[:200]}"})

    # ── Step 3: TypeScript check (non-blocking — warnings only) ──
    tsc_warnings = None
    try:
        tsc_result = await asyncio.to_thread(
            subprocess.run,
            ["npx", "tsc", "--noEmit"],
            cwd=project_dir, capture_output=True, text=True, timeout=60,
        )
        if tsc_result.returncode != 0:
            tsc_warnings = (tsc_result.stderr + tsc_result.stdout)[-2000:]
            logger.warning("verify_build_tsc_errors", project=project_name, errors=tsc_warnings[:500])
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass  # tsc is advisory — next build catches type errors too

    # ── Step 4: npm run build ──
    try:
        build_result = await asyncio.to_thread(
            subprocess.run,
            ["npm", "run", "build"],
            cwd=project_dir, capture_output=True, text=True, timeout=180,
        )
        if build_result.returncode != 0:
            error_output = (build_result.stderr + build_result.stdout)[-2000:]
            result = {
                "status": "fail",
                "step": "npm run build",
                "error": error_output,
                "message": "Build failed. Fix errors with write_code, then verify_build again.",
            }
            if tsc_warnings:
                result["tsc_warnings"] = tsc_warnings
            return json.dumps(result)
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "timeout", "step": "npm run build", "message": "Build timed out after 180s."})
    except Exception as e:
        logger.error("verify_build_build_crash", project=project_name, error=str(e)[:300])
        return json.dumps({"status": "error", "step": "npm run build", "message": f"Unexpected error: {str(e)[:200]}"})

    # ── All passed ──
    result = {"status": "pass", "message": "Build succeeded (clean install). Safe to deploy."}
    if tsc_warnings:
        result["tsc_warnings"] = tsc_warnings
    logger.info("verify_build_pass", project=project_name)
    return json.dumps(result)


@mcp.tool()
async def deploy(project_name: str, commit_message: str) -> str:
    """Push all code to GitHub main branch. Vercel auto-deploys from the push.

    Only call after verify_build passes. Returns the live Vercel URL.
    """
    from openclaw.integrations.github_client import get_authenticated_user, push_directory
    from openclaw.integrations.vercel_client import get_latest_deployment, ensure_protection_disabled

    project_dir = _project_dir(project_name)

    # Resolve repo
    repo_full_name = await _get_project_metadata(project_name, "github_repo")
    if not repo_full_name:
        user = await get_authenticated_user()
        repo_full_name = f"{user}/{project_name}"

    # Push to main
    push_result = await push_directory(
        repo_full_name, project_dir,
        commit_message=commit_message, branch="main",
    )

    # Get Vercel URL — wait briefly for the new deployment to register
    vercel_name = await _get_project_metadata(project_name, "vercel_project") or project_name
    try:
        await ensure_protection_disabled(vercel_name)
    except Exception:
        pass

    # Poll a few times to catch the new deployment (Vercel webhook has latency)
    live_url = None
    push_sha = push_result.get("commit_sha", "")
    for _ in range(4):
        await asyncio.sleep(5)
        deployment = await get_latest_deployment(vercel_name)
        if deployment:
            live_url = f"https://{deployment['url']}"
            break

    # Save deployed URL to project record
    if live_url:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from slugify import slugify
        from sqlalchemy import select
        try:
            async with async_session_factory() as session:
                slug_prefix = slugify(project_name)
                stmt = select(Project).where(Project.slug.startswith(slug_prefix))
                result = await session.execute(stmt)
                project = result.scalars().first()
                if project:
                    project.deployed_url = live_url
                    project.status = "deployed"
                    await session.commit()
        except Exception:
            pass

    return json.dumps({
        "status": "deployed",
        "commit": push_result.get("commit_sha", "")[:8],
        "files_pushed": push_result.get("files_pushed"),
        "url": live_url,
        "note": "Pushed to main. Vercel auto-deploys." + (" URL may take 30-60s to be ready." if live_url else " Check Vercel dashboard for deploy status."),
    })


@mcp.tool()
async def deploy_preview(project_name: str, branch_name: str, commit_message: str) -> str:
    """Push code to a feature branch (not main) so Vercel creates a preview deployment.

    Use this for client revisions — the client reviews the preview URL before it goes live.
    Returns the Vercel preview URL. Call approve_preview to merge to main after client approval.
    """
    from openclaw.integrations.github_client import (
        create_branch,
        get_authenticated_user,
        push_directory,
    )
    from openclaw.integrations.vercel_client import get_latest_deployment

    project_dir = _project_dir(project_name)

    # Resolve repo
    repo_full_name = await _get_project_metadata(project_name, "github_repo")
    if not repo_full_name:
        user = await get_authenticated_user()
        repo_full_name = f"{user}/{project_name}"

    # Create branch from main
    await create_branch(repo_full_name, branch_name, from_branch="main")

    # Push to the branch
    push_result = await push_directory(
        repo_full_name, project_dir,
        commit_message=commit_message, branch=branch_name,
    )

    # Poll for Vercel preview deployment (no target filter — previews aren't "production")
    vercel_name = await _get_project_metadata(project_name, "vercel_project") or project_name
    push_sha = push_result.get("commit_sha", "")
    preview_url = None
    for _ in range(8):
        await asyncio.sleep(5)
        deployment = await get_latest_deployment(vercel_name, target=None)
        if deployment and deployment.get("meta", {}).get("githubCommitSha", "") == push_sha:
            preview_url = f"https://{deployment['url']}"
            break
        # Fallback: if latest deploy is newer than our push, it's probably ours
        if deployment and not preview_url:
            preview_url = f"https://{deployment['url']}"

    return json.dumps({
        "status": "preview_deployed",
        "branch": branch_name,
        "commit": push_result.get("commit_sha", "")[:8],
        "preview_url": preview_url,
        "repo": repo_full_name,
        "note": f"Preview on branch '{branch_name}'. Call approve_preview to merge to main after client approval.",
    })


@mcp.tool()
async def approve_preview(project_name: str, branch_name: str) -> str:
    """Merge a preview branch into main after client approval. Vercel auto-deploys the merge.

    This creates a PR, squash-merges it, and returns the live production URL.
    """
    from openclaw.integrations.github_client import (
        create_pull_request,
        get_authenticated_user,
        merge_pull_request,
    )
    from openclaw.integrations.vercel_client import get_latest_deployment

    repo_full_name = await _get_project_metadata(project_name, "github_repo")
    if not repo_full_name:
        user = await get_authenticated_user()
        repo_full_name = f"{user}/{project_name}"

    # Create PR and merge (try squash, fall back to regular merge)
    pr = await create_pull_request(
        repo_full_name,
        head=branch_name,
        base="main",
        title=f"Client revision: {branch_name}",
        body="Approved by client via Clarmi funnel.",
    )
    try:
        merge_result = await merge_pull_request(repo_full_name, pr["number"], merge_method="squash")
    except Exception:
        merge_result = await merge_pull_request(repo_full_name, pr["number"], merge_method="merge")

    # Poll for production deployment
    vercel_name = await _get_project_metadata(project_name, "vercel_project") or project_name
    live_url = None
    for _ in range(5):
        await asyncio.sleep(5)
        deployment = await get_latest_deployment(vercel_name)
        if deployment:
            live_url = f"https://{deployment['url']}"
            break

    # Update deployed URL
    if live_url:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from slugify import slugify
        from sqlalchemy import select
        try:
            async with async_session_factory() as session:
                slug_prefix = slugify(project_name)
                stmt = select(Project).where(Project.slug.startswith(slug_prefix))
                result = await session.execute(stmt)
                project = result.scalars().first()
                if project:
                    project.deployed_url = live_url
                    await session.commit()
        except Exception:
            pass

    return json.dumps({
        "status": "merged_and_deployed",
        "branch": branch_name,
        "pr_number": pr["number"],
        "merge_sha": merge_result.get("sha", "")[:8],
        "url": live_url,
        "note": "Merged to main and deployed to production.",
    })
