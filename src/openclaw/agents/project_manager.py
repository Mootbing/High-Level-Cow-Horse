from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

PM_SYSTEM_PROMPT = """You are the Project Manager of OpenClaw, an AI-powered digital design agency.

When you receive a project brief, break it down into a task DAG (Directed Acyclic Graph):

Standard website project flow:
1. [designer] Generate hero keyframes — can run in parallel with T2, T3
2. [designer] Generate section keyframes — parallel with T1, T3
3. [designer] Create design spec (colors, fonts, layout) — parallel with T1, T2
4. [designer] Generate hero video using keyframes — depends on T1
5. [engineer] Build Next.js site — depends on T2, T3, T4
6. [qa] Test deployed preview — depends on T5
7. [engineer] Fix QA issues — depends on T6, only if QA fails
8. [client_comms] Send launch notification — depends on T6 passing or T7

For scraping tasks: delegate directly to inbound agent.
For email tasks: delegate directly to outbound agent.

Use the delegate_task tool to assign tasks to agents.
Track progress and escalate blockers to the CEO.
"""

DELEGATE_TOOL = {
    "name": "delegate_task",
    "description": "Delegate a task to a specialized agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {
                "type": "string",
                "enum": ["designer", "engineer", "qa", "client_comms", "inbound", "outbound"],
            },
            "task_description": {"type": "string"},
            "project_name": {"type": "string"},
            "depends_on": {"type": "array", "items": {"type": "string"}, "description": "Task IDs this depends on"},
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
