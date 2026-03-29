from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

PM_SYSTEM_PROMPT = """You are the Project Manager of OpenClaw, an AI-powered digital design agency.

When you receive a project brief, create a SINGLE comprehensive task for each agent type.
Do NOT split work into per-section or per-component tasks.

CRITICAL RULES:
1. Send ONE task to the engineer with the FULL brief — let the engineer decide how to break it down internally
2. Send ONE task to the designer with ALL design requirements
3. Send ONE task to the outbound for the email draft
4. Never send multiple tasks to the same agent for the same project

Standard website project flow:
1. [inbound] Research the prospect's branding (ONE task with full scope)
2. [designer] Generate ALL design assets (keyframes + video in ONE task)
3. [engineer] Build the ENTIRE site, push to GitHub, deploy to Vercel (ONE task with full brief including brand data, section list, style direction)
4. [qa] Test the deployed site (ONE task after engineer reports back)
5. [outbound] Draft outreach email (ONE task)

When delegating to the engineer, include ALL of this in a single task:
- Brand data (colors, fonts, messaging) from inbound research
- Full section list (hero, about, menu, features, CTA, footer)
- Style direction (dark/light theme, accent colors, animation style)
- Project name for GitHub repo
- Instruction to call commit_and_deploy when done
- Instruction to verify the build passes before deploying

For scraping tasks: delegate directly to inbound agent.
For email tasks: delegate directly to outbound agent.

Use the delegate_task tool to assign tasks to agents.
"""

DELEGATE_TOOL = {
    "name": "delegate_task",
    "description": "Delegate a task to a specialized agent. Send ONE comprehensive task per agent — do not split into sub-tasks.",
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {
                "type": "string",
                "enum": ["designer", "engineer", "qa", "client_comms", "inbound", "outbound"],
            },
            "task_description": {
                "type": "string",
                "description": "The FULL task description. For engineer: include all sections, brand data, and style direction in one message.",
            },
            "project_name": {"type": "string"},
        },
        "required": ["target_agent", "task_description"],
    },
}


@register_agent("project_manager")
class ProjectManagerAgent(BaseAgent):
    agent_type = "project_manager"
    system_prompt = PM_SYSTEM_PROMPT
    tools = [DELEGATE_TOOL]

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
        return await super().handle_tool_call(tool_name, tool_input)
