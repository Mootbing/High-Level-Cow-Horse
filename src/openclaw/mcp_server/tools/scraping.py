"""Scraping tools — website crawling and branding extraction via Firecrawl."""

from openclaw.mcp_server.server import mcp


@mcp.tool()
async def scrape_website(url: str, max_pages: int = 5) -> str:
    """Crawl a website (up to max_pages) and return markdown content, images, and link structure.

    Use this to research a prospect's site before building a replacement.
    Returns markdown content from each crawled page.
    """
    from openclaw.integrations.firecrawl_client import firecrawl_client

    result = await firecrawl_client.crawl(url, max_pages=min(max_pages, 5))
    status = result.get("status", "unknown")
    pages = result.get("data", [])

    if not pages:
        return f"Crawl status: {status}. No pages returned for {url}."

    output_parts = [f"Crawled {len(pages)} page(s) from {url} (status: {status})\n"]
    for i, page in enumerate(pages):
        page_url = page.get("metadata", {}).get("sourceURL", f"page-{i}")
        markdown = page.get("markdown", "")
        # Truncate very long pages
        if len(markdown) > 8000:
            markdown = markdown[:8000] + "\n\n... [truncated]"
        output_parts.append(f"--- PAGE {i + 1}: {page_url} ---\n{markdown}\n")

    return "\n".join(output_parts)


@mcp.tool()
async def extract_branding(url: str) -> str:
    """Extract structured branding data from a URL using AI-powered extraction.

    Returns company name, tagline, colors, fonts, emails, social links, tech stack.
    """
    from openclaw.integrations.firecrawl_client import firecrawl_client
    import json

    schema = {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "tagline": {"type": "string"},
            "contact_emails": {"type": "array", "items": {"type": "string"}},
            "brand_colors": {"type": "array", "items": {"type": "string"}, "description": "Hex color values"},
            "fonts": {"type": "array", "items": {"type": "string"}},
            "logo_url": {"type": "string"},
            "social_links": {"type": "object"},
            "industry": {"type": "string"},
            "tech_stack": {"type": "array", "items": {"type": "string"}},
        },
    }

    result = await firecrawl_client.extract(
        urls=[url],
        schema=schema,
        prompt="Extract all branding information: company name, tagline, contact emails, brand colors (hex), fonts, logo URL, social media links, industry, and tech stack.",
    )
    return json.dumps(result, indent=2)
