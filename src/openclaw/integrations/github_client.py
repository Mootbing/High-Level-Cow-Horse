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


async def add_collaborator(
    repo_full_name: str, username: str, permission: str = "push"
) -> bool:
    """Add a collaborator to a GitHub repo.

    *permission* can be 'pull', 'push', or 'admin'.
    Returns True if the invitation was sent (or user already has access).
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.put(
            f"{GITHUB_API}/repos/{repo_full_name}/collaborators/{username}",
            json={"permission": permission},
            headers=_headers(),
        )
        if resp.status_code in (201, 204):
            logger.info("collaborator_added", repo=repo_full_name, user=username, permission=permission)
            return True
        logger.warning(
            "collaborator_add_failed",
            repo=repo_full_name,
            user=username,
            status=resp.status_code,
        )
        return False


REPO_COLLABORATORS = ["mootbing"]


async def create_repo(name: str, description: str = "") -> dict:
    """Create a new GitHub repo under the bot account.

    If the repo already exists, returns its info instead of failing.
    Automatically shares the repo with REPO_COLLABORATORS.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GITHUB_API}/user/repos",
            json={
                "name": name,
                "description": description or f"Built by Clarmi Design Studio",
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

        # Share repo with all configured collaborators
        for collab in REPO_COLLABORATORS:
            await add_collaborator(data["full_name"], collab)

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


async def upload_file(
    repo_full_name: str,
    file_path_in_repo: str,
    content: bytes,
    commit_message: str,
    branch: str = "main",
) -> dict:
    """Upload a single file (binary-safe) to a GitHub repo via the Contents API.

    If the file already exists, it is overwritten. Returns the commit info.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        headers = _headers()
        url = f"{GITHUB_API}/repos/{repo_full_name}/contents/{file_path_in_repo}"

        # Check if the file already exists (need its SHA to update)
        existing_sha = None
        check = await client.get(url, headers=headers, params={"ref": branch})
        if check.status_code == 200:
            existing_sha = check.json().get("sha")

        payload = {
            "message": commit_message + "\n\nCo-Authored-By: Mootbing <mootbing@users.noreply.github.com>",
            "content": base64.b64encode(content).decode(),
            "branch": branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        resp = await client.put(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        logger.info(
            "file_uploaded",
            repo=repo_full_name,
            path=file_path_in_repo,
            sha=data.get("content", {}).get("sha", "")[:8],
        )
        return {
            "path": file_path_in_repo,
            "sha": data.get("content", {}).get("sha", ""),
            "commit_sha": data.get("commit", {}).get("sha", ""),
            "html_url": data.get("content", {}).get("html_url", ""),
        }


async def create_branch(repo_full_name: str, branch_name: str, from_branch: str = "main") -> dict:
    """Create a new branch from an existing branch.

    Returns the ref object for the new branch.  If the branch already exists,
    returns its current ref instead of failing.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        headers = _headers()

        # Get the SHA of the source branch
        ref_resp = await client.get(
            f"{GITHUB_API}/repos/{repo_full_name}/git/ref/heads/{from_branch}",
            headers=headers,
        )
        ref_resp.raise_for_status()
        source_sha = ref_resp.json()["object"]["sha"]

        # Create the new branch ref
        create_resp = await client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/git/refs",
            json={"ref": f"refs/heads/{branch_name}", "sha": source_sha},
            headers=headers,
        )

        if create_resp.status_code == 422:
            # Branch already exists — fetch it
            existing = await client.get(
                f"{GITHUB_API}/repos/{repo_full_name}/git/ref/heads/{branch_name}",
                headers=headers,
            )
            existing.raise_for_status()
            logger.info("branch_already_exists", repo=repo_full_name, branch=branch_name)
            return existing.json()

        create_resp.raise_for_status()
        logger.info("branch_created", repo=repo_full_name, branch=branch_name, from_branch=from_branch)
        return create_resp.json()


async def create_pull_request(
    repo_full_name: str,
    head: str,
    base: str = "main",
    title: str = "",
    body: str = "",
) -> dict:
    """Create a pull request from *head* into *base*.

    Returns the PR data dict including 'number' and 'html_url'.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/pulls",
            json={
                "title": title or f"Merge {head} into {base}",
                "head": head,
                "base": base,
                "body": body,
            },
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("pr_created", repo=repo_full_name, number=data["number"], url=data["html_url"])
        return data


async def merge_pull_request(
    repo_full_name: str,
    pull_number: int,
    merge_method: str = "squash",
) -> dict:
    """Merge an open pull request.

    *merge_method* can be 'merge', 'squash', or 'rebase'.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.put(
            f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pull_number}/merge",
            json={"merge_method": merge_method},
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("pr_merged", repo=repo_full_name, number=pull_number, sha=data.get("sha", "")[:8])
        return data


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

        # 3. Create tree — use base_tree to MERGE with existing repo files
        #    (preserves designer assets in public/assets/ that aren't in local dir)
        tree_body: dict = {"tree": tree_items}
        if current_sha:
            # Get the tree SHA from the current commit so we can merge
            commit_info = await client.get(
                f"{GITHUB_API}/repos/{repo_full_name}/git/commits/{current_sha}",
                headers=headers,
            )
            commit_info.raise_for_status()
            tree_body["base_tree"] = commit_info.json()["tree"]["sha"]

        tree_resp = await client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/git/trees",
            json=tree_body,
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
