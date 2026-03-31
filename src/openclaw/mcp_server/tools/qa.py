"""QA tools — verify URLs, take screenshots, run Lighthouse audits."""

import asyncio
import json
import os
import subprocess
import uuid

import httpx
import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


@mcp.tool()
async def verify_url(url: str) -> str:
    """Check if a URL is accessible. Returns HTTP status, response time, and any protection issues.

    Use this to verify a deployed site is live before running screenshots or Lighthouse.
    """
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url)
                body_preview = resp.text[:500] if resp.text else ""

                is_protected = (
                    resp.status_code == 401
                    or "protection" in body_preview.lower()
                    or "password" in body_preview.lower()
                )

                result = {
                    "status_code": resp.status_code,
                    "url": str(resp.url),
                    "is_protected": is_protected,
                    "content_length": len(resp.content),
                }

                if resp.status_code == 200 and not is_protected:
                    result["verdict"] = "ACCESSIBLE"
                elif is_protected:
                    result["verdict"] = "PROTECTED — deployment protection may be enabled"
                else:
                    result["verdict"] = f"HTTP {resp.status_code}"

                return json.dumps(result)
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            return json.dumps({"error": str(e), "url": url, "verdict": "UNREACHABLE"})

    return json.dumps({"error": "Max retries exceeded", "url": url})


@mcp.tool()
async def take_screenshot(url: str, viewport_widths: list[int] | None = None) -> str:
    """Take screenshots of a URL at multiple viewport widths using Playwright.

    Default viewports: 1440 (desktop), 1024 (tablet landscape), 768 (tablet), 375 (mobile).
    Returns file paths to the saved screenshots.
    """
    widths = viewport_widths or [1440, 1024, 768, 375]

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return json.dumps({"error": "Playwright not installed. Run: playwright install chromium"})

    screenshots = []
    screenshot_dir = os.path.join(settings.STORAGE_PATH, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for width in widths:
                page = await browser.new_page(viewport={"width": width, "height": 900})
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(2000)

                    filename = f"screenshot-{width}w-{uuid.uuid4().hex[:6]}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    await page.screenshot(path=filepath, full_page=True)
                    screenshots.append({"width": width, "path": filepath})
                except Exception as e:
                    screenshots.append({"width": width, "error": str(e)[:200]})
                finally:
                    await page.close()
        finally:
            await browser.close()

    return json.dumps({"url": url, "screenshots": screenshots})


@mcp.tool()
async def run_lighthouse(url: str) -> str:
    """Run a Lighthouse audit on a URL. Returns performance, accessibility, SEO, and best practices scores.

    Requires Node.js and npx to be available. Score >= 85 is considered passing.
    """
    try:
        result = subprocess.run(
            [
                "npx", "lighthouse", url,
                "--output=json", "--chrome-flags=--headless --no-sandbox",
                "--only-categories=performance,accessibility,best-practices,seo",
                "--quiet",
            ],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            return json.dumps({"error": f"Lighthouse failed: {result.stderr[:500]}"})

        data = json.loads(result.stdout)
        categories = data.get("categories", {})
        scores = {}
        for cat_id, cat_data in categories.items():
            score = cat_data.get("score")
            scores[cat_id] = round(score * 100) if score is not None else None

        avg = sum(s for s in scores.values() if s is not None) / max(len([s for s in scores.values() if s is not None]), 1)
        passed = avg >= 85

        return json.dumps({
            "url": url,
            "scores": scores,
            "average": round(avg, 1),
            "passed": passed,
            "verdict": f"{'PASSED' if passed else 'FAILED'} (avg: {avg:.0f}/100)",
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Lighthouse timed out after 120s"})
    except FileNotFoundError:
        return json.dumps({"error": "npx/lighthouse not available"})
    except json.JSONDecodeError:
        return json.dumps({"error": "Lighthouse output was not valid JSON"})
