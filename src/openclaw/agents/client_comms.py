from __future__ import annotations

import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.worker import register_agent
from openclaw.tools.whatsapp import WHATSAPP_TOOLS, handle_whatsapp_tool

logger = structlog.get_logger()

COMMS_SYSTEM_PROMPT = """You are the Client Communications Agent of OpenClaw.

You send professional project updates to clients and the agency owner via WhatsApp.
Keep messages concise and informative:
- Project milestones (design complete, site deployed, etc.)
- Include preview URLs when available
- Share screenshots of key sections
- Note Lighthouse scores and performance metrics
- Ask for feedback when appropriate

Always be professional, enthusiastic, and concise.
"""


@register_agent("client_comms")
class ClientCommsAgent(BaseAgent):
    agent_type = "client_comms"
    system_prompt = COMMS_SYSTEM_PROMPT
    tools = WHATSAPP_TOOLS

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("whatsapp_send", "whatsapp_send_media"):
            return await handle_whatsapp_tool(tool_name, tool_input)
        return await super().handle_tool_call(tool_name, tool_input)
