"""Shared website audit logic — fetch, score, and analyze websites.

Extracted from lead_gen.py so both MCP tools and the audit worker can reuse it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

import httpx
import structlog

logger = structlog.get_logger()

# Browser-like headers to avoid bot detection on simple httpx requests
BROWSER_HEADERS = {
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


@dataclass
class AuditResult:
    """Structured result from a website audit."""

    url: str
    final_url: str
    page_title: str | None
    meta_description: str | None
    is_https: bool
    tech_stack: list[str]
    scores: dict[str, int]
    overall: float
    site_problems: list[str]
    brand_colors: list[str]
    contact_emails: list[str]
    content_metrics: dict[str, float | int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


async def fetch_page(url: str, timeout: int = 20) -> tuple[str, str, bool, int]:
    """Fetch a webpage with bot-detection bypass.

    Tries httpx with browser headers first. If blocked (403/captcha),
    falls back to Playwright headless browser.

    Returns (html, final_url, is_https, status_code).
    Raises Exception if both methods fail.
    """
    # Attempt 1: httpx with browser headers (fast)
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers=BROWSER_HEADERS,
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
# Helpers
# ---------------------------------------------------------------------------


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication."""
    parsed = urlparse(url.lower().rstrip("/"))
    host = parsed.netloc or parsed.path
    host = host.removeprefix("www.")
    return host


def detect_tech_stack(html: str) -> list[str]:
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


def extract_site_problems(html: str, tech_stack: list[str], is_https: bool) -> list[str]:
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


def score_website_quality(html: str, is_https: bool) -> dict:
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


def extract_brand_colors(html: str) -> list[str]:
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


def extract_contact_emails(html: str) -> list[str]:
    """Extract email addresses from HTML."""
    email_pattern = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    matches = email_pattern.findall(html)
    # Deduplicate, skip common non-business emails
    skip_domains = {"example.com", "sentry.io", "wixpress.com",
                    "wordpress.org", "schema.org", "w3.org"}
    skip_prefixes = {"info", "contact", "hello", "support", "admin", "office",
                     "mail", "enquiries", "inquiries", "sales", "help",
                     "noreply", "no-reply"}
    emails: list[str] = []
    seen: set[str] = set()
    for email in matches:
        lower = email.lower()
        domain = lower.split("@")[1]
        prefix = lower.split("@")[0]
        if domain in skip_domains or lower in seen or prefix in skip_prefixes:
            continue
        seen.add(lower)
        emails.append(lower)
        if len(emails) >= 5:
            break
    return emails


# ---------------------------------------------------------------------------
# High-level audit function
# ---------------------------------------------------------------------------


async def run_audit(url: str) -> AuditResult:
    """Full audit pipeline: fetch -> score -> extract problems -> return structured result."""
    html, final_url, is_https, status_code = await fetch_page(url)

    if status_code != 200:
        raise Exception(f"Website returned HTTP {status_code}")

    quality = score_website_quality(html, is_https)
    tech_stack = detect_tech_stack(html)
    site_problems = extract_site_problems(html, tech_stack, is_https)
    brand_colors = extract_brand_colors(html)
    contact_emails = extract_contact_emails(html)

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else None

    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        html, re.IGNORECASE,
    )
    meta_description = desc_match.group(1).strip() if desc_match else None

    return AuditResult(
        url=url,
        final_url=final_url,
        page_title=page_title,
        meta_description=meta_description,
        is_https=is_https,
        tech_stack=tech_stack,
        scores=quality["scores"],
        overall=quality["overall"],
        site_problems=site_problems,
        brand_colors=brand_colors,
        contact_emails=contact_emails,
        content_metrics={
            "html_size_kb": round(len(html) / 1024, 1),
            "image_count": html.lower().count("<img"),
            "link_count": html.lower().count("<a "),
        },
    )
