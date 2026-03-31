"""BaseSkill class — the foundation for all OpenClaw skills.

Replaces the monolithic BaseAgent with a skill-oriented architecture.
Skills are discovered dynamically from the skills/ directory and executed
by the SkillRunner.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog
from anthropic import AsyncAnthropic

from openclaw.config import settings
from openclaw.queue.producer import publish
from openclaw.schemas.agent import AgentMessage


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class SkillContext:
    """Immutable bag of data passed to a skill when it executes.

    Attributes:
        project_id:   The project this task belongs to (may be ``None`` for
                       system-level tasks like research or learning).
        task_id:       A caller-supplied dedup / correlation ID.
        payload:       Arbitrary key-value data from the upstream skill or API.
        source_skill:  Name of the skill that delegated this task.
        message:       The full raw Redis Streams message dict, preserved so
                       skills can inspect any field the framework doesn't unpack.
    """

    project_id: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    source_skill: str | None = None
    message: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """Return value from :py:meth:`BaseSkill.execute`.

    Attributes:
        success:  ``True`` when the skill completed without errors.
        result:   A human-readable summary / the main output string.
        data:     Structured data the runner or downstream skills can use.
        error:    Error description when ``success`` is ``False``.
    """

    success: bool = True
    result: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


# ---------------------------------------------------------------------------
# BaseSkill
# ---------------------------------------------------------------------------

class BaseSkill(ABC):
    """Abstract base class every skill must subclass.

    Class-level attributes act as defaults; concrete skills override them
    either directly on the class body or via ``skill.yaml`` metadata that
    the :py:class:`~openclaw.runtime.skill_loader.SkillLoader` applies.

    Unlike the old ``BaseAgent``, the Claude client is **injected** by the
    runner rather than created internally.  This keeps skills testable and
    allows the runner to share a single ``AsyncAnthropic`` instance across
    all skills.
    """

    # -- Metadata (overridden in subclasses or loaded from skill.yaml) ------
    name: str = "base"
    description: str = ""
    tier: str = "light"  # "light" or "heavy"
    system_prompt: str = "You are a helpful assistant."
    model: str = ""
    max_context_messages: int = 50
    max_turns: int = 10
    tools: list[dict] = []
    timeout: int = 600  # seconds; runner uses this as asyncio.wait_for limit

    # -- Instance state (set in __init__) -----------------------------------

    def __init__(self, claude_client: AsyncAnthropic) -> None:
        self.client = claude_client
        self.model = self.model or settings.CLAUDE_MODEL
        self._current_project_id: str | None = None
        self.log = structlog.get_logger().bind(skill=self.name)

    # -- Public entry point -------------------------------------------------

    async def execute(self, context: SkillContext) -> SkillResult:
        """Main entry point invoked by the runner.

        The default implementation extracts ``prompt`` and ``context`` from
        ``context.payload``, calls :py:meth:`run`, and wraps the output in
        a :py:class:`SkillResult`.  Override in subclasses for radically
        different workflows.
        """
        if not self._current_project_id:
            self._current_project_id = context.project_id
        payload = context.payload

        self.log.info(
            "execute_start",
            project_id=context.project_id,
            task_id=context.task_id,
            payload_keys=list(payload.keys()),
        )

        prompt = payload.get("prompt", json.dumps(payload))
        conv_context: list[dict] = payload.get("context", [])

        t0 = time.monotonic()
        try:
            response = await self.run(prompt, conv_context)
        except Exception as exc:
            elapsed = round(time.monotonic() - t0, 2)
            self.log.error("execute_failed", elapsed_s=elapsed, error=str(exc))
            return SkillResult(success=False, error=str(exc))

        elapsed = round(time.monotonic() - t0, 2)
        self.log.info("execute_done", elapsed_s=elapsed, response_len=len(response))
        return SkillResult(success=True, result=response)

    # -- Multi-turn Claude loop ---------------------------------------------

    async def run(self, prompt: str, context: list[dict] | None = None) -> str:
        """Execute a multi-turn Claude API call, looping until Claude stops
        requesting tools.

        This is intentionally identical in behaviour to ``BaseAgent.run()``
        so that existing agent logic ports over without changes.
        """
        messages: list[dict] = []
        if context:
            messages.extend(context[-self.max_context_messages:])
        messages.append({"role": "user", "content": prompt})

        await self._persist_log("user", prompt)

        final_text_parts: list[str] = []

        for turn in range(self.max_turns):
            self.log.info(
                "claude_api_call",
                model=self.model,
                turn=turn + 1,
                msg_count=len(messages),
                tool_count=len(self.tools),
            )

            kwargs: dict[str, Any] = {
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
            assistant_content: list[dict] = []
            tool_results: list[dict] = []

            for block in response.content:
                if block.type == "text":
                    self.log.debug(
                        "response_text",
                        text_len=len(block.text),
                        preview=block.text[:200],
                    )
                    final_text_parts.append(block.text)
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    self.log.info(
                        "tool_call",
                        tool=block.name,
                        turn=turn + 1,
                        input_keys=(
                            list(block.input.keys())
                            if isinstance(block.input, dict)
                            else "N/A"
                        ),
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
                        result_status=(
                            tool_result.get("status", "unknown")
                            if isinstance(tool_result, dict)
                            else "raw"
                        ),
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
        else:
            # for-loop completed without break -- hit max_turns limit
            self.log.warning(
                "max_turns_reached",
                max_turns=self.max_turns,
                text_parts=len(final_text_parts),
            )

        full_response = "\n".join(final_text_parts)
        await self._persist_log("assistant", full_response, response.usage.output_tokens)
        return full_response

    # -- Tool handling (override in subclasses) -----------------------------

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call from Claude.  Override in subclasses."""
        self.log.warning("unhandled_tool_call", tool=tool_name)
        return {"error": f"Tool {tool_name} not implemented"}

    # -- Inter-skill delegation (publishes to Redis Streams) ----------------

    async def delegate(
        self,
        target_skill: str,
        payload: dict,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        """Delegate a task to another skill via Redis Streams."""
        if not task_id:
            dedup_input = f"{self.name}:{target_skill}:{payload.get('prompt', '')[:200]}"
            task_id = hashlib.sha256(dedup_input.encode()).hexdigest()[:16]

        message = AgentMessage(
            type="task",
            source_agent=self.name,
            target_agent=target_skill,
            project_id=project_id,
            task_id=task_id,
            payload=payload,
        )
        entry_id = await publish(target_skill, message.to_publish_dict())
        self.log.info(
            "delegated_task",
            target=target_skill,
            entry_id=entry_id,
            payload_preview=str(payload)[:200],
        )
        return entry_id

    async def report(
        self,
        target_skill: str,
        result: dict,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        """Send a result back to the delegating skill."""
        message = AgentMessage(
            type="result",
            source_agent=self.name,
            target_agent=target_skill,
            project_id=project_id,
            task_id=task_id,
            payload=result,
        )
        entry_id = await publish(target_skill, message.to_publish_dict())
        self.log.info(
            "reported_result",
            target=target_skill,
            entry_id=entry_id,
            result_keys=list(result.keys()),
        )
        return entry_id

    # -- Persistence --------------------------------------------------------

    async def _persist_log(
        self, role: str, content: str, token_count: int | None = None
    ) -> None:
        """Save a skill log entry to the database."""
        try:
            from openclaw.db.session import async_session_factory
            from openclaw.models.agent_log import AgentLog

            async with async_session_factory() as session:
                log = AgentLog(
                    agent_type=self.name,
                    project_id=getattr(self, "_current_project_id", None),
                    role=role,
                    content=content[:10_000],  # Truncate very long content
                    token_count=token_count,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            self.log.warning("persist_log_failed", error=str(e))
