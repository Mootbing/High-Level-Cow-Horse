"""BaseAgent class wrapping the Anthropic SDK."""

from __future__ import annotations

import json
import time

import structlog
from anthropic import AsyncAnthropic

from openclaw.config import settings
from openclaw.queue.producer import publish
from openclaw.schemas.agent import AgentMessage


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
        # Each agent instance gets its own bound logger with agent_type
        self.log = structlog.get_logger().bind(agent=self.agent_type)

    async def process_task(self, message: dict) -> dict:
        """Main entry point. Override in subclasses for custom behavior."""
        msg_type = message.get("type", "task")
        payload = message.get("payload", {})

        self.log.info("process_task_start", msg_type=msg_type, payload_keys=list(payload.keys()))

        prompt = payload.get("prompt", json.dumps(payload))
        context = payload.get("context", [])

        t0 = time.monotonic()
        response = await self.run(prompt, context)
        elapsed = round(time.monotonic() - t0, 2)

        self.log.info("process_task_done", elapsed_s=elapsed, response_len=len(response))
        return {"status": "completed", "result": response}

    async def run(self, prompt: str, context: list[dict] | None = None) -> str:
        """Execute a Claude API call with the agent's system prompt and tools."""
        messages = []
        if context:
            messages.extend(context[-self.max_context_messages :])
        messages.append({"role": "user", "content": prompt})

        self.log.info(
            "claude_api_call",
            model=self.model,
            prompt_len=len(prompt),
            context_msgs=len(messages) - 1,
            tool_count=len(self.tools),
        )

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "system": self.system_prompt,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools

        t0 = time.monotonic()
        response = await self.client.messages.create(**kwargs)
        api_elapsed = round(time.monotonic() - t0, 2)

        self.log.info(
            "claude_api_response",
            elapsed_s=api_elapsed,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            content_blocks=len(response.content),
        )

        # Persist the prompt and response to agent_logs DB table
        await self._persist_log("user", prompt, response.usage.input_tokens)

        # Extract text and handle tool calls
        result_parts = []
        for block in response.content:
            if block.type == "text":
                self.log.debug("response_text", text_len=len(block.text), preview=block.text[:200])
                result_parts.append(block.text)
            elif block.type == "tool_use":
                self.log.info(
                    "tool_call",
                    tool=block.name,
                    input_keys=list(block.input.keys()) if isinstance(block.input, dict) else "N/A",
                )
                t1 = time.monotonic()
                tool_result = await self.handle_tool_call(block.name, block.input)
                tool_elapsed = round(time.monotonic() - t1, 2)
                self.log.info(
                    "tool_call_done",
                    tool=block.name,
                    elapsed_s=tool_elapsed,
                    result_status=tool_result.get("status", "unknown") if isinstance(tool_result, dict) else "raw",
                )
                result_parts.append(json.dumps(tool_result))

        full_response = "\n".join(result_parts)
        await self._persist_log("assistant", full_response, response.usage.output_tokens)
        return full_response

    async def _persist_log(self, role: str, content: str, token_count: int | None = None) -> None:
        """Save an agent log entry to the database."""
        try:
            from openclaw.db.session import async_session_factory
            from openclaw.models.agent_log import AgentLog
            async with async_session_factory() as session:
                log = AgentLog(
                    agent_type=self.agent_type,
                    role=role,
                    content=content[:10000],  # Truncate very long content
                    token_count=token_count,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            self.log.warning("persist_log_failed", error=str(e))

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call from Claude. Override in subclasses."""
        self.log.warning("unhandled_tool_call", tool=tool_name)
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
        self.log.info(
            "delegated_task",
            target=target_agent,
            entry_id=entry_id,
            payload_preview=str(payload)[:200],
        )
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
        self.log.info(
            "reported_result",
            target=target_agent,
            entry_id=entry_id,
            result_keys=list(result.keys()),
        )
        return entry_id
