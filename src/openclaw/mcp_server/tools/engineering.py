"""Engineering tools — scaffold, write code, build, and deploy Next.js projects."""

import asyncio
import json
import os
import subprocess

import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


def _project_dir(project_name: str) -> str:
    return os.path.join(settings.STORAGE_PATH, project_name, "site")


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
            "gsap": "^3.12.0", "@studio-freight/lenis": "^1.0.0", "framer-motion": "^11.0.0",
        },
        "devDependencies": {
            "@types/node": "latest", "@types/react": "latest", "@types/react-dom": "latest",
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
    """Run npm install + npm run build locally to catch errors before deploying.

    Always call this before deploy(). If it fails, fix the code with write_code and try again.
    """
    project_dir = _project_dir(project_name)

    try:
        await asyncio.to_thread(
            subprocess.run,
            ["npm", "install", "--legacy-peer-deps"],
            cwd=project_dir, capture_output=True, text=True, timeout=120,
        )
        build_result = await asyncio.to_thread(
            subprocess.run,
            ["npm", "run", "build"],
            cwd=project_dir, capture_output=True, text=True, timeout=120,
        )

        if build_result.returncode == 0:
            return json.dumps({"status": "pass", "message": "Build succeeded. Safe to deploy."})
        else:
            error_output = build_result.stderr + build_result.stdout
            error_tail = error_output[-2000:] if len(error_output) > 2000 else error_output
            return json.dumps({
                "status": "fail",
                "error": error_tail,
                "message": "Build failed. Fix errors with write_code, then verify_build again.",
            })
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "timeout", "message": "Build timed out after 120s."})
    except FileNotFoundError:
        return json.dumps({"status": "skip", "message": "npm not available — skip and deploy."})


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

    # Get Vercel URL
    vercel_name = await _get_project_metadata(project_name, "vercel_project") or project_name
    try:
        await ensure_protection_disabled(vercel_name)
    except Exception:
        pass

    deployment = await get_latest_deployment(vercel_name)
    live_url = f"https://{deployment['url']}" if deployment else None

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
