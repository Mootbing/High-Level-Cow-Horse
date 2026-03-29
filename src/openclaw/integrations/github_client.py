"""GitHub API client for creating repos and pushing code for generated websites."""

from __future__ import annotations

import base64
import os

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.GITHUB_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def create_repo(name: str, description: str = "") -> dict:
    """Create a new GitHub repo under the bot account.

    If the repo already exists, returns its info instead of failing.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GITHUB_API}/user/repos",
            json={
                "name": name,
                "description": description or f"Built by OpenClaw AI Design Agency",
                "private": True,
                "auto_init": True,  # Creates initial commit on main branch
            },
            headers=_headers(),
        )
        if resp.status_code == 422:
            # Repo already exists — fetch it
            user = await get_authenticated_user()
            return await get_repo(f"{user}/{name}")
        resp.raise_for_status()
        data = resp.json()
        logger.info("repo_created", name=data["full_name"], url=data["html_url"])
        return data


async def get_repo(full_name: str) -> dict:
    """Get repo info by full name (owner/repo)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{GITHUB_API}/repos/{full_name}", headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def get_authenticated_user() -> str:
    """Get the username of the authenticated GitHub user."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{GITHUB_API}/user", headers=_headers())
        resp.raise_for_status()
        return resp.json()["login"]


async def delete_repo(full_name: str) -> bool:
    """Delete a GitHub repo. Returns True if deleted."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(f"{GITHUB_API}/repos/{full_name}", headers=_headers())
        if resp.status_code == 204:
            logger.info("repo_deleted", name=full_name)
            return True
        logger.warning("repo_delete_failed", name=full_name, status=resp.status_code)
        return False


async def push_directory(repo_full_name: str, local_dir: str, commit_message: str, branch: str = "main") -> dict:
    """Push an entire local directory to a GitHub repo using the Git trees API.

    This creates a single commit with all files, which is efficient and atomic.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        headers = _headers()

        # 1. Get the current commit SHA on the branch (or handle empty repo)
        is_empty_repo = False
        current_sha = None
        ref_resp = await client.get(
            f"{GITHUB_API}/repos/{repo_full_name}/git/ref/heads/{branch}",
            headers=headers,
        )
        if ref_resp.status_code == 404:
            # Try default branch
            repo_info = await get_repo(repo_full_name)
            default_branch = repo_info.get("default_branch", "main")
            ref_resp = await client.get(
                f"{GITHUB_API}/repos/{repo_full_name}/git/ref/heads/{default_branch}",
                headers=headers,
            )
            if ref_resp.status_code == 409 or ref_resp.status_code == 404:
                # Empty repo — no commits yet
                is_empty_repo = True
            else:
                ref_resp.raise_for_status()
                current_sha = ref_resp.json()["object"]["sha"]
        else:
            ref_resp.raise_for_status()
            current_sha = ref_resp.json()["object"]["sha"]

        # 2. Create blobs for each file
        tree_items = []
        for root, dirs, files in os.walk(local_dir):
            # Skip node_modules, .next, .git
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git", "__pycache__")]
            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, local_dir)

                # Read file as bytes
                with open(fpath, "rb") as f:
                    content = f.read()

                # Create blob
                blob_resp = await client.post(
                    f"{GITHUB_API}/repos/{repo_full_name}/git/blobs",
                    json={
                        "content": base64.b64encode(content).decode(),
                        "encoding": "base64",
                    },
                    headers=headers,
                )
                blob_resp.raise_for_status()
                blob_sha = blob_resp.json()["sha"]

                tree_items.append({
                    "path": rel_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })

        # 3. Create tree
        tree_resp = await client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/git/trees",
            json={"tree": tree_items},
            headers=headers,
        )
        tree_resp.raise_for_status()
        tree_sha = tree_resp.json()["sha"]

        # 4. Create commit
        commit_body = {
            "message": commit_message + "\n\nCo-Authored-By: Mootbing <mootbing@users.noreply.github.com>",
            "tree": tree_sha,
            "author": {
                "name": "jason-clarmi",
                "email": "jason@clarmi.studio",
            },
            "committer": {
                "name": "jason-clarmi",
                "email": "jason@clarmi.studio",
            },
        }
        if current_sha:
            commit_body["parents"] = [current_sha]
        else:
            commit_body["parents"] = []

        commit_resp = await client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/git/commits",
            json=commit_body,
            headers=headers,
        )
        commit_resp.raise_for_status()
        new_commit_sha = commit_resp.json()["sha"]

        # 5. Update or create branch ref
        if is_empty_repo:
            ref_create = await client.post(
                f"{GITHUB_API}/repos/{repo_full_name}/git/refs",
                json={"ref": f"refs/heads/{branch}", "sha": new_commit_sha},
                headers=headers,
            )
            ref_create.raise_for_status()
        else:
            ref_update = await client.patch(
                f"{GITHUB_API}/repos/{repo_full_name}/git/refs/heads/{branch}",
                json={"sha": new_commit_sha},
                headers=headers,
            )
            ref_update.raise_for_status()

        logger.info(
            "code_pushed",
            repo=repo_full_name,
            commit=new_commit_sha[:8],
            files=len(tree_items),
        )
        return {
            "commit_sha": new_commit_sha,
            "files_pushed": len(tree_items),
            "repo": repo_full_name,
            "url": f"https://github.com/{repo_full_name}/commit/{new_commit_sha}",
        }
