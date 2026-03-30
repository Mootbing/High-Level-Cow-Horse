from __future__ import annotations

import asyncio
import hashlib
import json
import re

import redis.asyncio as aioredis
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent
from openclaw.config import settings
from openclaw.queue.streams import stream_name

logger = structlog.get_logger()

# Regex for asset paths the designer uploads to public/assets/
_ASSET_RE = re.compile(r'/assets/[\w\-]+\.(?:mp4|png|jpg|jpeg|webp|svg|gif|webm)')
_FAILED_ASSET_RE = re.compile(r'UPLOAD_FAILED:(/assets/[\w\-]+\.(?:mp4|png|jpg|jpeg|webp|svg|gif|webm))')

# Steps that get a blocking reviewer gate before PM advances.
# QA is itself a quality gate; outbound is fire-and-forget.
_REVIEW_STEPS = {"inbound", "designer", "engineer"}
_MAX_STEP_ATTEMPTS = 2  # 1 original + 1 retry if reviewer fails

PM_SYSTEM_PROMPT = """You are the Project Manager of Clarmi Design Studio, an AI-powered digital design agency.

When you receive a project brief, create a SINGLE comprehensive task for each agent type.
Do NOT split work into per-section or per-component tasks.

CRITICAL RULES:
1. Send ONE task to the engineer with the FULL brief — let the engineer decide how to break it down internally
2. Send ONE task to the designer with ALL design requirements
3. Send ONE task to the outbound for the email draft
4. Never send multiple tasks to the same agent for the same project

PIPELINE SEQUENCE (MUST follow this order — each step depends on the previous):

Step 1: [inbound] Research the prospect's branding (ONE task with full scope)
  - Use delegate_and_wait to get the brand research results BEFORE continuing.

Step 2: [designer] Generate ALL design assets (hero video + section keyframes in ONE task)
  - Include the brand research from Step 1 in the task.
  - Use delegate_and_wait to get the generated asset URLs BEFORE continuing.
  - The designer returns asset paths like /assets/hero-video-xxx.mp4, /assets/keyframe-hero-xxx.png

Step 3: [engineer] Build the ENTIRE site with designer assets embedded
  - Include ALL of this in the engineer task:
    * Brand data (colors, fonts, messaging) from Step 1
    * ASSET URLS from Step 2 — list every /assets/... path the designer returned
    * Full section list (hero, about, menu, features, CTA, footer)
    * Style direction (dark/light theme, accent colors, animation style)
    * Project name for GitHub repo
    * Explicit instruction: "Use the hero video at /assets/hero-video-xxx.mp4 as the Hero section background video"
    * Explicit instruction: "Use keyframe images as section backgrounds"
    * Instruction to call commit_and_deploy when done
    * Instruction to verify the build passes before deploying
  - Use delegate_and_wait to get the deploy URL BEFORE continuing.

Step 4: [qa] Verify the deployed site loads correctly
  - Include the Vercel URL from Step 3 in the QA task.
  - Include the asset URLs from Step 2 so QA can verify they load.
  - Tell QA: "First verify_url to confirm the site is live, then verify_assets to check all designer assets load, then take screenshots and run Lighthouse."
  - Use delegate_and_wait to get the QA report.

Step 5: [outbound] Draft outreach email — ONLY if QA passed
  - HARD GATE: Only proceed to this step if QA returned APPROVED (score >= 85, deployment READY, HTTP 200).
  - If the QA result contains ANY of: "fail", "FAIL", "401", "protection", "error" — STOP HERE. Do NOT delegate to outbound.
  - Include the live URL from Step 3 and QA pass/fail from Step 4.
  - Use delegate_task (fire-and-forget) for this last step.

IMPORTANT: Use delegate_and_wait (NOT delegate_task) for Steps 1-4 so you receive results
before proceeding to the next step. This ensures the designer's assets are available for
the engineer, and the engineer's URL is available for QA.

IMPORTANT: Each step is automatically reviewed before you advance. If the reviewer rejects
a step, the agent retries once with the reviewer's feedback. You do NOT need to handle
reviewer logic yourself — just call delegate_and_wait and it handles review + retry.

IMPORTANT: If QA reports a FAIL, a 401, or any deployment protection issue, do NOT proceed to
the outbound step. The pipeline must stop here. Report the failure and end your task.

IMPORTANT: If a step returns "timeout", do NOT restart the whole pipeline. Report the timeout
and stop. The timed-out agent may still be running — re-delegating would cause duplicate work.
Never re-delegate to an agent that already received a task for this project.

For scraping tasks: delegate directly to inbound agent.
For email tasks: delegate directly to outbound agent.
"""

DELEGATE_TOOL = {
    "name": "delegate_task",
    "description": "Fire-and-forget: delegate a task to an agent without waiting for results. Use for the final step (outbound) only.",
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {
                "type": "string",
                "enum": ["designer", "engineer", "qa", "client_comms", "inbound", "outbound"],
            },
            "task_description": {
                "type": "string",
                "description": "The FULL task description.",
            },
            "project_name": {"type": "string"},
        },
        "required": ["target_agent", "task_description"],
    },
}

DELEGATE_AND_WAIT_TOOL = {
    "name": "delegate_and_wait",
    "description": (
        "Delegate a task to an agent AND wait for the result before continuing. "
        "Use this for sequential pipeline steps where the next step depends on this result. "
        "Returns the agent's full result text. Timeout: 15 minutes. "
        "Steps 1-3 (inbound, designer, engineer) are automatically reviewed before "
        "returning — if review fails, the step retries once with feedback."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {
                "type": "string",
                "enum": ["designer", "engineer", "qa", "client_comms", "inbound", "outbound"],
            },
            "task_description": {
                "type": "string",
                "description": "The FULL task description. For engineer: include all sections, brand data, style direction, AND asset URLs.",
            },
            "project_name": {"type": "string"},
        },
        "required": ["target_agent", "task_description", "project_name"],
    },
}


@register_agent("project_manager")
class ProjectManagerAgent(BaseAgent):
    agent_type = "project_manager"
    system_prompt = PM_SYSTEM_PROMPT
    max_turns = 30  # PM needs more turns for the sequential pipeline
    tools = [DELEGATE_TOOL, DELEGATE_AND_WAIT_TOOL]

    async def process_task(self, message: dict) -> dict:
        # Capture project_id from the incoming message so we can forward it
        self._current_project_id = message.get("project_id")
        payload = message.get("payload", {})
        if not self._current_project_id:
            self._current_project_id = payload.get("project_id")
        self._designer_assets: list[str] = []  # Populated when designer result arrives
        return await super().process_task(message)

    @staticmethod
    def _format_asset_block(assets: list[str]) -> str:
        """Build a deterministic asset injection block for the engineer task."""
        block = "\n\n=== DESIGNER ASSETS — MANDATORY, EMBED ALL IN THE SITE ===\n"
        for url in assets:
            if url.endswith((".mp4", ".webm")):
                block += (
                    f"- HERO VIDEO: {url}\n"
                    f'  Embed: <video autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover">'
                    f'<source src="{url}" type="video/mp4" /></video>\n'
                )
            else:
                block += (
                    f"- SECTION IMAGE: {url}\n"
                    f"  Embed as: <img src=\"{url}\" /> or background-image: url({url})\n"
                )
        block += "=== END DESIGNER ASSETS ===\n"
        return block

    # ------------------------------------------------------------------
    # Helpers: polling and reviewer gate
    # ------------------------------------------------------------------

    async def _poll_for_result(
        self,
        r: aioredis.Redis,
        pm_stream: str,
        source_agent: str,
        task_id: str,
        timeout_s: int = 900,
    ) -> str | None:
        """Poll PM stream for a result from *source_agent* with matching *task_id*.

        Returns the full result text, or None on timeout.
        """
        poll_interval_s = 5
        elapsed = 0

        while elapsed < timeout_s:
            entries = await r.xrevrange(pm_stream, count=50)

            for _entry_id, fields in entries:
                try:
                    data = json.loads(fields.get("data", "{}"))
                except (json.JSONDecodeError, TypeError):
                    continue

                if (
                    data.get("type") == "result"
                    and data.get("source_agent") == source_agent
                    and data.get("task_id") == task_id
                ):
                    result_payload = data.get("payload", {})
                    result_text = result_payload.get("result", str(result_payload))

                    # Fetch full (untruncated) result from DB if available
                    _db_task_id = result_payload.get("db_task_id")
                    if _db_task_id:
                        try:
                            from openclaw.db.session import async_session_factory
                            from openclaw.services.task_service import get_task

                            async with async_session_factory() as _s:
                                _task = await get_task(_s, _db_task_id)
                                if _task and _task.output_data:
                                    _full = _task.output_data.get("result", "")
                                    if _full and len(_full) > len(result_text):
                                        result_text = _full
                                        self.log.info(
                                            "full_result_from_db",
                                            db_task_id=_db_task_id,
                                            len=len(result_text),
                                        )
                        except Exception:
                            pass  # Fall back to stream version

                    # Set dedup key so the worker loop skips this result
                    dedup_key = f"openclaw:dedup:project_manager:{task_id}"
                    await r.set(dedup_key, "1", ex=3600)

                    self.log.info(
                        "poll_result_received",
                        source=source_agent,
                        task_id=task_id,
                        elapsed_s=elapsed,
                        result_len=len(result_text),
                    )
                    return result_text

            await asyncio.sleep(poll_interval_s)
            elapsed += poll_interval_s

            if elapsed % 60 == 0:
                self.log.info(
                    "poll_waiting",
                    source=source_agent,
                    task_id=task_id,
                    elapsed_s=elapsed,
                )

        self.log.warning(
            "poll_timeout",
            source=source_agent,
            task_id=task_id,
            timeout_s=timeout_s,
        )
        return None

    async def _request_review(
        self,
        r: aioredis.Redis,
        pm_stream: str,
        reviewed_agent: str,
        result_text: str,
        original_task_id: str,
    ) -> tuple[bool, str]:
        """Send result to reviewer and block until verdict.

        Returns (passed: bool, review_text: str).
        On reviewer timeout, returns (True, ...) so the pipeline isn't blocked.
        """
        review_task_id = hashlib.sha256(
            f"pm_review:{reviewed_agent}:{original_task_id}".encode()
        ).hexdigest()[:16]

        review_prompt = (
            f"Review the output of the {reviewed_agent} agent.\n\n"
            f"Result:\n{result_text[:3000]}\n\n"
            f"Verify this step completed correctly. "
            f"Use verify_url or verify_file tools if needed."
        )

        await self.delegate(
            target_agent="reviewer",
            payload={
                "prompt": review_prompt,
                "source": reviewed_agent,
            },
            project_id=getattr(self, "_current_project_id", None),
            task_id=review_task_id,
        )
        self.log.info(
            "review_requested",
            reviewed_agent=reviewed_agent,
            review_task_id=review_task_id,
        )

        # Wait for reviewer (shorter timeout — should be fast)
        review_text = await self._poll_for_result(
            r, pm_stream, "reviewer", review_task_id, timeout_s=300
        )

        if review_text is None:
            self.log.warning("review_timeout", reviewed_agent=reviewed_agent)
            return True, "Review timed out — proceeding"

        # Parse structured verdict (reviewer prepends "VERDICT:pass" or "VERDICT:fail")
        if review_text.startswith("VERDICT:fail"):
            return False, review_text
        if review_text.startswith("VERDICT:pass"):
            return True, review_text

        # Fallback: keyword detection in text
        lower = review_text.lower()
        if "failed" in lower and "passed" not in lower[-300:]:
            return False, review_text
        return True, review_text

    def _extract_post_result(self, target: str, result_text: str) -> None:
        """Extract assets / evaluate QA gate from an agent's result."""
        # Extract designer asset URLs deterministically
        if target == "designer":
            all_paths = _ASSET_RE.findall(result_text)
            failed = set(_FAILED_ASSET_RE.findall(result_text))
            self._designer_assets = list(
                dict.fromkeys(p for p in all_paths if p not in failed)
            )
            self.log.info(
                "designer_assets_extracted",
                count=len(self._designer_assets),
                urls=self._designer_assets,
            )

        # Track QA pass/fail for hard gate
        if target == "qa":
            result_lower = result_text.lower()
            qa_failed = any(
                kw in result_lower
                for kw in [
                    "fail", "401", "protection_enabled",
                    "protection_unresolved", "error", "not approved",
                ]
            )
            self._qa_passed = not qa_failed
            self.log.info("qa_gate_evaluated", qa_passed=self._qa_passed)

    # ------------------------------------------------------------------
    # Tool handlers
    # ------------------------------------------------------------------

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "delegate_task":
            return await self._handle_delegate_task(tool_input)
        elif tool_name == "delegate_and_wait":
            return await self._handle_delegate_and_wait(tool_input)
        return await super().handle_tool_call(tool_name, tool_input)

    async def _handle_delegate_task(self, tool_input: dict) -> dict:
        """Fire-and-forget delegation (outbound only)."""
        target = tool_input["target_agent"]

        # HARD GATE: block outbound if QA has not passed
        if target == "outbound":
            qa_passed = getattr(self, "_qa_passed", None)
            if qa_passed is not True:
                self.log.warning("outbound_blocked_qa_not_passed", qa_passed=qa_passed)
                return {
                    "status": "blocked",
                    "reason": "Cannot send outreach: QA has not passed. Pipeline stops here.",
                }

        task_desc = tool_input["task_description"]
        if target == "engineer" and self._designer_assets:
            task_desc += self._format_asset_block(self._designer_assets)

        # Generate task_id and pre-set dedup key so the auto-reported
        # result doesn't get re-processed by PM worker after pipeline ends.
        task_id = hashlib.sha256(
            f"pm_fire:{target}:{tool_input['task_description'][:100]}".encode()
        ).hexdigest()[:16]

        await self.delegate(
            target_agent=target,
            payload={
                "prompt": task_desc,
                "project_name": tool_input.get("project_name", ""),
                "source": "project_manager",
            },
            project_id=getattr(self, "_current_project_id", None),
            task_id=task_id,
        )

        # Pre-set dedup so the auto-reported result is skipped by PM worker
        try:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.set(f"openclaw:dedup:project_manager:{task_id}", "1", ex=3600)
            await r.aclose()
        except Exception:
            pass

        return {"status": "delegated", "to": target}

    async def _handle_delegate_and_wait(self, tool_input: dict) -> dict:
        """Delegate, wait for result, run reviewer gate, retry once on fail."""
        target = tool_input["target_agent"]
        project_name = tool_input.get("project_name", "")

        task_desc_original = tool_input["task_description"]

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pm_stream = stream_name("project_manager")

        max_attempts = _MAX_STEP_ATTEMPTS if target in _REVIEW_STEPS else 1

        try:
            for attempt in range(max_attempts):
                # Build task description (may include reviewer feedback on retry)
                if attempt == 0:
                    task_desc = task_desc_original
                # else: task_desc was updated at end of previous iteration

                if target == "engineer" and self._designer_assets:
                    task_desc_with_assets = task_desc + self._format_asset_block(self._designer_assets)
                else:
                    task_desc_with_assets = task_desc

                # Unique task_id per attempt (so retries aren't dedup'd)
                task_id = hashlib.sha256(
                    f"pm_wait:{target}:{project_name}:{task_desc[:100]}:{attempt}".encode()
                ).hexdigest()[:16]

                # Delegate to target agent
                await self.delegate(
                    target_agent=target,
                    payload={
                        "prompt": task_desc_with_assets,
                        "project_name": project_name,
                        "source": "project_manager",
                    },
                    project_id=getattr(self, "_current_project_id", None),
                    task_id=task_id,
                )
                self.log.info(
                    "delegate_and_wait_sent",
                    target=target,
                    task_id=task_id,
                    attempt=attempt + 1,
                )

                # Wait for agent result (heavy agents like engineer need longer)
                from openclaw.queue.streams import HEAVY_AGENTS
                poll_timeout = settings.HEAVY_TASK_TIMEOUT_S + 120 if target in HEAVY_AGENTS else 900
                result_text = await self._poll_for_result(
                    r, pm_stream, target, task_id, timeout_s=poll_timeout
                )
                if result_text is None:
                    return {
                        "status": "timeout",
                        "from": target,
                        "task_id": task_id,
                        "message": f"{target} did not return a result within 900s.",
                    }

                # Extract assets / evaluate QA gate
                self._extract_post_result(target, result_text)

                # Reviewer gate (skip for QA — it IS the quality gate)
                if target in _REVIEW_STEPS:
                    passed, review_text = await self._request_review(
                        r, pm_stream, target, result_text, task_id
                    )
                    if passed:
                        self.log.info(
                            "review_passed",
                            target=target,
                            attempt=attempt + 1,
                        )
                        return {
                            "status": "completed",
                            "from": target,
                            "task_id": task_id,
                            "result": result_text,
                        }
                    else:
                        self.log.warning(
                            "review_failed",
                            target=target,
                            attempt=attempt + 1,
                            review_preview=review_text[:200],
                        )
                        if attempt < max_attempts - 1:
                            # Retry: append reviewer feedback to the original task
                            task_desc = (
                                f"{task_desc_original}\n\n"
                                f"=== PREVIOUS ATTEMPT FAILED REVIEW ===\n"
                                f"{review_text[:1500]}\n"
                                f"=== FIX THE ISSUES ABOVE AND TRY AGAIN ==="
                            )
                            continue
                        # All retries exhausted
                        return {
                            "status": "review_failed",
                            "from": target,
                            "task_id": task_id,
                            "result": result_text,
                            "review": review_text[:2000],
                            "message": f"{target} failed review after {max_attempts} attempts.",
                        }
                else:
                    # No reviewer gate for this step (e.g., QA)
                    return {
                        "status": "completed",
                        "from": target,
                        "task_id": task_id,
                        "result": result_text,
                    }

        finally:
            await r.aclose()

        # Should not reach here
        return {"status": "error", "from": target, "message": "Unexpected loop exit"}
