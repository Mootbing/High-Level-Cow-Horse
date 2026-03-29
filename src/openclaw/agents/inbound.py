from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

INBOUND_SYSTEM_PROMPT = """You are the Inbound Research Agent of OpenClaw, a digital design agency.

Your job is to scrape prospect websites and extract their branding information:
- Company name and tagline
- Contact emails
- Brand colors (hex values)
- Fonts used
- Logo URL
- Social media links
- Industry
- Tech stack

WORKFLOW:
1. First use firecrawl_scrape to get the page content (full content is stored in DB, you get a preview)
2. Then use firecrawl_extract to get clean structured branding data (colors, fonts, emails, etc.)
3. Then use store_prospect to save the structured data
4. The firecrawl_extract tool is the most important — it returns clean structured data using AI extraction

Always use BOTH scrape AND extract for best results. The scrape gives you raw content,
the extract gives you clean structured branding data.
"""

FIRECRAWL_SCRAPE_TOOL = {
    "name": "firecrawl_scrape",
    "description": "Scrape a website URL and return its content.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to scrape."},
        },
        "required": ["url"],
    },
}

FIRECRAWL_EXTRACT_TOOL = {
    "name": "firecrawl_extract",
    "description": "Extract structured branding data from a website URL.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to extract data from."},
        },
        "required": ["url"],
    },
}

STORE_PROSPECT_TOOL = {
    "name": "store_prospect",
    "description": "Store extracted prospect data in the database.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "company_name": {"type": "string"},
            "tagline": {"type": "string"},
            "contact_emails": {"type": "array", "items": {"type": "string"}},
            "brand_colors": {"type": "array", "items": {"type": "string"}},
            "fonts": {"type": "array", "items": {"type": "string"}},
            "logo_url": {"type": "string"},
            "social_links": {"type": "object"},
            "industry": {"type": "string"},
            "tech_stack": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["url"],
    },
}


@register_agent("inbound")
class InboundAgent(BaseAgent):
    agent_type = "inbound"
    system_prompt = INBOUND_SYSTEM_PROMPT
    tools = [FIRECRAWL_SCRAPE_TOOL, FIRECRAWL_EXTRACT_TOOL, STORE_PROSPECT_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "firecrawl_scrape":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select

            result = await firecrawl_client.scrape(tool_input["url"])
            data = result.get("data", {})

            # Store the FULL scrape in the database (raw_data field on Prospect)
            full_markdown = str(data.get("markdown", ""))
            full_html = str(data.get("html", ""))
            total_size = len(full_markdown) + len(full_html)

            async with async_session_factory() as session:
                existing = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = existing.scalar_one_or_none()
                if prospect:
                    prospect.raw_data = {
                        "markdown": full_markdown,
                        "html": full_html,
                        "metadata": data.get("metadata", {}),
                    }
                else:
                    prospect = Prospect(
                        url=tool_input["url"],
                        raw_data={
                            "markdown": full_markdown,
                            "html": full_html,
                            "metadata": data.get("metadata", {}),
                        },
                    )
                    session.add(prospect)
                await session.commit()

            self.log.info("scrape_stored", url=tool_input["url"], total_chars=total_size)

            # Return a focused summary to Claude (stays within token limits)
            # Extract the most useful parts: title, description, first 12K of markdown
            metadata = data.get("metadata", {})
            summary = {
                "success": True,
                "url": tool_input["url"],
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "ogImage": metadata.get("ogImage", ""),
                "total_content_length": total_size,
                "stored_in_database": True,
                "content_preview": full_markdown[:12000],
            }
            if total_size > 12000:
                summary["note"] = f"Full content ({total_size:,} chars) stored in database. This is a preview of the first 12,000 chars."
            return summary

        elif tool_name == "firecrawl_extract":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            schema = {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "tagline": {"type": "string"},
                    "contact_emails": {"type": "array", "items": {"type": "string"}},
                    "brand_colors": {"type": "array", "items": {"type": "string"}},
                    "fonts": {"type": "array", "items": {"type": "string"}},
                    "logo_url": {"type": "string"},
                    "social_links": {"type": "object"},
                    "industry": {"type": "string"},
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                },
            }
            result = await firecrawl_client.extract(
                [tool_input["url"]], schema,
                prompt="Extract company branding information including colors, fonts, emails, and tech stack."
            )
            return result
        elif tool_name == "store_prospect":
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            async with async_session_factory() as session:
                prospect = Prospect(
                    url=tool_input["url"],
                    company_name=tool_input.get("company_name"),
                    tagline=tool_input.get("tagline"),
                    contact_emails=tool_input.get("contact_emails", []),
                    brand_colors=tool_input.get("brand_colors", []),
                    fonts=tool_input.get("fonts", []),
                    logo_url=tool_input.get("logo_url"),
                    social_links=tool_input.get("social_links", {}),
                    industry=tool_input.get("industry"),
                    tech_stack=tool_input.get("tech_stack", []),
                    raw_data=tool_input,
                )
                session.add(prospect)
                await session.commit()
                return {"status": "stored", "url": tool_input["url"]}
        return await super().handle_tool_call(tool_name, tool_input)
