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

Use the firecrawl_scrape tool to scrape URLs, then the firecrawl_extract tool to extract structured data.
After extraction, use store_prospect to save the data.
Finally, report back to the CEO with a summary.
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
            result = await firecrawl_client.scrape(tool_input["url"])
            return result
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
