from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

RESEARCH_SYSTEM_PROMPT = """You are the Research Agent of OpenClaw, a digital design agency.

You autonomously research the latest web design trends, animation techniques, and tools.
Every 6 hours you scan:
1. Awwwards (awwwards.com) for award-winning websites
2. Dribbble for trending web design shots
3. CSS-Tricks and Codrops for new animation tutorials
4. npm for trending animation/scroll packages

For each finding, extract:
- What's new or trending
- Code snippets or techniques
- How it can be applied to our websites
- Relevance score (how useful is this for our agency)

Store findings in the knowledge base with proper categorization.
Send a weekly digest to the owner via WhatsApp.
"""

SCRAPE_TOOL = {
    "name": "research_scrape",
    "description": "Scrape a website for design research.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "focus": {"type": "string", "description": "What to look for (trends, techniques, tools, etc.)"},
        },
        "required": ["url"],
    },
}

STORE_KNOWLEDGE_TOOL = {
    "name": "store_knowledge",
    "description": "Store a research finding in the knowledge base.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["trend", "technique", "component", "tool", "inspiration"]},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "source_url": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "code_snippet": {"type": "string"},
            "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["category", "title", "content"],
    },
}


@register_agent("research")
class ResearchAgent(BaseAgent):
    agent_type = "research"
    system_prompt = RESEARCH_SYSTEM_PROMPT
    tools = [SCRAPE_TOOL, STORE_KNOWLEDGE_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "research_scrape":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            result = await firecrawl_client.scrape(tool_input["url"])
            return result

        elif tool_name == "store_knowledge":
            from openclaw.db.session import async_session_factory
            from openclaw.models.knowledge import KnowledgeBase
            async with async_session_factory() as session:
                entry = KnowledgeBase(
                    category=tool_input["category"],
                    title=tool_input["title"],
                    content=tool_input["content"],
                    source_url=tool_input.get("source_url"),
                    source_type=tool_input.get("source_type", "research"),
                    relevance_score=tool_input.get("relevance_score", 0.8),
                    tags=tool_input.get("tags", []),
                    code_snippet=tool_input.get("code_snippet"),
                )
                session.add(entry)
                await session.commit()
                return {"status": "stored", "title": tool_input["title"]}

        return await super().handle_tool_call(tool_name, tool_input)
