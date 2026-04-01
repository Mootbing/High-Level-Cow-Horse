"""Competitor analysis tools — discover, analyze, and report on local competitors."""

from __future__ import annotations

import json

import httpx
import structlog

from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


async def _get_prospect_for_project(project_name: str):
    """Look up the Prospect record linked to a project.

    Returns (project, prospect) or (None, None).
    Uses the centralized find_project_by_name for consistent lookup.
    """
    from sqlalchemy.orm import selectinload

    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from openclaw.services.project_service import find_project_by_name

    async with async_session_factory() as session:
        project = await find_project_by_name(session, project_name)

        if not project:
            return None, None

        # Eager-load the prospect relationship if not already loaded
        if project.prospect_id and not project.prospect:
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select
            stmt = select(Prospect).where(Prospect.id == project.prospect_id)
            result = await session.execute(stmt)
            prospect = result.scalars().first()
            return project, prospect

        if not project.prospect:
            return None, None
        return project, project.prospect


# ---------------------------------------------------------------------------
# Tool 1: find_competitors
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_competitors(
    project_name: str,
    search_query: str | None = None,
    radius_m: float = 5000.0,
) -> str:
    """Find nearby competing businesses using Google Places API.

    Discovers businesses similar to the prospect in their area, scores them by
    relevance (type match, proximity, price level, review volume), and returns
    the top 10 ranked competitors.

    Call this after store_prospect — requires prospect lat/lng and industry.
    If search_query is omitted, one is auto-generated from the prospect's industry.
    """
    from openclaw.integrations.google_places import (
        haversine_distance,
        score_relevance,
        search_nearby_competitors,
    )

    project, prospect = await _get_prospect_for_project(project_name)
    if not prospect:
        return json.dumps({
            "status": "error",
            "message": "No prospect linked to this project.",
        })

    lat, lng = prospect.latitude, prospect.longitude
    if lat is None or lng is None:
        return json.dumps({
            "status": "error",
            "message": (
                "Prospect has no lat/lng. "
                "Store location data with store_prospect first."
            ),
        })

    # Build search query from industry if not provided
    query = search_query or (
        f"{prospect.industry or 'business'} near {prospect.company_name or ''}"
    )

    # Search via Google Places
    places = await search_nearby_competitors(
        query, lat, lng, radius_m=radius_m,
    )

    # Filter out the prospect itself (by URL or name match)
    prospect_url = (prospect.url or "").rstrip("/").lower()
    prospect_name_lower = (prospect.company_name or "").lower()
    filtered: list[dict] = []
    for p in places:
        p_url = (p.get("website") or "").rstrip("/").lower()
        p_name = (p.get("name") or "").lower()
        if p_url and prospect_url and p_url == prospect_url:
            continue
        if p_name and prospect_name_lower and p_name == prospect_name_lower:
            continue
        filtered.append(p)

    # Determine prospect's types and price level for scoring
    raw = prospect.raw_data or {}
    prospect_types: list[str] = raw.get("place_types", [])
    if not prospect_types and prospect.industry:
        prospect_types = [prospect.industry.lower().replace(" ", "_")]
    prospect_price: str | None = raw.get("price_level")

    # Score relevance and add distance
    for p in filtered:
        p["relevance_score"] = score_relevance(
            p, lat, lng, prospect_types, prospect_price, radius_m,
        )
        plat, plng = p.get("latitude"), p.get("longitude")
        if plat is not None and plng is not None:
            dist_m = haversine_distance(lat, lng, plat, plng)
            p["distance_mi"] = round(dist_m / 1609.34, 1)

    # Sort by relevance descending, take top 10
    filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    top = filtered[:10]

    # Persist to prospect.raw_data["competitors"]
    from sqlalchemy import select as sa_select

    from openclaw.db.session import async_session_factory
    from openclaw.models.prospect import Prospect as ProspectModel

    async with async_session_factory() as session:
        stmt = sa_select(ProspectModel).where(ProspectModel.id == prospect.id)
        result = await session.execute(stmt)
        p_record = result.scalar_one()
        existing = p_record.raw_data or {}
        p_record.raw_data = {**existing, "competitors": top}
        await session.commit()

    logger.info(
        "competitors_found",
        project=project_name,
        total=len(places),
        filtered=len(filtered),
        top=len(top),
    )

    return json.dumps({
        "status": "found",
        "total_places_returned": len(places),
        "competitors_after_filter": len(filtered),
        "top_competitors": len(top),
        "competitors": top,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: analyze_competitor_websites
# ---------------------------------------------------------------------------

def _score_website(html: str, is_https: bool) -> dict:
    """Analyse raw HTML and return quality scores + strengths/weaknesses."""
    html_lower = html.lower()
    scores: dict[str, int] = {}

    # --- Technical (1-10) ---
    tech = 5.0
    if is_https:
        tech += 1
    if "viewport" in html_lower:
        tech += 1
    if "charset" in html_lower:
        tech += 0.5
    if html_lower.count("<script") > 15:
        tech -= 1
    if "wordpress" in html_lower or "wp-content" in html_lower:
        tech -= 0.5
    if "wix.com" in html_lower or "squarespace" in html_lower:
        tech -= 0.5
    if any(kw in html_lower for kw in ("__next", "react", "_next/static", "vue")):
        tech += 1
    scores["technical"] = max(1, min(10, round(tech)))

    # --- Mobile friendly (1-10) ---
    mobile = 5.0
    if "viewport" in html_lower and "width=device-width" in html_lower:
        mobile += 2
    if "flex" in html_lower or "grid" in html_lower:
        mobile += 1
    if "@media" in html_lower:
        mobile += 1
    if html_lower.count("<table") > 3:
        mobile -= 2
    scores["mobile_friendly"] = max(1, min(10, round(mobile)))

    # --- Visual design (1-10) ---
    visual = 5.0
    if "font-family" in html_lower:
        visual += 0.5
    if "fonts.googleapis" in html_lower or "fonts.gstatic" in html_lower:
        visual += 0.5
    if "gradient" in html_lower or "animation" in html_lower:
        visual += 1
    if html_lower.count("color:") > 8 or html_lower.count("background") > 10:
        visual += 0.5
    if "<marquee" in html_lower or "<blink" in html_lower:
        visual -= 3
    if "tailwind" in html_lower or "bootstrap" in html_lower:
        visual += 0.5
    scores["visual_design"] = max(1, min(10, round(visual)))

    # --- UX / Navigation (1-10) ---
    ux = 5.0
    if "<nav" in html_lower:
        ux += 1
    if 'href="tel:' in html_lower or 'href="mailto:' in html_lower:
        ux += 1
    if "<footer" in html_lower:
        ux += 0.5
    if "<header" in html_lower:
        ux += 0.5
    if html_lower.count("<a ") > 50:
        ux -= 1
    if "search" in html_lower:
        ux += 0.5
    cta_words = [
        "book", "order", "contact", "call", "reserve",
        "get started", "sign up", "buy",
    ]
    cta_count = sum(1 for w in cta_words if w in html_lower)
    if cta_count >= 2:
        ux += 1
    elif cta_count == 0:
        ux -= 1
    scores["ux_navigation"] = max(1, min(10, round(ux)))

    # --- Content quality (1-10) ---
    content = 5.0
    if "<h1" in html_lower:
        content += 1
    if "testimonial" in html_lower or "review" in html_lower:
        content += 1
    if html_lower.count("<img") > 2:
        content += 0.5
    if html_lower.count("<p") < 3:
        content -= 1
    if "about" in html_lower and "team" in html_lower:
        content += 0.5
    if "lorem ipsum" in html_lower:
        content -= 3
    scores["content_quality"] = max(1, min(10, round(content)))

    # --- Overall weighted ---
    overall = (
        scores["visual_design"] * 0.20
        + scores["ux_navigation"] * 0.25
        + scores["content_quality"] * 0.20
        + scores["technical"] * 0.15
        + scores["mobile_friendly"] * 0.20
    )

    # --- Strengths / weaknesses ---
    strengths: list[str] = []
    weaknesses: list[str] = []

    if scores["technical"] >= 7:
        strengths.append("Modern tech stack — fast and well-built")
    elif scores["technical"] <= 4:
        weaknesses.append("Outdated tech — slow loads, likely WordPress or page builder")

    if scores["mobile_friendly"] >= 7:
        strengths.append("Fully responsive — works well on mobile")
    elif scores["mobile_friendly"] <= 4:
        weaknesses.append("Not mobile-friendly — losing phone visitors")

    if scores["visual_design"] >= 7:
        strengths.append("Clean, modern visual design")
    elif scores["visual_design"] <= 4:
        weaknesses.append("Dated visual design — looks stuck in 2015")

    if scores["ux_navigation"] >= 7:
        strengths.append("Clear navigation and strong CTAs")
    elif scores["ux_navigation"] <= 4:
        weaknesses.append("Poor navigation — visitors can't find what they need")

    if scores["content_quality"] >= 7:
        strengths.append("Strong content with social proof")
    elif scores["content_quality"] <= 4:
        weaknesses.append("Thin content — no testimonials or social proof")

    if is_https:
        strengths.append("HTTPS secured")
    else:
        weaknesses.append("No HTTPS — browser shows 'Not Secure' warning")

    if cta_count >= 2:
        strengths.append("Multiple clear calls-to-action")
    elif cta_count == 0:
        weaknesses.append("No clear call-to-action — visitors don't know what to do")

    return {
        "scores": scores,
        "overall_score": round(overall, 1),
        "strengths": strengths[:3],
        "weaknesses": weaknesses[:3],
    }


@mcp.tool()
async def analyze_competitor_websites(project_name: str) -> str:
    """Scrape and score the websites of the top 5 competitors.

    For each competitor with a website, fetches the homepage and scores it on:
    visual_design, ux_navigation, content_quality, technical, mobile_friendly
    (each 1-10).  Also identifies up to 3 strengths and 3 weaknesses as short
    punchy statements.

    Call find_competitors first.  Results are stored in
    prospect.raw_data["competitor_analysis"].
    """
    project, prospect = await _get_prospect_for_project(project_name)
    if not prospect:
        return json.dumps({
            "status": "error",
            "message": "No prospect linked to this project.",
        })

    competitors = (prospect.raw_data or {}).get("competitors", [])
    if not competitors:
        return json.dumps({
            "status": "error",
            "message": "No competitors found. Call find_competitors first.",
        })

    top5 = competitors[:5]
    analyses: list[dict] = []

    for comp in top5:
        website = comp.get("website")
        analysis: dict = {
            "name": comp.get("name"),
            "address": comp.get("address"),
            "distance_mi": comp.get("distance_mi"),
            "rating": comp.get("rating"),
            "review_count": comp.get("review_count"),
            "price_level": comp.get("price_level"),
            "primary_type": (
                comp.get("primary_type_display") or comp.get("primary_type")
            ),
            "website": website,
            "relevance_score": comp.get("relevance_score"),
            "google_maps_url": comp.get("google_maps_url"),
        }

        # No website → score 0
        if not website:
            analysis["website_scores"] = None
            analysis["strengths"] = []
            analysis["weaknesses"] = [
                "No website — invisible to online customers",
            ]
            analysis["overall_score"] = 0
            analyses.append(analysis)
            continue

        # Fetch the homepage (with bot-detection bypass)
        try:
            from openclaw.mcp_server.tools.lead_gen import _fetch_page
            html, final_url, is_https, _status = await _fetch_page(
                website, timeout=15,
            )
            if _status != 200:
                raise Exception(f"HTTP {_status}")
        except Exception as exc:
            analysis["website_scores"] = None
            analysis["strengths"] = []
            analysis["weaknesses"] = [
                f"Website unreachable — {str(exc)[:80]}",
            ]
            analysis["overall_score"] = 0
            analyses.append(analysis)
            continue

        # Score
        result = _score_website(html, is_https)
        analysis["website_scores"] = result["scores"]
        analysis["overall_score"] = result["overall_score"]
        analysis["strengths"] = result["strengths"]
        analysis["weaknesses"] = result["weaknesses"]
        analyses.append(analysis)

    # Persist to prospect.raw_data["competitor_analysis"]
    from sqlalchemy import select as sa_select

    from openclaw.db.session import async_session_factory
    from openclaw.models.prospect import Prospect as ProspectModel

    async with async_session_factory() as session:
        stmt = sa_select(ProspectModel).where(ProspectModel.id == prospect.id)
        result = await session.execute(stmt)
        p_record = result.scalar_one()
        existing = p_record.raw_data or {}
        p_record.raw_data = {**existing, "competitor_analysis": analyses}
        await session.commit()

    logger.info(
        "competitor_analysis_complete",
        project=project_name,
        analyzed=len(analyses),
    )

    return json.dumps({
        "status": "analyzed",
        "competitors_analyzed": len(analyses),
        "analysis": analyses,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: generate_competitor_report
# ---------------------------------------------------------------------------

@mcp.tool()
async def generate_competitor_report(project_name: str) -> str:
    """Prepare data and template for generating the competitor analysis HTML deck.

    Returns the competitor analysis data, prospect data, template reference path,
    and base CSS path.  The agent should then:

    1. Read templates/competitors/reference.md for the generation guide
    2. Read templates/pitch/viewport-base.css to embed inline
    3. Generate the HTML following the reference
    4. Call write_code(project_name, "public/competitors/index.html", html)
    5. Call deploy(project_name, "Add competitor analysis")

    The deck is served at /competitors/ on the deployed site.
    """
    project, prospect = await _get_prospect_for_project(project_name)
    if not prospect:
        return json.dumps({
            "status": "error",
            "message": "No prospect linked to this project.",
        })

    analysis = (prospect.raw_data or {}).get("competitor_analysis", [])
    if not analysis:
        return json.dumps({
            "status": "error",
            "message": (
                "No competitor analysis found. "
                "Call analyze_competitor_websites first."
            ),
        })

    # Market stats for the overview slide
    ratings = [c["rating"] for c in analysis if c.get("rating")]
    web_scores = [c["overall_score"] for c in analysis if c.get("overall_score")]
    price_levels = [c["price_level"] for c in analysis if c.get("price_level")]

    market_stats: dict = {
        "total_analyzed": len(analysis),
        "avg_rating": (
            round(sum(ratings) / len(ratings), 1) if ratings else None
        ),
        "avg_website_score": (
            round(sum(web_scores) / len(web_scores), 1) if web_scores else None
        ),
        "price_distribution": {
            pl: price_levels.count(pl) for pl in set(price_levels)
        },
    }

    # Common weaknesses across competitors (for gap analysis)
    all_weaknesses: list[str] = []
    for c in analysis:
        all_weaknesses.extend(c.get("weaknesses", []))
    weakness_freq: dict[str, int] = {}
    for w in all_weaknesses:
        key = w.lower()[:50]
        weakness_freq[key] = weakness_freq.get(key, 0) + 1
    common_weaknesses = sorted(
        weakness_freq.items(), key=lambda x: x[1], reverse=True,
    )[:5]

    return json.dumps({
        "status": "ready",
        "prospect": {
            "company_name": prospect.company_name,
            "industry": prospect.industry,
            "brand_colors": prospect.brand_colors,
            "site_problems": (prospect.raw_data or {}).get("site_problems", []),
        },
        "competitors": analysis,
        "market_stats": market_stats,
        "common_competitor_weaknesses": [w[0] for w in common_weaknesses],
        "template_reference": "templates/competitors/reference.md",
        "base_css": "templates/pitch/viewport-base.css",
        "output_path": "public/competitors/index.html",
        "note": (
            "Read the template reference and base CSS, "
            "then generate the HTML and call write_code + deploy."
        ),
    }, indent=2)
