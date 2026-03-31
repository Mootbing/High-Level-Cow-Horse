"""Research tools — store knowledge entries."""

import json

from openclaw.mcp_server.server import mcp


@mcp.tool()
async def store_knowledge(
    category: str,
    title: str,
    content: str,
    source_url: str | None = None,
    tags: list[str] | None = None,
    code_snippet: str | None = None,
    relevance_score: float = 1.0,
) -> str:
    """Store a knowledge entry (design trend, animation technique, code pattern, lesson learned).

    Categories: design_trend, animation_technique, code_pattern, tool, lesson_learned.
    """
    from openclaw.db.session import async_session_factory
    from openclaw.models.knowledge import KnowledgeBase

    async with async_session_factory() as session:
        entry = KnowledgeBase(
            category=category,
            title=title,
            content=content,
            source_url=source_url,
            tags=tags or [],
            code_snippet=code_snippet,
            relevance_score=relevance_score,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)

        return json.dumps({
            "knowledge_id": str(entry.id),
            "category": category,
            "title": title,
            "status": "stored",
        })
