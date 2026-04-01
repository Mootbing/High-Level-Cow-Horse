"""Lead generation tools — discover, audit, score, and qualify prospects at scale."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import structlog

from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()

# Browser-like headers to avoid bot detection on simple httpx requests
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


async def _fetch_page(url: str, timeout: int = 20) -> tuple[str, str, bool, int]:
    """Fetch a webpage with bot-detection bypass.

    Tries httpx with browser headers first. If blocked (403/captcha),
    falls back to Playwright headless browser.

    Returns (html, final_url, is_https, status_code).
    Raises Exception if both methods fail.
    """
    # Attempt 1: httpx with browser headers (fast)
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers=_BROWSER_HEADERS,
        ) as client:
            resp = await client.get(url)
            html = resp.text[:80_000]
            final_url = str(resp.url)
            is_https = final_url.startswith("https://")

            # Check for captcha/challenge pages
            html_lower = html.lower()
            is_blocked = (
                resp.status_code == 403
                or resp.status_code == 503
                or "cf-challenge" in html_lower
                or "captcha" in html_lower
                or "just a moment" in html_lower
                or ("ray id" in html_lower and len(html) < 5000)
                or "checking your browser" in html_lower
                or "challenge-platform" in html_lower
            )

            if not is_blocked and resp.status_code == 200:
                return html, final_url, is_https, resp.status_code

            logger.info("httpx_blocked", url=url, status=resp.status_code)
    except Exception as exc:
        logger.info("httpx_failed", url=url, error=str(exc)[:100])

    # Attempt 2: Playwright headless browser (handles JS challenges)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise Exception(
            f"Website blocked request and Playwright not available: {url}"
        )

    logger.info("playwright_fallback", url=url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                viewport={"width": 1280, "height": 800},
            )
            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=30000,
            )
            # Wait for any JS challenges to resolve
            await page.wait_for_timeout(3000)

            status_code = response.status if response else 0
            final_url = page.url
            is_https = final_url.startswith("https://")
            html = await page.content()
            html = html[:80_000]

            return html, final_url, is_https, status_code
        finally:
            await browser.close()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication."""
    parsed = urlparse(url.lower().rstrip("/"))
    host = parsed.netloc or parsed.path
    host = host.removeprefix("www.")
    return host


def _detect_tech_stack(html: str) -> list[str]:
    """Detect CMS/framework from HTML source."""
    h = html.lower()
    stack: list[str] = []
    if "wp-content" in h or "wordpress" in h:
        stack.append("WordPress")
    if "wix.com" in h:
        stack.append("Wix")
    if "squarespace" in h:
        stack.append("Squarespace")
    if "shopify" in h:
        stack.append("Shopify")
    if "weebly" in h:
        stack.append("Weebly")
    if "godaddy" in h:
        stack.append("GoDaddy")
    if "webflow" in h:
        stack.append("Webflow")
    if "__next" in h or "_next/static" in h:
        stack.append("Next.js")
    if "react" in h and "__next" not in h:
        stack.append("React")
    if "vue" in h:
        stack.append("Vue")
    if "angular" in h:
        stack.append("Angular")
    if "gatsby" in h:
        stack.append("Gatsby")
    if "bootstrap" in h:
        stack.append("Bootstrap")
    if "tailwind" in h:
        stack.append("Tailwind")
    if "jquery" in h:
        stack.append("jQuery")
    return stack


def _extract_site_problems(html: str, tech_stack: list[str], is_https: bool) -> list[str]:
    """Generate specific, punchy site problem statements from HTML analysis."""
    h = html.lower()
    problems: list[str] = []

    # Tech / performance problems
    page_builders = {"WordPress", "Wix", "Squarespace", "Weebly", "GoDaddy"}
    detected_builders = [t for t in tech_stack if t in page_builders]
    if detected_builders:
        builder = detected_builders[0]
        plugin_count = h.count("wp-content/plugins/")
        if builder == "WordPress" and plugin_count > 5:
            problems.append(
                f"{builder} with {plugin_count}+ plugins — bloated, slow, security risk"
            )
        else:
            problems.append(
                f"Built on {builder} — template site, limited performance and customization"
            )

    script_count = h.count("<script")
    if script_count > 12:
        problems.append(
            f"{script_count} script tags — page likely takes 4s+ to load"
        )

    if not is_https:
        problems.append(
            "No HTTPS — browser shows 'Not Secure' warning to every visitor"
        )

    # Mobile / responsive problems
    if "viewport" not in h or "width=device-width" not in h:
        problems.append(
            "No mobile viewport — site is unusable on phones"
        )
    if h.count("<table") > 3 and "flex" not in h and "grid" not in h:
        problems.append(
            "Table-based layout — broken on mobile, stuck in 2005"
        )
    if "@media" not in h and "flex" not in h and "grid" not in h:
        problems.append(
            "No responsive CSS — layout doesn't adapt to screen size"
        )

    # Navigation / UX problems
    nav_links = h.count("<a ")
    if nav_links > 40:
        problems.append(
            f"{nav_links}+ links on the page — cluttered, visitors don't know where to click"
        )

    cta_words = ["book", "order", "contact", "call", "reserve",
                 "get started", "sign up", "buy", "schedule", "request"]
    cta_count = sum(1 for w in cta_words if w in h)
    if cta_count == 0:
        problems.append(
            "No clear call-to-action — visitors leave without converting"
        )

    # Content problems
    if "<h1" not in h:
        problems.append(
            "Missing H1 heading — hurts SEO and visitors don't know what the business does"
        )
    if "testimonial" not in h and "review" not in h and "rating" not in h:
        problems.append(
            "No testimonials or reviews — missing social proof that builds trust"
        )
    if h.count("<img") < 2:
        problems.append(
            "Almost no images — site feels empty and unprofessional"
        )
    if "lorem ipsum" in h:
        problems.append(
            "Placeholder text visible — 'Lorem ipsum' still on the live site"
        )

    # Design problems
    if "fonts.googleapis" not in h and "fonts.gstatic" not in h and "typekit" not in h:
        problems.append(
            "No custom fonts — using default system fonts looks generic"
        )
    if "<marquee" in h or "<blink" in h:
        problems.append(
            "Using <marquee> or <blink> — literally 1990s HTML"
        )

    # Copyright year check (match both © symbol and &copy; entity)
    copyright_match = re.search(r"(?:©|&copy;)\s*(\d{4})", html)
    if copyright_match:
        year = int(copyright_match.group(1))
        if year < datetime.now().year - 2:
            problems.append(
                f"Copyright says {year} — site appears abandoned"
            )

    return problems[:8]  # Cap at 8 most important


def _score_website_quality(html: str, is_https: bool) -> dict:
    """Score website quality across 5 dimensions (1-10 each).

    Reuses the same scoring methodology as competitor analysis for consistency.
    """
    h = html.lower()
    scores: dict[str, int] = {}

    # Technical (1-10)
    tech = 5.0
    if is_https:
        tech += 1
    if "viewport" in h:
        tech += 1
    if "charset" in h:
        tech += 0.5
    if h.count("<script") > 15:
        tech -= 1
    if "wordpress" in h or "wp-content" in h:
        tech -= 0.5
    if "wix.com" in h or "squarespace" in h:
        tech -= 0.5
    if any(kw in h for kw in ("__next", "react", "_next/static", "vue")):
        tech += 1
    scores["technical"] = max(1, min(10, round(tech)))

    # Mobile friendly (1-10)
    mobile = 5.0
    if "viewport" in h and "width=device-width" in h:
        mobile += 2
    if "flex" in h or "grid" in h:
        mobile += 1
    if "@media" in h:
        mobile += 1
    if h.count("<table") > 3:
        mobile -= 2
    scores["mobile_friendly"] = max(1, min(10, round(mobile)))

    # Visual design (1-10)
    visual = 5.0
    if "font-family" in h:
        visual += 0.5
    if "fonts.googleapis" in h or "fonts.gstatic" in h:
        visual += 0.5
    if "gradient" in h or "animation" in h:
        visual += 1
    if h.count("color:") > 8 or h.count("background") > 10:
        visual += 0.5
    if "<marquee" in h or "<blink" in h:
        visual -= 3
    if "tailwind" in h or "bootstrap" in h:
        visual += 0.5
    scores["visual_design"] = max(1, min(10, round(visual)))

    # UX / Navigation (1-10)
    ux = 5.0
    if "<nav" in h:
        ux += 1
    if 'href="tel:' in h or 'href="mailto:' in h:
        ux += 1
    if "<footer" in h:
        ux += 0.5
    if "<header" in h:
        ux += 0.5
    if h.count("<a ") > 50:
        ux -= 1
    if "search" in h:
        ux += 0.5
    cta_words = ["book", "order", "contact", "call", "reserve",
                 "get started", "sign up", "buy"]
    cta_count = sum(1 for w in cta_words if w in h)
    if cta_count >= 2:
        ux += 1
    elif cta_count == 0:
        ux -= 1
    scores["ux_navigation"] = max(1, min(10, round(ux)))

    # Content quality (1-10)
    content = 5.0
    if "<h1" in h:
        content += 1
    if "testimonial" in h or "review" in h:
        content += 1
    if h.count("<img") > 2:
        content += 0.5
    if h.count("<p") < 3:
        content -= 1
    if "about" in h and "team" in h:
        content += 0.5
    if "lorem ipsum" in h:
        content -= 3
    scores["content_quality"] = max(1, min(10, round(content)))

    # Weighted overall
    overall = (
        scores["visual_design"] * 0.20
        + scores["ux_navigation"] * 0.25
        + scores["content_quality"] * 0.20
        + scores["technical"] * 0.15
        + scores["mobile_friendly"] * 0.20
    )

    return {
        "scores": scores,
        "overall": round(overall, 1),
    }


def _compute_opportunity_score(
    business_rating: float | None,
    review_count: int,
    website_overall: float,
) -> float:
    """Compute lead opportunity score.

    Formula: business_quality * website_weakness
    - Good business (high rating, many reviews) + bad website = HIGH score
    - Bad business OR good website = LOW score

    Returns 0.0-10.0 scale.
    """
    # Clamp inputs to valid ranges
    rating = max(0.0, min(business_rating or 3.5, 5.0))
    review_count = max(0, review_count)
    website_overall = max(0.0, min(website_overall, 10.0))

    # Business quality: 0-1 scale
    rating_signal = rating / 5.0

    # Review volume: logarithmic scale, sweet spot 20-500
    if review_count <= 0:
        volume_signal = 0.3
    else:
        volume_signal = min(math.log10(review_count + 1) / 3.0, 1.0)

    business_quality = (rating_signal * 0.6 + volume_signal * 0.4)

    # Website weakness: inverse of quality (lower quality = higher opportunity)
    website_weakness = (10.0 - website_overall) / 10.0

    # Opportunity = business quality * website weakness * 10
    opportunity = business_quality * website_weakness * 10.0

    return round(min(opportunity, 10.0), 2)


def _compute_adventure_score(
    business_rating: float | None,
    review_count: int,
) -> float:
    """Score adventure-mode leads (businesses with no website).

    Purely business quality — no website weakness factor.
    High rating + many reviews + no website = goldmine.

    Returns 0.0-10.0 scale.
    """
    rating = max(0.0, min(business_rating or 3.0, 5.0))
    review_count = max(0, review_count)

    rating_signal = rating / 5.0

    if review_count <= 0:
        volume_signal = 0.1
    else:
        volume_signal = min(math.log10(review_count + 1) / 3.0, 1.0)

    adventure_score = (rating_signal * 0.5 + volume_signal * 0.5) * 10.0
    return round(min(adventure_score, 10.0), 2)


def _extract_brand_colors(html: str) -> list[str]:
    """Extract hex colors from HTML/CSS."""
    hex_pattern = re.compile(r"#([0-9a-fA-F]{3,8})\b")
    matches = hex_pattern.findall(html)
    # Filter to valid 3 or 6 char hex, deduplicate, skip common defaults
    colors: list[str] = []
    skip = {"000", "fff", "000000", "ffffff", "333", "666", "999",
            "ccc", "ddd", "eee", "333333", "666666", "999999"}
    seen: set[str] = set()
    for m in matches:
        if len(m) not in (3, 6):
            continue
        lower = m.lower()
        if lower in skip or lower in seen:
            continue
        seen.add(lower)
        colors.append(f"#{lower}")
        if len(colors) >= 5:
            break
    return colors


def _extract_contact_emails(html: str) -> list[str]:
    """Extract email addresses from HTML."""
    email_pattern = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    matches = email_pattern.findall(html)
    # Deduplicate, skip common non-business emails
    skip_domains = {"example.com", "sentry.io", "wixpress.com",
                    "wordpress.org", "schema.org", "w3.org"}
    emails: list[str] = []
    seen: set[str] = set()
    for email in matches:
        lower = email.lower()
        domain = lower.split("@")[1]
        if domain in skip_domains or lower in seen:
            continue
        seen.add(lower)
        emails.append(lower)
        if len(emails) >= 5:
            break
    return emails


# ---------------------------------------------------------------------------
# Tool 1: discover_prospects
# ---------------------------------------------------------------------------

@mcp.tool()
async def discover_prospects(
    industry: str,
    location: str,
    max_results: int = 10,
    radius_m: float = 10000.0,
    mode: str = "revamp",
) -> str:
    """Discover businesses in a target industry and location using Google Places API.

    Two modes:
    - "revamp" (default): Finds businesses WITH websites to redesign.
    - "adventure": Finds businesses WITHOUT websites — ranked by reviews/rating.
      These are successful offline businesses with no online presence.

    Does NOT store anything — use run_lead_generation for the full pipeline,
    or audit_prospect_website to evaluate individual results.

    Args:
        industry: Business type (e.g. "restaurant", "salon", "dental office", "plumber")
        location: City/area (e.g. "Austin TX", "Brooklyn NY", "downtown Dallas")
        max_results: Maximum businesses to return (default 10, max 20)
        radius_m: Search radius in meters (default 10km)
        mode: "revamp" (businesses with websites) or "adventure" (businesses without websites)
    """
    from openclaw.integrations.google_places import search_nearby_competitors

    mode = mode.lower()
    if mode not in ("revamp", "adventure"):
        return json.dumps({"status": "error", "message": f"Invalid mode: {mode}. Use 'revamp' or 'adventure'."})

    max_results = min(max_results, 20)

    # We need lat/lng for the search — geocode the location first
    lat, lng = await _geocode_location(location)
    if lat is None or lng is None:
        return json.dumps({
            "status": "error",
            "message": f"Could not geocode location: {location}. Try a more specific city/address.",
        })

    # Search Google Places
    query = f"{industry} in {location}"
    try:
        places = await search_nearby_competitors(
            query, lat, lng, radius_m=radius_m, max_results=max_results,
        )
    except Exception as exc:
        logger.error("discover_places_error", error=str(exc))
        return json.dumps({
            "status": "error",
            "message": f"Google Places search failed: {str(exc)[:200]}",
        })

    # Split by website presence
    with_websites = [p for p in places if p.get("website")]
    without_websites_list = [p for p in places if not p.get("website")]

    # Select target list based on mode
    if mode == "adventure":
        # Sort by rating * log(review_count) descending — best businesses first
        def _adventure_sort_key(p: dict) -> float:
            rc = p.get("review_count", 0)
            return (p.get("rating") or 0) * (math.log10(rc + 1) if rc > 0 else 0)

        without_websites_list.sort(key=_adventure_sort_key, reverse=True)
        target_places = without_websites_list
    else:
        target_places = with_websites

    # Check for duplicates already in our database (batch query)
    from openclaw.db.session import async_session_factory
    from openclaw.models.prospect import Prospect
    from sqlalchemy import select, or_

    existing_urls: set[str] = set()
    if target_places:
        if mode == "adventure":
            # Adventure mode: Google Maps URLs share the same domain, so use exact match
            maps_urls = [p.get("google_maps_url") for p in target_places if p.get("google_maps_url")]
            if maps_urls:
                async with async_session_factory() as session:
                    stmt = select(Prospect.url).where(Prospect.url.in_(maps_urls))
                    result = await session.execute(stmt)
                    existing_urls = {row[0] for row in result.all()}
        else:
            # Revamp mode: use normalized domain matching (each business has unique domain)
            normalized_map: dict[str, str] = {}
            for p in target_places:
                url = p.get("website")
                if url:
                    normalized_map[_normalize_url(url)] = url

            if normalized_map:
                async with async_session_factory() as session:
                    conditions = [
                        Prospect.url.ilike(f"%{n}%") for n in normalized_map
                    ]
                    stmt = select(Prospect.url).where(or_(*conditions))
                    result = await session.execute(stmt)
                    existing_prospect_urls = [row[0] for row in result.all()]

                    for existing_url in existing_prospect_urls:
                        for normalized in normalized_map:
                            if normalized in existing_url.lower():
                                existing_urls.add(normalized)
                                break

    # Build response list
    prospects_list = []
    for p in target_places:
        if mode == "adventure":
            lookup_url = p.get("google_maps_url")
            is_existing = lookup_url in existing_urls if lookup_url else False
        else:
            lookup_url = p.get("website")
            normalized = _normalize_url(lookup_url) if lookup_url else ""
            is_existing = normalized in existing_urls
        entry = {
            "name": p.get("name"),
            "address": p.get("address"),
            "rating": p.get("rating"),
            "review_count": p.get("review_count", 0),
            "price_level": p.get("price_level"),
            "primary_type": (
                p.get("primary_type_display") or p.get("primary_type")
            ),
            "latitude": p.get("latitude"),
            "longitude": p.get("longitude"),
            "google_maps_url": p.get("google_maps_url"),
            "already_in_db": is_existing,
        }
        if mode == "revamp":
            entry["website"] = p.get("website")
        else:
            entry["adventure_score"] = _compute_adventure_score(
                p.get("rating"), p.get("review_count", 0),
            )
        prospects_list.append(entry)

    new_prospects = [p for p in prospects_list if not p["already_in_db"]]

    logger.info(
        "prospects_discovered",
        industry=industry,
        location=location,
        mode=mode,
        total_places=len(places),
        target_count=len(target_places),
        new_prospects=len(new_prospects),
    )

    return json.dumps({
        "status": "discovered",
        "mode": mode,
        "search_query": query,
        "search_center": {"latitude": lat, "longitude": lng},
        "total_places_found": len(places),
        "with_websites": len(with_websites),
        "without_websites": len(without_websites_list),
        "target_count": len(target_places),
        "already_in_database": len(existing_urls),
        "new_prospects": len(new_prospects),
        "prospects": prospects_list,
    }, indent=2)


async def _geocode_location(location: str) -> tuple[float | None, float | None]:
    """Geocode a location string to lat/lng using Google Places Text Search."""
    from openclaw.config import settings

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.location,places.formattedAddress",
        "Content-Type": "application/json",
    }
    payload = {
        "textQuery": location,
        "maxResultCount": 1,
        "languageCode": "en",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error("geocode_error", status=response.status_code)
                return None, None
            data = response.json()
            places = data.get("places", [])
            if not places:
                return None, None
            loc = places[0].get("location", {})
            return loc.get("latitude"), loc.get("longitude")
    except Exception as exc:
        logger.error("geocode_exception", error=str(exc))
        return None, None


# ---------------------------------------------------------------------------
# Tool 2: audit_prospect_website
# ---------------------------------------------------------------------------

@mcp.tool()
async def audit_prospect_website(
    url: str,
    company_name: str | None = None,
    industry: str | None = None,
) -> str:
    """Fetch and audit a prospect's website for quality, problems, and lead potential.

    Scores the website across 5 dimensions (technical, mobile, visual, UX, content),
    identifies specific site problems as punchy statements, extracts basic branding
    data, and detects the tech stack.

    Use this to evaluate individual prospects before deciding to pursue them.
    """
    # Fetch the website (with bot-detection bypass)
    try:
        html, final_url, is_https, status_code = await _fetch_page(url)
    except Exception as exc:
        return json.dumps({
            "status": "error",
            "url": url,
            "message": f"Could not fetch website: {str(exc)[:200]}",
        })

    if status_code != 200:
        return json.dumps({
            "status": "error",
            "url": url,
            "message": f"Website returned HTTP {status_code}",
        })

    # Score the website
    quality = _score_website_quality(html, is_https)

    # Detect tech stack
    tech_stack = _detect_tech_stack(html)

    # Extract site problems
    site_problems = _extract_site_problems(html, tech_stack, is_https)

    # Extract basic branding
    brand_colors = _extract_brand_colors(html)
    contact_emails = _extract_contact_emails(html)

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else None

    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        html, re.IGNORECASE,
    )
    meta_description = desc_match.group(1).strip() if desc_match else None

    # Content size metrics
    content_length = len(html)
    image_count = html.lower().count("<img")
    link_count = html.lower().count("<a ")

    result = {
        "status": "audited",
        "url": url,
        "final_url": final_url,
        "company_name": company_name,
        "page_title": page_title,
        "meta_description": meta_description,
        "is_https": is_https,
        "tech_stack": tech_stack,
        "website_scores": quality["scores"],
        "website_overall": quality["overall"],
        "site_problems": site_problems,
        "problem_count": len(site_problems),
        "brand_colors": brand_colors,
        "contact_emails": contact_emails,
        "content_metrics": {
            "html_size_kb": round(content_length / 1024, 1),
            "image_count": image_count,
            "link_count": link_count,
        },
    }

    logger.info(
        "prospect_audited",
        url=url,
        overall_score=quality["overall"],
        problems=len(site_problems),
    )

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: run_lead_generation
# ---------------------------------------------------------------------------

@mcp.tool()
async def run_lead_generation(
    industry: str,
    location: str,
    max_results: int = 10,
    radius_m: float = 10000.0,
    min_opportunity_score: float = 2.5,
    mode: str = "revamp",
) -> str:
    """Full lead generation pipeline: discover businesses, score, and store qualified leads.

    Two modes:
    - "revamp" (default): Finds businesses WITH websites, audits them, scores by
      business quality x website weakness. Good business + bad website = high score.
    - "adventure": Finds businesses WITHOUT websites, scores purely on business quality
      (rating + reviews). Successful offline businesses with no online presence = goldmine.

    Args:
        industry: Business type (e.g. "restaurant", "hair salon", "dentist")
        location: City/area (e.g. "Austin TX", "downtown Chicago")
        max_results: Max businesses to discover (default 10, max 20)
        radius_m: Search radius in meters (default 10km)
        min_opportunity_score: Minimum score to qualify as a lead (default 2.5, scale 0-10)
        mode: "revamp" (businesses with websites) or "adventure" (businesses without websites)
    """
    from openclaw.db.session import async_session_factory
    from openclaw.integrations.google_places import search_nearby_competitors
    from openclaw.models.prospect import Prospect
    from openclaw.services.prospect_service import get_or_create_prospect
    from sqlalchemy import or_, select

    mode = mode.lower()
    if mode not in ("revamp", "adventure"):
        return json.dumps({"status": "error", "message": f"Invalid mode: {mode}. Use 'revamp' or 'adventure'."})

    max_results = min(max_results, 20)
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # Step 1: Geocode location
    lat, lng = await _geocode_location(location)
    if lat is None or lng is None:
        return json.dumps({
            "status": "error",
            "message": f"Could not geocode location: {location}",
        })

    # Step 2: Discover businesses
    query = f"{industry} in {location}"
    try:
        places = await search_nearby_competitors(
            query, lat, lng, radius_m=radius_m, max_results=max_results,
        )
    except Exception as exc:
        return json.dumps({
            "status": "error",
            "message": f"Google Places search failed: {str(exc)[:200]}",
        })

    # Split by website presence and select target list
    with_websites = [p for p in places if p.get("website")]
    without_websites = [p for p in places if not p.get("website")]

    if mode == "adventure":
        target_places = without_websites
        no_results_msg = f"Found {len(places)} businesses but all have websites already."
    else:
        target_places = with_websites
        no_results_msg = f"Found {len(places)} businesses but none have websites."

    if not target_places:
        return json.dumps({
            "status": "no_results",
            "mode": mode,
            "message": no_results_msg,
            "search_query": query,
        })

    # Step 3: Pre-check for existing prospects (batch query to avoid N+1)
    existing_map: dict[str, str] = {}  # lookup_key -> prospect_id

    if mode == "adventure":
        # Adventure mode: exact URL match (Google Maps URLs share the same domain)
        maps_urls = [p.get("google_maps_url") for p in target_places if p.get("google_maps_url")]
        if maps_urls:
            async with async_session_factory() as session:
                stmt = select(Prospect).where(Prospect.url.in_(maps_urls))
                result = await session.execute(stmt)
                for prospect in result.scalars().all():
                    existing_map[prospect.url] = str(prospect.id)
    else:
        # Revamp mode: normalized domain matching
        normalized_to_url: dict[str, str] = {}
        for p in target_places:
            url = p.get("website")
            if url:
                normalized_to_url[_normalize_url(url)] = url

        if normalized_to_url:
            async with async_session_factory() as session:
                conditions = [
                    Prospect.url.ilike(f"%{n}%") for n in normalized_to_url
                ]
                stmt = select(Prospect).where(or_(*conditions))
                result = await session.execute(stmt)
                for prospect in result.scalars().all():
                    p_url = prospect.url.lower()
                    for normalized in normalized_to_url:
                        if normalized in p_url:
                            existing_map[normalized] = str(prospect.id)
                            break

    # Process each place
    leads: list[dict] = []
    errors: list[dict] = []
    skipped_existing = 0

    for place in target_places:
        # Determine dedup key based on mode
        if mode == "adventure":
            dedup_key = place.get("google_maps_url") or ""
        else:
            lookup_url = place.get("website")
            dedup_key = _normalize_url(lookup_url) if lookup_url else ""

        # Check if already in database
        if dedup_key in existing_map:
            skipped_existing += 1
            leads.append({
                "name": place.get("name"),
                "website": place.get("website"),
                "google_maps_url": place.get("google_maps_url"),
                "status": "already_exists",
                "prospect_id": existing_map[normalized],
                "opportunity_score": None,
            })
            continue

        if mode == "adventure":
            # Adventure mode: no website to audit — score purely on business quality
            opportunity = _compute_adventure_score(
                business_rating=place.get("rating"),
                review_count=place.get("review_count", 0),
            )

            lead_data = {
                "name": place.get("name"),
                "address": place.get("address"),
                "rating": place.get("rating"),
                "review_count": place.get("review_count", 0),
                "price_level": place.get("price_level"),
                "primary_type": (
                    place.get("primary_type_display") or place.get("primary_type")
                ),
                "google_maps_url": place.get("google_maps_url"),
                "has_website": False,
                "opportunity_score": opportunity,
                "status": "qualified" if opportunity >= min_opportunity_score else "below_threshold",
            }

            # Store qualified adventure leads
            if opportunity >= min_opportunity_score:
                store_url = place.get("google_maps_url") or f"no-website://{place.get('name', 'unknown')}"
                async with async_session_factory() as session:
                    prospect, created = await get_or_create_prospect(
                        session,
                        url=store_url,
                        company_name=place.get("name"),
                        industry=industry,
                        latitude=place.get("latitude"),
                        longitude=place.get("longitude"),
                        raw_data={
                            "lead_source": "auto_discovery",
                            "lead_mode": "adventure",
                            "lead_batch": batch_id,
                            "lead_score": opportunity,
                            "lead_industry": industry,
                            "lead_location": location,
                            "has_website": False,
                            "place_id": place.get("place_id"),
                            "google_rating": place.get("rating"),
                            "google_review_count": place.get("review_count", 0),
                            "google_price_level": place.get("price_level"),
                            "google_maps_url": place.get("google_maps_url"),
                            "google_address": place.get("address"),
                            "place_types": place.get("types", []),
                            "discovered_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    lead_data["prospect_id"] = str(prospect.id)
                    lead_data["stored"] = True

        else:
            # Revamp mode: audit the website
            website = place["website"]

            try:
                html, final_url, is_https, status_code = await _fetch_page(website)
            except Exception as exc:
                errors.append({
                    "name": place.get("name"),
                    "website": website,
                    "error": f"Fetch failed: {str(exc)[:100]}",
                })
                continue

            if status_code != 200:
                errors.append({
                    "name": place.get("name"),
                    "website": website,
                    "error": f"HTTP {status_code}",
                })
                continue

            quality = _score_website_quality(html, is_https)
            tech_stack = _detect_tech_stack(html)
            site_problems = _extract_site_problems(html, tech_stack, is_https)
            brand_colors = _extract_brand_colors(html)
            contact_emails = _extract_contact_emails(html)

            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", html,
                re.IGNORECASE | re.DOTALL,
            )
            page_title = title_match.group(1).strip() if title_match else None

            opportunity = _compute_opportunity_score(
                business_rating=place.get("rating"),
                review_count=place.get("review_count", 0),
                website_overall=quality["overall"],
            )

            lead_data = {
                "name": place.get("name"),
                "website": website,
                "address": place.get("address"),
                "rating": place.get("rating"),
                "review_count": place.get("review_count", 0),
                "price_level": place.get("price_level"),
                "primary_type": (
                    place.get("primary_type_display") or place.get("primary_type")
                ),
                "page_title": page_title,
                "website_scores": quality["scores"],
                "website_overall": quality["overall"],
                "site_problems": site_problems,
                "problem_count": len(site_problems),
                "tech_stack": tech_stack,
                "contact_emails": contact_emails,
                "opportunity_score": opportunity,
                "status": "qualified" if opportunity >= min_opportunity_score else "below_threshold",
            }

            if opportunity >= min_opportunity_score:
                async with async_session_factory() as session:
                    prospect, created = await get_or_create_prospect(
                        session,
                        url=website,
                        company_name=place.get("name"),
                        industry=industry,
                        contact_emails=contact_emails,
                        brand_colors=brand_colors,
                        tech_stack=tech_stack,
                        latitude=place.get("latitude"),
                        longitude=place.get("longitude"),
                        raw_data={
                            "site_problems": site_problems,
                            "lead_source": "auto_discovery",
                            "lead_mode": "revamp",
                            "lead_batch": batch_id,
                            "lead_score": opportunity,
                            "lead_industry": industry,
                            "lead_location": location,
                            "website_scores": quality["scores"],
                            "website_overall": quality["overall"],
                            "google_rating": place.get("rating"),
                            "google_review_count": place.get("review_count", 0),
                            "google_price_level": place.get("price_level"),
                            "google_maps_url": place.get("google_maps_url"),
                            "google_address": place.get("address"),
                            "place_types": place.get("types", []),
                            "price_level": place.get("price_level"),
                            "discovered_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    lead_data["prospect_id"] = str(prospect.id)
                    lead_data["stored"] = True

        leads.append(lead_data)

    # Sort by opportunity score descending
    leads.sort(
        key=lambda x: x.get("opportunity_score") or 0,
        reverse=True,
    )

    qualified = [l for l in leads if l.get("status") == "qualified"]
    below = [l for l in leads if l.get("status") == "below_threshold"]

    logger.info(
        "lead_generation_complete",
        industry=industry,
        location=location,
        mode=mode,
        batch_id=batch_id,
        total_places=len(places),
        target_count=len(target_places),
        qualified=len(qualified),
        below_threshold=len(below),
        errors=len(errors),
        skipped_existing=skipped_existing,
    )

    return json.dumps({
        "status": "completed",
        "mode": mode,
        "batch_id": batch_id,
        "search_query": query,
        "search_center": {"latitude": lat, "longitude": lng},
        "summary": {
            "total_places_found": len(places),
            "with_websites": len(with_websites),
            "without_websites": len(without_websites),
            "target_count": len(target_places),
            "qualified_leads": len(qualified),
            "below_threshold": len(below),
            "already_in_database": skipped_existing,
            "fetch_errors": len(errors),
            "min_opportunity_score": min_opportunity_score,
        },
        "qualified_leads": qualified,
        "below_threshold": below,
        "errors": errors if errors else None,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: get_lead_pipeline
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_lead_pipeline(
    industry: str | None = None,
    location: str | None = None,
    min_score: float | None = None,
    limit: int = 20,
    include_promoted: bool = False,
    mode: str | None = None,
) -> str:
    """View the lead pipeline — all auto-discovered prospects ranked by opportunity.

    Filter by industry, location, minimum opportunity score, or mode.
    Shows leads that haven't been promoted to projects yet (unless include_promoted=True).

    Args:
        industry: Filter by industry
        location: Filter by location
        min_score: Minimum opportunity score
        limit: Max leads to return (default 20)
        include_promoted: Include leads already promoted to projects
        mode: Filter by mode — "revamp" (have websites), "adventure" (no websites), or None (all)
    """
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from openclaw.models.prospect import Prospect
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with async_session_factory() as session:
        # Fetch more than requested limit since we filter in Python
        # (not all prospects are auto-discovered leads)
        fetch_limit = min(limit * 5, 500)
        stmt = (
            select(Prospect)
            .options(selectinload(Prospect.projects))
            .order_by(Prospect.created_at.desc())
            .limit(fetch_limit)
        )

        result = await session.execute(stmt)
        prospects = list(result.scalars().all())

    # Filter to auto-discovered leads
    leads: list[dict] = []
    for p in prospects:
        raw = p.raw_data or {}
        if raw.get("lead_source") != "auto_discovery":
            continue

        lead_industry = raw.get("lead_industry", "")
        lead_location = raw.get("lead_location", "")
        lead_score = raw.get("lead_score", 0)
        lead_mode = raw.get("lead_mode", "revamp")

        # Apply filters
        if industry and industry.lower() not in lead_industry.lower():
            continue
        if location and location.lower() not in lead_location.lower():
            continue
        if min_score and lead_score < min_score:
            continue
        if mode:
            if mode.lower() == "adventure" and lead_mode != "adventure":
                continue
            if mode.lower() == "revamp" and lead_mode == "adventure":
                continue

        has_project = len(p.projects) > 0
        if not include_promoted and has_project:
            continue

        lead_entry: dict = {
            "prospect_id": str(p.id),
            "company_name": p.company_name,
            "url": p.url,
            "industry": p.industry,
            "lead_mode": lead_mode,
            "opportunity_score": lead_score,
            "google_rating": raw.get("google_rating"),
            "google_review_count": raw.get("google_review_count"),
            "lead_location": lead_location,
            "lead_batch": raw.get("lead_batch"),
            "discovered_at": raw.get("discovered_at"),
            "has_project": has_project,
            "project_status": (
                p.projects[0].status if has_project else None
            ),
        }

        if lead_mode == "adventure":
            lead_entry["has_website"] = False
            lead_entry["google_address"] = raw.get("google_address")
            lead_entry["place_id"] = raw.get("place_id")
        else:
            lead_entry["website_overall"] = raw.get("website_overall")
            lead_entry["site_problems"] = raw.get("site_problems", [])[:3]
            lead_entry["contact_emails"] = p.contact_emails

        leads.append(lead_entry)

    # Sort by opportunity score
    leads.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

    # Apply limit after filtering
    leads = leads[:limit]

    return json.dumps({
        "status": "ok",
        "total_leads": len(leads),
        "filters": {
            "industry": industry,
            "location": location,
            "min_score": min_score,
            "mode": mode,
            "include_promoted": include_promoted,
        },
        "leads": leads,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: promote_lead
# ---------------------------------------------------------------------------

@mcp.tool()
async def promote_lead(
    prospect_id: str,
    auto_create_project: bool = True,
) -> str:
    """Promote an auto-discovered lead into the full website build pipeline.

    Looks up the prospect, creates a project linked to it (if auto_create_project=True),
    and returns the project details ready for the pipeline.

    For revamp leads: prospect has branding, site problems, contact info — skip deep research.
    For adventure leads: prospect has no website — run explore_business first to gather data.
    """
    import uuid as _uuid

    from openclaw.db.session import async_session_factory
    from openclaw.models.prospect import Prospect
    from openclaw.services.project_service import create_project as _create

    try:
        pid = _uuid.UUID(prospect_id)
    except ValueError:
        return json.dumps({"error": f"Invalid prospect_id: {prospect_id}"})

    async with async_session_factory() as session:
        prospect = await session.get(Prospect, pid)
        if not prospect:
            return json.dumps({"error": f"Prospect {prospect_id} not found"})

        raw = prospect.raw_data or {}
        if raw.get("lead_source") != "auto_discovery":
            return json.dumps({
                "status": "warning",
                "message": "This prospect was not auto-discovered. You can still proceed.",
                "prospect_id": prospect_id,
                "company_name": prospect.company_name,
            })

        # Check if already has a project
        from openclaw.models.project import Project
        from sqlalchemy import select

        stmt = select(Project).where(Project.prospect_id == pid)
        result = await session.execute(stmt)
        existing_project = result.scalar_one_or_none()

        if existing_project:
            return json.dumps({
                "status": "already_promoted",
                "prospect_id": prospect_id,
                "company_name": prospect.company_name,
                "project_id": str(existing_project.id),
                "project_name": existing_project.name,
                "project_status": existing_project.status,
            })

        lead_mode = raw.get("lead_mode", "revamp")
        is_adventure = lead_mode == "adventure"

        project_data: dict = {
            "prospect_id": prospect_id,
            "company_name": prospect.company_name,
            "url": prospect.url,
            "industry": prospect.industry,
            "lead_mode": lead_mode,
            "opportunity_score": raw.get("lead_score"),
            "google_rating": raw.get("google_rating"),
            "google_review_count": raw.get("google_review_count"),
        }

        if is_adventure:
            project_data["google_address"] = raw.get("google_address")
            project_data["place_id"] = raw.get("place_id")
            project_data["has_website"] = False
        else:
            project_data["contact_emails"] = prospect.contact_emails
            project_data["site_problems"] = raw.get("site_problems", [])
            project_data["website_overall"] = raw.get("website_overall")

        if auto_create_project:
            name = prospect.company_name or urlparse(prospect.url).netloc

            if is_adventure:
                brief = (
                    f"New website build for {name} (no existing website). "
                    f"Google rating: {raw.get('google_rating', 'N/A')} "
                    f"({raw.get('google_review_count', 0)} reviews). "
                    f"Address: {raw.get('google_address', 'N/A')}. "
                    f"Needs explore_business to gather photos, reviews, and details first."
                )
            else:
                brief = (
                    f"Website redesign for {name}. "
                    f"Current site scores {raw.get('website_overall', '?')}/10. "
                    f"Key problems: {'; '.join(raw.get('site_problems', [])[:3])}. "
                    f"Google rating: {raw.get('google_rating', 'N/A')} "
                    f"({raw.get('google_review_count', 0)} reviews)."
                )

            project = await _create(
                session=session,
                name=name,
                brief=brief,
            )
            # Link prospect to project
            project.prospect_id = pid
            await session.commit()
            await session.refresh(project)

            metadata = project.metadata_ or {}
            project_data["project_id"] = str(project.id)
            project_data["project_name"] = project.name
            project_data["project_slug"] = project.slug
            project_data["project_status"] = project.status
            project_data["github_repo"] = metadata.get("github_repo")
            project_data["github_url"] = metadata.get("github_url")
            project_data["vercel_project"] = metadata.get("vercel_project")

        # Update prospect metadata
        raw["promoted_at"] = datetime.now(timezone.utc).isoformat()
        prospect.raw_data = {**raw}
        await session.commit()

        if is_adventure:
            next_steps = [
                f"This business has NO existing website — run explore_business('{prospect_id}') first.",
                "explore_business will gather Google Places photos, reviews, hours, and phone number.",
                "Then use WebSearch + WebFetch to find the business on Yelp, Instagram, and Facebook for more photos and details.",
                "Synthesize brand identity (colors, fonts, tagline) from gathered data and industry.",
                "Call store_prospect to save enriched data, then proceed to pitch → design → build.",
            ]
        else:
            next_steps = [
                "The prospect already has site_problems and branding data from the lead audit.",
                "Run the pitch generation pipeline (Step 2) — skip deep research.",
                "Use store_prospect to enrich with additional data if needed.",
                "Draft outreach email with draft_email referencing the specific site problems.",
            ]

        return json.dumps({
            "status": "promoted",
            **project_data,
            "next_steps": next_steps,
        }, indent=2)


# ---------------------------------------------------------------------------
# Tool 6: batch_lead_generation
# ---------------------------------------------------------------------------

@mcp.tool()
async def batch_lead_generation(
    industries: list[str] | None = None,
    locations: list[str] | None = None,
    max_per_search: int = 5,
    min_opportunity_score: float = 2.5,
    mode: str = "revamp",
) -> str:
    """Run lead generation across multiple industries and locations in one call.

    If industries/locations are not provided, uses configured defaults from settings.
    Runs each industry+location combination and aggregates results.

    This is the tool to use for daily prospecting runs or batch discovery.

    Args:
        industries: List of industries (e.g. ["restaurant", "salon", "dentist"])
        locations: List of locations (e.g. ["Austin TX", "Dallas TX"])
        max_per_search: Max results per industry+location combo (default 5)
        min_opportunity_score: Minimum score to qualify (default 2.5)
        mode: "revamp" (businesses with websites) or "adventure" (businesses without websites)
    """
    from openclaw.config import settings

    mode = mode.lower()
    if mode not in ("revamp", "adventure"):
        return json.dumps({"status": "error", "message": f"Invalid mode: {mode}. Use 'revamp' or 'adventure'."})

    # Use defaults from config if not provided
    if not industries:
        raw = getattr(settings, "PROSPECTING_INDUSTRIES", "")
        if raw:
            industries = [i.strip() for i in raw.split(",") if i.strip()]
        else:
            return json.dumps({
                "status": "error",
                "message": (
                    "No industries provided and PROSPECTING_INDUSTRIES not configured. "
                    "Pass industries=['restaurant', 'salon'] or set the env var."
                ),
            })

    if not locations:
        raw = getattr(settings, "PROSPECTING_LOCATIONS", "")
        if raw:
            locations = [l.strip() for l in raw.split(",") if l.strip()]
        else:
            return json.dumps({
                "status": "error",
                "message": (
                    "No locations provided and PROSPECTING_LOCATIONS not configured. "
                    "Pass locations=['Austin TX'] or set the env var."
                ),
            })

    # Check daily limit
    daily_limit = getattr(settings, "PROSPECTING_DAILY_LIMIT", 50)
    total_combos = len(industries) * len(locations)
    total_max = total_combos * max_per_search
    if total_max > daily_limit:
        max_per_search = max(1, daily_limit // total_combos)
        logger.info(
            "batch_limit_adjusted",
            daily_limit=daily_limit,
            adjusted_max_per_search=max_per_search,
        )

    batch_results: list[dict] = []
    total_qualified = 0
    total_processed = 0

    for loc in locations:
        for ind in industries:
            logger.info("batch_run", industry=ind, location=loc, mode=mode)

            # Call run_lead_generation for each combo
            result_json = await run_lead_generation(
                industry=ind,
                location=loc,
                max_results=max_per_search,
                min_opportunity_score=min_opportunity_score,
                mode=mode,
            )
            result = json.loads(result_json)

            summary = result.get("summary", {})
            qualified_count = summary.get("qualified_leads", 0)
            processed_count = summary.get("target_count", 0)

            batch_results.append({
                "industry": ind,
                "location": loc,
                "mode": mode,
                "status": result.get("status"),
                "qualified_leads": qualified_count,
                "businesses_processed": processed_count,
                "top_lead": (
                    result.get("qualified_leads", [{}])[0].get("name")
                    if result.get("qualified_leads") else None
                ),
                "top_score": (
                    result.get("qualified_leads", [{}])[0].get("opportunity_score")
                    if result.get("qualified_leads") else None
                ),
            })
            total_qualified += qualified_count
            total_processed += processed_count

    if mode == "adventure":
        next_steps = [
            "Use get_lead_pipeline(mode='adventure') to view discovered businesses without websites.",
            "Use promote_lead(prospect_id) to move top leads into the build pipeline.",
            "After promoting, run explore_business(prospect_id) to gather photos, reviews, and details.",
        ]
    else:
        next_steps = [
            "Use get_lead_pipeline() to view all qualified leads ranked by score.",
            "Use promote_lead(prospect_id) to move top leads into the build pipeline.",
            "Use lookup_prospect(url) to get full details on any lead.",
        ]

    return json.dumps({
        "status": "batch_completed",
        "mode": mode,
        "total_combinations": total_combos,
        "total_businesses_processed": total_processed,
        "total_qualified_leads": total_qualified,
        "results_by_search": batch_results,
        "next_steps": next_steps,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 7: explore_business
# ---------------------------------------------------------------------------

@mcp.tool()
async def explore_business(
    prospect_id: str,
) -> str:
    """Explore a business with no website — gather photos, reviews, hours, and details
    from Google Places to build a website from scratch.

    Call this after promoting an adventure-mode lead. It enriches the prospect record
    with Google Places photos, reviews, opening hours, phone number, and editorial
    summary. After this tool returns, use WebSearch + WebFetch to find the business
    on Yelp, Instagram, and Facebook for additional photos and details.

    Args:
        prospect_id: The prospect UUID from promote_lead
    """
    import uuid as _uuid

    from openclaw.db.session import async_session_factory
    from openclaw.integrations.google_places import get_place_details, resolve_photo_urls
    from openclaw.models.prospect import Prospect

    try:
        pid = _uuid.UUID(prospect_id)
    except ValueError:
        return json.dumps({"error": f"Invalid prospect_id: {prospect_id}"})

    async with async_session_factory() as session:
        prospect = await session.get(Prospect, pid)
        if not prospect:
            return json.dumps({"error": f"Prospect {prospect_id} not found"})

        raw = prospect.raw_data or {}
        place_id = raw.get("place_id")
        if not place_id:
            return json.dumps({
                "status": "error",
                "message": "No place_id found on this prospect. explore_business requires an adventure-mode lead with Google Places data.",
            })

        # Fetch detailed place data from Google Places API (single call)
        try:
            details = await get_place_details(place_id)
        except Exception as exc:
            return json.dumps({
                "status": "error",
                "message": f"Google Places details fetch failed: {str(exc)[:200]}",
            })

        # Resolve photos from the details response (no extra API call)
        try:
            photo_urls = await resolve_photo_urls(details.get("photos", []), max_photos=10)
        except Exception as exc:
            logger.warning("explore_photos_failed", error=str(exc)[:100])
            photo_urls = []

        # Extract reviews
        reviews_raw = details.get("reviews", [])
        reviews = []
        for r in reviews_raw[:10]:
            reviews.append({
                "author": r.get("authorAttribution", {}).get("displayName", ""),
                "rating": r.get("rating"),
                "text": (r.get("text", {}).get("text", "") or "")[:500],
                "time": r.get("relativePublishTimeDescription", ""),
            })

        # Extract opening hours
        hours = {}
        regular_hours = details.get("regularOpeningHours") or details.get("currentOpeningHours")
        if regular_hours:
            for desc in regular_hours.get("weekdayDescriptions", []):
                # Format: "Monday: 9:00 AM – 9:00 PM"
                parts = desc.split(": ", 1)
                if len(parts) == 2:
                    hours[parts[0].strip()] = parts[1].strip()

        # Extract other details
        phone = details.get("nationalPhoneNumber")
        editorial = details.get("editorialSummary", {}).get("text")
        display_name = details.get("displayName", {}).get("text", prospect.company_name)

        # Enrich prospect raw_data
        enrichment = {
            "explored_at": datetime.now(timezone.utc).isoformat(),
            "google_photos": photo_urls,
            "google_reviews": reviews,
            "google_hours": hours,
            "google_phone": phone,
            "google_editorial_summary": editorial,
        }
        prospect.raw_data = {**raw, **enrichment}

        # Update top-level fields if we got new info
        if display_name and not prospect.company_name:
            prospect.company_name = display_name

        await session.commit()

        company = prospect.company_name or "the business"
        location = raw.get("google_address", raw.get("lead_location", ""))

        return json.dumps({
            "status": "explored",
            "prospect_id": prospect_id,
            "company_name": prospect.company_name,
            "google_photos_count": len(photo_urls),
            "google_photos": photo_urls[:5],
            "google_reviews_count": len(reviews),
            "google_reviews_preview": reviews[:3],
            "google_hours": hours,
            "google_phone": phone,
            "google_editorial_summary": editorial,
            "next_steps": [
                f"Google data gathered: {len(photo_urls)} photos, {len(reviews)} reviews, {'hours found' if hours else 'no hours'}.",
                f"Now use WebSearch to find more data. Search queries to try:",
                f'  1. WebSearch: "{company}" site:yelp.com {location}',
                f'  2. WebSearch: "{company}" {location} site:instagram.com',
                f'  3. WebSearch: "{company}" {location} site:facebook.com',
                f'  4. WebSearch: "{company}" {location} menu OR services OR prices',
                "For each result found, use WebFetch to extract: photos, menu/services, description, additional reviews.",
                "Then synthesize a brand identity:",
                "  - Pick 3-5 brand_colors based on industry + photo palette + review tone",
                "  - Pick Google Fonts that match the business vibe (serif=heritage, sans=modern, slab=casual)",
                "  - Write a tagline from review themes (what do customers rave about?)",
                f"Finally call store_prospect(url='{prospect.url}', brand_colors=[...], fonts=[...], "
                "social_links={...}, raw_data={yelp_photos: [...], yelp_description: '...', ...}) to save everything.",
            ],
        }, indent=2)
