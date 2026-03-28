"""BaseAgent class wrapping the Anthropic SDK."""

from __future__ import annotations

import json

import structlog
from anthropic import AsyncAnthropic

from openclaw.config import settings
from openclaw.queue.producer import publish
from openclaw.schemas.agent import AgentMessage

logger = structlog.get_logger()


class BaseAgent:
    """Base class for all OpenClaw agents."""

    agent_type: str = "base"
    system_prompt: str = "You are a helpful assistant."
    model: str = ""
    max_context_messages: int = 50
    tools: list[dict] = []

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = self.model or settings.CLAUDE_MODEL

    async def process_task(self, message: dict) -> dict:
        """Main entry point. Override in subclasses for custom behavior."""
        msg_type = message.get("type", "task")
        payload = message.get("payload", {})

        prompt = payload.get("prompt", json.dumps(payload))
        context = payload.get("context", [])

        response = await self.run(prompt, context)
        return {"status": "completed", "result": response}

    async def run(self, prompt: str, context: list[dict] | None = None) -> str:
        """Execute a Claude API call with the agent's system prompt and tools."""
        messages = []
        if context:
            messages.extend(context[-self.max_context_messages :])
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "system": self.system_prompt,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools

        response = await self.client.messages.create(**kwargs)

        # Extract text from response
        result_parts = []
        for block in response.content:
            if block.type == "text":
                result_parts.append(block.text)
            elif block.type == "tool_use":
                tool_result = await self.handle_tool_call(block.name, block.input)
                result_parts.append(json.dumps(tool_result))

        return "\n".join(result_parts)

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call from Claude. Override in subclasses."""
        logger.warning("unhandled_tool_call", tool=tool_name, agent=self.agent_type)
        return {"error": f"Tool {tool_name} not implemented"}

    async def delegate(
        self,
        target_agent: str,
        payload: dict,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        """Delegate a task to another agent via Redis Streams."""
        message = AgentMessage(
            type="task",
            source_agent=self.agent_type,
            target_agent=target_agent,
            project_id=project_id,
            task_id=task_id,
            payload=payload,
        )
        entry_id = await publish(target_agent, message.to_publish_dict())
        logger.info("delegated_task", target=target_agent, entry_id=entry_id)
        return entry_id

    async def report(
        self,
        target_agent: str,
        result: dict,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        """Send a result back to the delegating agent."""
        message = AgentMessage(
            type="result",
            source_agent=self.agent_type,
            target_agent=target_agent,
            project_id=project_id,
            task_id=task_id,
            payload=result,
        )
        entry_id = await publish(target_agent, message.to_publish_dict())
        return entry_id
