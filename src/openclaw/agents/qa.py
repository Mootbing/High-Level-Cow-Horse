from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.worker import register_agent

logger = structlog.get_logger()

QA_SYSTEM_PROMPT = """You are the QA Engineer of OpenClaw, a digital design agency.

You test generated websites for quality. For each site:
1. Take screenshots at multiple viewports (1440px, 1024px, 768px, 375px)
2. Run Lighthouse audit (performance, accessibility, SEO, best practices)
3. Check scroll animation smoothness
4. Verify responsive behavior
5. Check for broken images/videos

Produce a structured QA report:
- Overall score (0-100)
- Pass/Fail (threshold: 85)
- List of issues found with severity
- Screenshots at each viewport
- Lighthouse scores

If the site passes (>=85), mark as approved.
If it fails, create detailed bug reports for the Engineer to fix.
"""

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


@register_agent("qa")
class QAAgent(BaseAgent):
    agent_type = "qa"
    system_prompt = QA_SYSTEM_PROMPT
    tools = [SCREENSHOT_TOOL, LIGHTHOUSE_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "take_screenshot":
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
                    return {"status": "captured", "path": filepath}
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

        return await super().handle_tool_call(tool_name, tool_input)
