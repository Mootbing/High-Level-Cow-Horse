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
    max_turns: int = 10  # Safety limit; subclasses can override
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
        """Execute a multi-turn Claude API call, looping until Claude stops requesting tools."""
        messages = []
        if context:
            messages.extend(context[-self.max_context_messages :])
        messages.append({"role": "user", "content": prompt})

        await self._persist_log("user", prompt)

        final_text_parts = []

        for turn in range(self.max_turns):
            self.log.info(
                "claude_api_call",
                model=self.model,
                turn=turn + 1,
                msg_count=len(messages),
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
                turn=turn + 1,
                stop_reason=response.stop_reason,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                content_blocks=len(response.content),
            )

            # Build the assistant message content and handle tool calls
            assistant_content = []
            tool_results = []

            for block in response.content:
                if block.type == "text":
                    self.log.debug("response_text", text_len=len(block.text), preview=block.text[:200])
                    final_text_parts.append(block.text)
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    self.log.info(
                        "tool_call",
                        tool=block.name,
                        turn=turn + 1,
                        input_keys=list(block.input.keys()) if isinstance(block.input, dict) else "N/A",
                    )
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    t1 = time.monotonic()
                    tool_result = await self.handle_tool_call(block.name, block.input)
                    tool_elapsed = round(time.monotonic() - t1, 2)
                    self.log.info(
                        "tool_call_done",
                        tool=block.name,
                        elapsed_s=tool_elapsed,
                        result_status=tool_result.get("status", "unknown") if isinstance(tool_result, dict) else "raw",
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(tool_result),
                    })

            # If Claude is done (end_turn or no tool calls), break
            if response.stop_reason == "end_turn" or not tool_results:
                break

            # Otherwise, add assistant message + tool results and continue
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        full_response = "\n".join(final_text_parts)
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
        import hashlib
        if not task_id:
            dedup_input = f"{self.agent_type}:{target_agent}:{payload.get('prompt', '')[:200]}"
            task_id = hashlib.sha256(dedup_input.encode()).hexdigest()[:16]

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
