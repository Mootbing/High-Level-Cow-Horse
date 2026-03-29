from __future__ import annotations

import asyncio
import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

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

Step 5: [outbound] Draft outreach email
  - Include the live URL from Step 3 and QA pass/fail from Step 4.
  - Use delegate_task (fire-and-forget) for this last step.

IMPORTANT: Use delegate_and_wait (NOT delegate_task) for Steps 1-4 so you receive results
before proceeding to the next step. This ensures the designer's assets are available for
the engineer, and the engineer's URL is available for QA.

IMPORTANT: If QA reports a 401 or deployment protection issue, that is an INFRASTRUCTURE issue,
not a code issue. Do NOT re-delegate to the engineer to "fix" it. Just note it in the report
and proceed to the outbound step. Never send the engineer a second task for the same project.

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
        "Returns the agent's full result text. Timeout: 15 minutes."
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

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "delegate_task":
            target = tool_input["target_agent"]
            await self.delegate(
                target_agent=target,
                payload={
                    "prompt": tool_input["task_description"],
                    "project_name": tool_input.get("project_name", ""),
                    "source": "project_manager",
                },
            )
            return {"status": "delegated", "to": target}

        elif tool_name == "delegate_and_wait":
            target = tool_input["target_agent"]
            project_name = tool_input.get("project_name", "")

            # Generate a unique task_id so we can match the result
            import hashlib
            task_id = hashlib.sha256(
                f"pm_wait:{target}:{project_name}:{tool_input['task_description'][:100]}".encode()
            ).hexdigest()[:16]

            # Delegate the task
            await self.delegate(
                target_agent=target,
                payload={
                    "prompt": tool_input["task_description"],
                    "project_name": project_name,
                    "source": "project_manager",
                },
                task_id=task_id,
            )
            self.log.info("delegate_and_wait_sent", target=target, task_id=task_id)

            # Poll our own stream for the result message from the target agent
            import redis.asyncio as redis
            from openclaw.config import settings
            from openclaw.queue.streams import stream_name

            r = redis.from_url(settings.REDIS_URL, decode_responses=True)
            pm_stream = stream_name("project_manager")
            timeout_s = 900  # 15 minutes
            poll_interval_s = 5
            elapsed = 0

            try:
                while elapsed < timeout_s:
                    # Read new messages from the PM stream (direct read, not consumer group)
                    # Use XREVRANGE to check recent messages for our result
                    entries = await r.xrevrange(pm_stream, count=50)

                    for entry_id, fields in entries:
                        try:
                            data = json.loads(fields.get("data", "{}"))
                        except (json.JSONDecodeError, TypeError):
                            continue

                        # Match: result from the target agent for our task
                        if (
                            data.get("type") == "result"
                            and data.get("source_agent") == target
                            and data.get("task_id") == task_id
                        ):
                            result_payload = data.get("payload", {})
                            result_text = result_payload.get("result", str(result_payload))
                            self.log.info(
                                "delegate_and_wait_received",
                                target=target,
                                task_id=task_id,
                                elapsed_s=elapsed,
                                result_len=len(result_text),
                            )
                            return {
                                "status": "completed",
                                "from": target,
                                "task_id": task_id,
                                "result": result_text,
                            }

                    await asyncio.sleep(poll_interval_s)
                    elapsed += poll_interval_s

                    if elapsed % 60 == 0:
                        self.log.info(
                            "delegate_and_wait_polling",
                            target=target,
                            task_id=task_id,
                            elapsed_s=elapsed,
                        )
            finally:
                await r.aclose()

            # Timeout
            self.log.warning(
                "delegate_and_wait_timeout",
                target=target,
                task_id=task_id,
                timeout_s=timeout_s,
            )
            return {
                "status": "timeout",
                "from": target,
                "task_id": task_id,
                "message": f"{target} did not return a result within {timeout_s}s. The task may still be running.",
            }

        return await super().handle_tool_call(tool_name, tool_input)
