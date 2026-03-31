"""Prospect tools — store and lookup scraped prospect/company data."""

import json

from openclaw.mcp_server.server import mcp


@mcp.tool()
async def store_prospect(
    url: str,
    company_name: str | None = None,
    tagline: str | None = None,
    contact_emails: list[str] | None = None,
    brand_colors: list[str] | None = None,
    fonts: list[str] | None = None,
    logo_url: str | None = None,
    social_links: dict | None = None,
    industry: str | None = None,
    tech_stack: list[str] | None = None,
    site_problems: list[str] | None = None,
    raw_data: dict | None = None,
) -> str:
    """Store or update prospect data from website research.

    Saves company branding, contact info, identified site problems, and raw crawl data.
    Site problems should be SHORT, SPECIFIC, PUNCHY statements (e.g. "14-item menu — visitors won't know where to click").
    """
    from openclaw.db.session import async_session_factory
    from openclaw.services.prospect_service import get_or_create_prospect

    kwargs = {}
    if company_name is not None:
        kwargs["company_name"] = company_name
    if tagline is not None:
        kwargs["tagline"] = tagline
    if contact_emails is not None:
        kwargs["contact_emails"] = contact_emails
    if brand_colors is not None:
        kwargs["brand_colors"] = brand_colors
    if fonts is not None:
        kwargs["fonts"] = fonts
    if logo_url is not None:
        kwargs["logo_url"] = logo_url
    if social_links is not None:
        kwargs["social_links"] = social_links
    if industry is not None:
        kwargs["industry"] = industry
    if tech_stack is not None:
        kwargs["tech_stack"] = tech_stack
    if raw_data is not None:
        kwargs["raw_data"] = raw_data
    if site_problems is not None:
        kwargs["raw_data"] = {**(raw_data or {}), "site_problems": site_problems}

    async with async_session_factory() as session:
        prospect, created = await get_or_create_prospect(session, url=url, **kwargs)
        if not created:
            # Update existing prospect with new data
            for key, value in kwargs.items():
                if hasattr(prospect, key):
                    setattr(prospect, key, value)
            await session.commit()
            await session.refresh(prospect)

        return json.dumps({
            "prospect_id": str(prospect.id),
            "url": prospect.url,
            "company_name": prospect.company_name,
            "created": created,
        })


@mcp.tool()
async def lookup_prospect(url: str | None = None, company_name: str | None = None) -> str:
    """Look up a prospect by URL or company name. Returns full profile including site problems."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.prospect import Prospect
    from sqlalchemy import select

    async with async_session_factory() as session:
        if url:
            stmt = select(Prospect).where(Prospect.url == url)
        elif company_name:
            stmt = select(Prospect).where(Prospect.company_name.ilike(f"%{company_name}%"))
        else:
            return json.dumps({"error": "Provide either url or company_name"})

        result = await session.execute(stmt)
        prospect = result.scalar_one_or_none()
        if not prospect:
            return json.dumps({"error": "Prospect not found"})

        return json.dumps({
            "prospect_id": str(prospect.id),
            "url": prospect.url,
            "company_name": prospect.company_name,
            "tagline": prospect.tagline,
            "contact_emails": prospect.contact_emails,
            "brand_colors": prospect.brand_colors,
            "fonts": prospect.fonts,
            "logo_url": prospect.logo_url,
            "social_links": prospect.social_links,
            "industry": prospect.industry,
            "tech_stack": prospect.tech_stack,
            "site_problems": (prospect.raw_data or {}).get("site_problems", []),
        }, indent=2)
