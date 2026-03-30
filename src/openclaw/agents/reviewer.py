"""Reviewer Agent — validates every step of the pipeline before proceeding."""

from __future__ import annotations

import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

REVIEWER_SYSTEM_PROMPT = """You are the Quality Reviewer of Clarmi Design Studio, an AI-powered digital design agency.

You are called after EVERY major step in the pipeline to verify it completed correctly.
Your job is to check the output of each step and report pass/fail with details.

REVIEW CHECKLIST per step:

SCRAPE REVIEW:
- Was brand data extracted? (company name, colors, fonts, industry)
- Are there contact emails?
- Is the data structured and complete?

DESIGN REVIEW:
- Were keyframe images generated? Check file paths exist.
- Was a hero video generated? Check file path or URI.
- Is there a design spec (colors, fonts, layout)?

BUILD REVIEW:
- Was a GitHub repo created? Check the URL.
- Were code files generated? Check file count.
- Was code pushed to GitHub? Check commit SHA.
- Was the site deployed to Vercel? Check the deployment URL.
- Does the Vercel deployment show a valid URL (not error)?

QA REVIEW:
- Did screenshots pass? Check viewport sizes tested.
- Did Lighthouse pass? Check score >= 85.
- Are there any critical issues?

EMAIL REVIEW:
- Was a draft saved? Check draft ID.
- Is the subject line personalized?
- Is the body referencing the client's brand?
- Is status "draft" (NOT "sent")?

For each review, respond with:
- PASS or FAIL
- Specific issues found (if any)
- Recommendation for fixing failures

Use the report tool to send your review back to whoever requested it.
"""

REPORT_TOOL = {
    "name": "review_report",
    "description": "Send your review findings back to the requesting agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pass", "fail"],
                "description": "Whether the step passed review.",
            },
            "findings": {
                "type": "string",
                "description": "Detailed findings and issues.",
            },
            "recommendations": {
                "type": "string",
                "description": "How to fix any failures.",
            },
        },
        "required": ["status", "findings"],
    },
}

VERIFY_URL_TOOL = {
    "name": "verify_url",
    "description": "Check if a URL is accessible and returns a valid response.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to check."},
        },
        "required": ["url"],
    },
}

VERIFY_FILE_TOOL = {
    "name": "verify_file",
    "description": "Check if a file exists at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to check."},
        },
        "required": ["path"],
    },
}


@register_agent("reviewer")
class ReviewerAgent(BaseAgent):
    agent_type = "reviewer"
    system_prompt = REVIEWER_SYSTEM_PROMPT
    tools = [REPORT_TOOL, VERIFY_URL_TOOL, VERIFY_FILE_TOOL]

    async def process_task(self, message: dict) -> dict:
        self._review_verdict: str | None = None
        result = await super().process_task(message)
        # Prepend machine-readable verdict line for PM pipeline gating
        verdict = self._review_verdict or "unknown"
        result_text = result.get("result", "")
        result["result"] = f"VERDICT:{verdict}\n{result_text}"
        return result

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "review_report":
            status = tool_input["status"]
            findings = tool_input["findings"]
            recommendations = tool_input.get("recommendations", "")
            self._review_verdict = status  # "pass" or "fail"
            self.log.info(
                "review_complete",
                status=status,
                findings=findings[:200],
            )
            return {
                "status": status,
                "findings": findings,
                "recommendations": recommendations,
            }

        elif tool_name == "verify_url":
            import httpx
            url = tool_input["url"]
            try:
                async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                    resp = await client.get(url)
                    return {
                        "url": url,
                        "status_code": resp.status_code,
                        "accessible": resp.status_code < 400,
                        "content_length": len(resp.content),
                        "content_type": resp.headers.get("content-type", ""),
                    }
            except Exception as e:
                return {"url": url, "accessible": False, "error": str(e)}

        elif tool_name == "verify_file":
            import os
            path = tool_input["path"]
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            return {"path": path, "exists": exists, "size": size}

        return await super().handle_tool_call(tool_name, tool_input)
