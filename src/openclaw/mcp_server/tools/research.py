"""Research tools — scrape design trend sites and store knowledge."""

import json

from openclaw.mcp_server.server import mcp

TREND_SOURCES = {
    "awwwards": "https://www.awwwards.com/websites/sites_of_the_day/",
    "dribbble": "https://dribbble.com/shots/popular",
    "css_tricks": "https://css-tricks.com/",
    "smashing_magazine": "https://www.smashingmagazine.com/",
    "codrops": "https://tympanus.net/codrops/",
}


@mcp.tool()
async def search_design_trends(sources: list[str] | None = None) -> str:
    """Scrape design trend websites for the latest web design trends, animations, and techniques.

    Default sources: Awwwards, Dribbble, CSS-Tricks, Smashing Magazine, Codrops.
    Returns markdown content from each source.
    """
    from openclaw.integrations.firecrawl_client import firecrawl_client

    source_names = sources or list(TREND_SOURCES.keys())
    results = []

    for name in source_names:
        url = TREND_SOURCES.get(name)
        if not url:
            results.append({"source": name, "error": f"Unknown source: {name}"})
            continue

        try:
            data = await firecrawl_client.scrape(url)
            markdown = data.get("data", {}).get("markdown", "")
            if len(markdown) > 5000:
                markdown = markdown[:5000] + "\n... [truncated]"
            results.append({"source": name, "url": url, "content": markdown})
        except Exception as e:
            results.append({"source": name, "url": url, "error": str(e)[:200]})

    return json.dumps(results, indent=2)


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
