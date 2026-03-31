"""Inbound Research Skill — scrapes prospect websites, extracts brand data,
identifies site problems.

Ported from openclaw.agents.inbound.InboundAgent.
"""

from __future__ import annotations

import json
import structlog

from openclaw.runtime.skill_base import BaseSkill, SkillContext, SkillResult

logger = structlog.get_logger()

INBOUND_SYSTEM_PROMPT = """You are the Inbound Research Agent of Clarmi Design Studio, a digital design agency.

Your job is to deeply research prospect websites, extract EVERYTHING needed to rebuild them better,
and identify specific problems with their current site that we can reference in outreach.

WORKFLOW:
1. Use firecrawl_crawl to crawl the site (up to 5 pages max)
2. Analyze the crawled content yourself to extract branding data (colors, fonts, emails, etc.)
3. Critically audit the site for specific problems (see SITE PROBLEMS below)
4. Use store_prospect to save all extracted data INCLUDING site_problems

IMPORTANT: Do NOT use firecrawl_scrape or firecrawl_extract — the crawl already captures all content.
Only use ONE firecrawl_crawl call per prospect. Extract branding data from the crawled markdown yourself.

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

SITE PROBLEMS — CRITICAL STEP:
After crawling, analyze the site content and structure to identify specific, concrete problems.
Look for ALL of these categories:

NAVIGATION & UX:
- Confusing or cluttered menu/navbar (too many items, unclear labels, buried pages)
- No mobile hamburger menu visible (non-responsive nav)
- Missing or broken links in navigation
- No clear call-to-action above the fold
- Important pages buried 3+ clicks deep

DESIGN & VISUAL:
- Dated/outdated visual design (pre-2020 aesthetic, gradients from 2010, etc.)
- Inconsistent fonts or colors across pages
- Poor text contrast / readability issues
- No visual hierarchy — everything looks the same importance
- Generic stock photos instead of real brand imagery
- Cluttered layout with no whitespace
- No scroll animations or micro-interactions (static/flat feel)

PERFORMANCE & TECH:
- Built on WordPress, Wix, Squarespace, or other page builders (mention which one)
- Likely slow load times (heavy images, lots of scripts, page builder bloat)
- Not mobile-optimized (content structure suggests desktop-only design)
- Missing HTTPS or mixed content warnings
- Outdated JavaScript frameworks or libraries

CONTENT & CONVERSION:
- Weak or missing hero section (no compelling headline above the fold)
- No social proof (missing testimonials, reviews, trust badges)
- No clear value proposition in first 5 seconds
- Missing or weak calls-to-action
- Contact info hard to find
- No pricing transparency (if applicable)
- Blog/news section abandoned (old dates)

For each problem found, write it as a SHORT, SPECIFIC, PUNCHY statement that could be used
directly in an outreach email. Think like a sales consultant who genuinely noticed something:

GOOD examples:
- "Your menu bar has 14 items — visitors won't know where to click first"
- "Your hero section is a stock photo with no headline — you have 3 seconds to hook someone"
- "Built on WordPress with 23 plugins — that's why the site takes 6+ seconds to load"
- "No mobile menu — 60% of your visitors are on phones and they can't navigate"
- "Your testimonials are buried on page 4 — nobody will ever see them"
- "No call-to-action above the fold — visitors have to scroll to figure out what you want them to do"

BAD examples (too generic, don't use these):
- "The website could be improved"
- "The design is outdated"
- "Consider modernizing"

You MUST identify at least 3 specific problems. Most sites have 5-10. Be honest and specific.
Store them in the site_problems field of store_prospect.

The goal: capture EVERYTHING from the old site so the engineer can recreate it better,
AND give the outbound agent ammunition for compelling, specific outreach.
Store all raw page content in the prospect's raw_data field.
"""

FIRECRAWL_CRAWL_TOOL = {
    "name": "firecrawl_crawl",
    "description": "Crawl a website including subpages. Returns content from up to 5 pages. This is the ONLY Firecrawl tool you should use.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The root URL to crawl."},
            "max_pages": {"type": "integer", "description": "Max pages to crawl (default 5).", "default": 5},
        },
        "required": ["url"],
    },
}

STORE_PROSPECT_TOOL = {
    "name": "store_prospect",
    "description": "Store extracted prospect data in the database. MUST include site_problems — at least 3 specific issues found on the site.",
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
            "site_problems": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["navigation", "design", "performance", "content"],
                            "description": "Problem category.",
                        },
                        "problem": {
                            "type": "string",
                            "description": "Short, specific, punchy description of the problem. Written so it can be dropped directly into a cold email.",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "How much this hurts their business.",
                        },
                    },
                    "required": ["category", "problem", "severity"],
                },
                "description": "Specific problems found on the prospect's current site. At least 3 required.",
            },
        },
        "required": ["url", "site_problems"],
    },
}


class InboundSkill(BaseSkill):
    name = "inbound"
    description = "Scrapes prospect websites, extracts brand data, identifies site problems"
    tier = "light"
    system_prompt = INBOUND_SYSTEM_PROMPT
    tools = [FIRECRAWL_CRAWL_TOOL, STORE_PROSPECT_TOOL]
    timeout = 600

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "firecrawl_crawl":
            from openclaw.integrations.firecrawl_client import firecrawl_client
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select
            from datetime import datetime, timedelta, timezone

            # Check if we already have recent crawl data (< 24h old) to avoid re-crawling
            async with async_session_factory() as session:
                existing = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = existing.scalar_one_or_none()
                if prospect and prospect.raw_data and prospect.raw_data.get("pages"):
                    crawled_at = prospect.raw_data.get("crawled_at")
                    if crawled_at:
                        try:
                            crawl_time = datetime.fromisoformat(crawled_at)
                        except (ValueError, TypeError):
                            crawl_time = None
                        if crawl_time and datetime.now(timezone.utc) - crawl_time < timedelta(hours=24):
                            self.log.info("crawl_skipped_cached", url=tool_input["url"])
                            return {
                                "success": True,
                                "url": tool_input["url"],
                                "pages_crawled": prospect.raw_data.get("pages_crawled", 0),
                                "content_preview": "\n\n".join([
                                    f"### {p['title']}\n{p['markdown'][:2000]}"
                                    for p in prospect.raw_data.get("pages", [])[:5]
                                ]),
                                "images_found": len(prospect.raw_data.get("images", [])),
                                "image_urls": prospect.raw_data.get("images", [])[:15],
                                "stored_in_database": True,
                                "note": "Using cached crawl data (less than 24h old). No Firecrawl credits used.",
                            }

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
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
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

                problems = tool_input.get("site_problems", [])
                return {
                    "status": status,
                    "url": tool_input["url"],
                    "site_problems_stored": len(problems),
                }

        return await super().handle_tool_call(tool_name, tool_input)
