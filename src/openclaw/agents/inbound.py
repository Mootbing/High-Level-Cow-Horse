from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

INBOUND_SYSTEM_PROMPT = """You are the Inbound Research Agent of Clarmi Design Studio, a digital design agency.

Your job is to deeply research prospect websites and extract EVERYTHING needed to rebuild them better.

WORKFLOW:
1. Use firecrawl_crawl to crawl the ENTIRE site (all subpages, up to 20 pages)
2. Use firecrawl_extract to get structured branding data
3. Use store_prospect to save all data

WHAT TO EXTRACT:
- Company name, tagline, mission statement
- Contact emails, phone numbers, addresses
- Brand colors (exact hex values from the site)
- Fonts used
- Logo URL and all key image URLs
- Social media links
- Industry and positioning
- Tech stack
- ALL page content: every heading, paragraph, blurb, description
- Menu items, pricing, product descriptions
- Team member names and bios
- Testimonials and reviews
- Hours of operation, locations
- Any API endpoints or external service links visible in the page
- Image URLs for hero images, product photos, team photos, gallery images
- Navigation structure (what pages exist, how they link)

The goal: capture EVERYTHING from the old site so the engineer can recreate it better.
Store all raw page content in the prospect's raw_data field.
"""

FIRECRAWL_CRAWL_TOOL = {
    "name": "firecrawl_crawl",
    "description": "Crawl an ENTIRE website including all subpages. Returns content from up to 20 pages. Use this instead of firecrawl_scrape to get the full site.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The root URL to crawl."},
            "max_pages": {"type": "integer", "description": "Max pages to crawl (default 5).", "default": 5},
        },
        "required": ["url"],
    },
}

FIRECRAWL_SCRAPE_TOOL = {
    "name": "firecrawl_scrape",
    "description": "Scrape a single page. Use firecrawl_crawl instead for full site crawls.",
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
    "description": "Extract structured branding data from a website URL using AI.",
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
    tools = [FIRECRAWL_CRAWL_TOOL, FIRECRAWL_SCRAPE_TOOL, FIRECRAWL_EXTRACT_TOOL, STORE_PROSPECT_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "firecrawl_crawl":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select

            max_pages = min(tool_input.get("max_pages", 5), 5)  # Cap at 5 to conserve Firecrawl credits
            result = await firecrawl_client.crawl(tool_input["url"], max_pages=max_pages)

            # Crawl returns a list of pages — collect all content
            pages = result.get("data", [])
            if not isinstance(pages, list):
                pages = [result.get("data", {})]

            all_content = []
            all_images = []
            all_links = []
            page_summaries = []

            for page in pages:
                if not isinstance(page, dict):
                    continue
                md = str(page.get("markdown", ""))
                metadata = page.get("metadata", {})
                page_url = metadata.get("sourceURL", metadata.get("url", ""))

                # Collect content
                all_content.append({
                    "url": page_url,
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "markdown": md[:8000],  # First 8K per page
                })

                # Extract image URLs from markdown
                import re
                images = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', md)
                images += re.findall(r'src=["\']?(https?://[^"\'>\s]+)', str(page.get("html", "")))
                all_images.extend(images[:20])  # Cap per page

                # Extract links
                links = re.findall(r'href=["\']?(https?://[^"\'>\s]+)', str(page.get("html", "")))
                all_links.extend(links[:30])

                page_summaries.append(f"- {page_url}: {metadata.get('title', 'untitled')}")

            # Deduplicate
            all_images = list(set(all_images))[:50]
            all_links = list(set(all_links))[:100]

            # Store full crawl in DB
            total_chars = sum(len(p.get("markdown", "")) for p in all_content)
            async with async_session_factory() as session:
                existing = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = existing.scalar_one_or_none()
                crawl_data = {
                    "pages": all_content,
                    "images": all_images,
                    "links": all_links,
                    "pages_crawled": len(pages),
                }
                if prospect:
                    prospect.raw_data = crawl_data
                else:
                    prospect = Prospect(url=tool_input["url"], raw_data=crawl_data)
                    session.add(prospect)
                await session.commit()

            self.log.info("crawl_stored", url=tool_input["url"], pages=len(pages), images=len(all_images), total_chars=total_chars)

            # Return summary to Claude (stays within token limits)
            return {
                "success": True,
                "url": tool_input["url"],
                "pages_crawled": len(pages),
                "pages": page_summaries[:20],
                "images_found": len(all_images),
                "image_urls": all_images[:15],
                "links_found": len(all_links),
                "key_links": [l for l in all_links if tool_input["url"].split("//")[1].split("/")[0] in l][:20],
                "content_preview": "\n\n".join([
                    f"### {p['title']}\n{p['markdown'][:2000]}" for p in all_content[:5]
                ]),
                "stored_in_database": True,
                "note": f"Full content ({total_chars:,} chars across {len(pages)} pages) stored in database.",
            }

        elif tool_name == "firecrawl_scrape":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select

            result = await firecrawl_client.scrape(tool_input["url"])
            data = result.get("data", {})

            full_markdown = str(data.get("markdown", ""))
            full_html = str(data.get("html", ""))
            total_size = len(full_markdown) + len(full_html)

            # Extract images
            import re
            images = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', full_markdown)
            images += re.findall(r'src=["\']?(https?://[^"\'>\s]+)', full_html)
            images = list(set(images))[:30]

            async with async_session_factory() as session:
                existing = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = existing.scalar_one_or_none()
                scrape_data = {
                    "markdown": full_markdown,
                    "html": full_html,
                    "metadata": data.get("metadata", {}),
                    "images": images,
                }
                if prospect:
                    prospect.raw_data = {**prospect.raw_data, **scrape_data}
                else:
                    prospect = Prospect(url=tool_input["url"], raw_data=scrape_data)
                    session.add(prospect)
                await session.commit()

            self.log.info("scrape_stored", url=tool_input["url"], total_chars=total_size, images=len(images))

            metadata = data.get("metadata", {})
            return {
                "success": True,
                "url": tool_input["url"],
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "total_content_length": total_size,
                "images_found": len(images),
                "image_urls": images[:10],
                "content_preview": full_markdown[:8000],
                "stored_in_database": True,
            }

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
            from sqlalchemy import select
            async with async_session_factory() as session:
                existing = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = existing.scalar_one_or_none()
                if prospect:
                    for field in ["company_name", "tagline", "logo_url", "industry"]:
                        if tool_input.get(field):
                            setattr(prospect, field, tool_input[field])
                    for field in ["contact_emails", "brand_colors", "fonts", "tech_stack"]:
                        if tool_input.get(field):
                            setattr(prospect, field, tool_input[field])
                    if tool_input.get("social_links"):
                        prospect.social_links = tool_input["social_links"]
                    prospect.raw_data = {**prospect.raw_data, **tool_input}
                    status = "updated"
                else:
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
                    status = "stored"
                await session.commit()
                return {"status": status, "url": tool_input["url"]}

        return await super().handle_tool_call(tool_name, tool_input)
