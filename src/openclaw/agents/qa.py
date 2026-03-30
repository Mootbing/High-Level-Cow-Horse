from __future__ import annotations

import asyncio
import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

QA_SYSTEM_PROMPT = """You are the QA Engineer of Clarmi Design Studio, a digital design agency.

You test generated websites for quality. WORKFLOW (follow this exact order):

1. FIRST: call verify_url to confirm the Vercel deployment is live and returns HTTP 200.
   - If the deployment is still building (readyState != READY), wait and retry.
   - If the URL returns 401, Vercel deployment protection is on. Call disable_protection with the project name, then retry verify_url. If it STILL returns 401 after disabling protection, mark as FAIL with "deployment_protection_unresolved".
   - If the URL returns other non-200 status, report FAIL.
2. THEN: Take screenshots at multiple viewports (1440px, 1024px, 768px, 375px)
3. THEN: Run Lighthouse audit (performance, accessibility, SEO, best practices)
4. THEN: If asset URLs were provided, call verify_assets to confirm they load correctly.

Produce a structured QA report:
- Live URL (the Vercel URL)
- Deployment status (READY / BUILDING / ERROR)
- HTTP status code
- Asset check results (pass/fail for each asset URL)
- Overall score (0-100)
- Pass/Fail (threshold: 85)
- List of issues found with severity
- Screenshots at each viewport
- Lighthouse scores

If the site passes (>=85) AND the deployment is READY AND assets load, mark as APPROVED.
If it fails, create detailed bug reports for the Engineer to fix.
"""

VERIFY_URL_TOOL = {
    "name": "verify_url",
    "description": "Check that a deployed Vercel URL is live. Returns HTTP status code and Vercel deployment state (READY, BUILDING, ERROR). Retries up to 3 times with backoff if the site is still building.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The full Vercel URL to check (e.g., https://project-name.vercel.app)."},
            "project_name": {"type": "string", "description": "Vercel project name, used to check deployment readyState."},
        },
        "required": ["url"],
    },
}

VERIFY_ASSETS_TOOL = {
    "name": "verify_assets",
    "description": "Check that designer-generated assets (videos, images) are accessible on the deployed site. Returns pass/fail for each asset URL.",
    "input_schema": {
        "type": "object",
        "properties": {
            "base_url": {"type": "string", "description": "The site base URL (e.g., https://project-name.vercel.app)."},
            "asset_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of asset paths to check (e.g., ['/assets/hero-video.mp4', '/assets/keyframe-hero.png']).",
            },
        },
        "required": ["base_url", "asset_paths"],
    },
}

SCREENSHOT_TOOL = {
    "name": "take_screenshot",
    "description": "Take a screenshot of a website at a specific viewport width.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "viewport_width": {"type": "integer", "default": 1440},
            "full_page": {"type": "boolean", "default": True},
        },
        "required": ["url"],
    },
}

LIGHTHOUSE_TOOL = {
    "name": "run_lighthouse",
    "description": "Run a Lighthouse audit on a URL and return scores.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
        },
        "required": ["url"],
    },
}

DISABLE_PROTECTION_TOOL = {
    "name": "disable_protection",
    "description": "Disable Vercel deployment protection for a project. Use this if verify_url returns a 401. After calling this, retry verify_url.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Vercel project name."},
        },
        "required": ["project_name"],
    },
}


@register_agent("qa")
class QAAgent(BaseAgent):
    agent_type = "qa"
    system_prompt = QA_SYSTEM_PROMPT
    tools = [VERIFY_URL_TOOL, VERIFY_ASSETS_TOOL, SCREENSHOT_TOOL, LIGHTHOUSE_TOOL, DISABLE_PROTECTION_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "verify_url":
            import httpx

            url = tool_input["url"]
            project_name = tool_input.get("project_name")

            # Check Vercel deployment state if project_name provided
            deploy_state = None
            deploy_url = None
            if project_name:
                try:
                    from openclaw.integrations.vercel_client import get_latest_deployment
                    deployment = await get_latest_deployment(project_name)
                    if deployment:
                        deploy_state = deployment.get("readyState")
                        deploy_url = f"https://{deployment.get('url', '')}"
                except Exception as e:
                    self.log.warning("vercel_state_check_failed", error=str(e))

            # Retry with backoff — deployments take time
            last_status = None
            for attempt in range(4):
                if attempt > 0:
                    wait_secs = 15 * attempt  # 15s, 30s, 45s
                    self.log.info("verify_url_retry", attempt=attempt + 1, wait_s=wait_secs)
                    await asyncio.sleep(wait_secs)

                try:
                    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                        resp = await client.get(url)
                        last_status = resp.status_code

                        if resp.status_code == 200:
                            return {
                                "status": "live",
                                "http_status": 200,
                                "url": url,
                                "deploy_state": deploy_state or "READY",
                                "deploy_url": deploy_url or url,
                            }
                        elif resp.status_code == 401:
                            # Vercel deployment protection is blocking access
                            return {
                                "status": "protection_enabled",
                                "http_status": 401,
                                "url": url,
                                "deploy_state": deploy_state or "READY",
                                "deploy_url": deploy_url or url,
                                "message": (
                                    "Vercel deployment protection is blocking access (HTTP 401). "
                                    "Call disable_protection with the project name, then retry verify_url."
                                ),
                            }
                except Exception as e:
                    last_status = str(e)
                    self.log.warning("verify_url_error", attempt=attempt + 1, error=str(e)[:200])

                # Re-check deploy state on retry
                if project_name:
                    try:
                        from openclaw.integrations.vercel_client import get_latest_deployment
                        deployment = await get_latest_deployment(project_name)
                        if deployment:
                            deploy_state = deployment.get("readyState")
                            if deploy_state == "READY":
                                deploy_url = f"https://{deployment.get('url', '')}"
                    except Exception:
                        pass

            return {
                "status": "fail",
                "http_status": last_status,
                "url": url,
                "deploy_state": deploy_state or "UNKNOWN",
                "message": f"Site did not return 200 after retries. Last status: {last_status}",
            }

        elif tool_name == "verify_assets":
            import httpx

            base_url = tool_input["base_url"].rstrip("/")
            asset_paths = tool_input.get("asset_paths", [])
            results = []

            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                for path in asset_paths:
                    full_url = f"{base_url}{path}"
                    try:
                        resp = await client.head(full_url)
                        results.append({
                            "path": path,
                            "url": full_url,
                            "status": resp.status_code,
                            "pass": resp.status_code == 200,
                            "content_type": resp.headers.get("content-type", ""),
                        })
                    except Exception as e:
                        results.append({
                            "path": path,
                            "url": full_url,
                            "status": "error",
                            "pass": False,
                            "error": str(e)[:200],
                        })

            all_passed = all(r["pass"] for r in results)
            return {
                "status": "pass" if all_passed else "fail",
                "total": len(results),
                "passed": sum(1 for r in results if r["pass"]),
                "failed": sum(1 for r in results if not r["pass"]),
                "details": results,
            }

        elif tool_name == "take_screenshot":
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page(
                        viewport={"width": tool_input.get("viewport_width", 1440), "height": 900}
                    )
                    await page.goto(tool_input["url"], wait_until="networkidle")
                    screenshot = await page.screenshot(full_page=tool_input.get("full_page", True))
                    await browser.close()

                    import os, uuid
                    from openclaw.config import settings
                    filename = f"screenshot-{tool_input.get('viewport_width', 1440)}-{uuid.uuid4().hex[:8]}.png"
                    filepath = os.path.join(settings.STORAGE_PATH, "qa", filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(screenshot)
                    # Verify the file was actually written and has content
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        return {"status": "captured", "path": filepath, "size": os.path.getsize(filepath)}
                    else:
                        return {"status": "failed", "error": f"Screenshot file missing or empty at {filepath}", "path": filepath}
            except Exception as e:
                return {"error": str(e)}

        elif tool_name == "run_lighthouse":
            import subprocess
            try:
                result = subprocess.run(
                    ["npx", "lighthouse", tool_input["url"], "--output=json", "--chrome-flags=--headless --no-sandbox"],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    categories = data.get("categories", {})
                    scores = {
                        name: int((cat.get("score", 0) or 0) * 100)
                        for name, cat in categories.items()
                    }
                    return {"scores": scores}
                return {"error": result.stderr[:500]}
            except Exception as e:
                return {"error": str(e)}

        elif tool_name == "disable_protection":
            project_name = tool_input["project_name"]
            try:
                from openclaw.integrations.vercel_client import ensure_protection_disabled
                await ensure_protection_disabled(project_name)
                return {
                    "status": "success",
                    "message": f"Deployment protection disabled for {project_name}. Retry verify_url now.",
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)[:500],
                    "message": "Could not disable protection. Mark the site as FAIL.",
                }

        return await super().handle_tool_call(tool_name, tool_input)
