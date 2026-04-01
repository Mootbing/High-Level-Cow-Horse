"""Ingest tools — crawl a website and produce structured JSON pseudocode of every element."""

from __future__ import annotations

import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx
import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()

# ──────────────────────────────────────────────────────────────────────────────
# Browser headers (reused from lead_gen)
# ──────────────────────────────────────────────────────────────────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ──────────────────────────────────────────────────────────────────────────────
# Fetch helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch(url: str, timeout: int = 20) -> str:
    """Fetch a page and return raw HTML. Tries httpx first, Playwright fallback."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers=_BROWSER_HEADERS,
        ) as client:
            resp = await client.get(url)
            html = resp.text[:120_000]  # generous cap
            html_lower = html.lower()
            is_blocked = (
                resp.status_code in (403, 503)
                or "cf-challenge" in html_lower
                or "just a moment" in html_lower
                or "checking your browser" in html_lower
            )
            if not is_blocked and resp.status_code == 200:
                return html
    except Exception:
        pass

    # Playwright fallback
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(f"Site blocked and Playwright unavailable: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            return (await page.content())[:120_000]
        finally:
            await browser.close()


def _same_domain(base_url: str, href: str) -> bool:
    """Check if href is on the same domain as base_url."""
    base_host = urlparse(base_url).netloc.removeprefix("www.")
    href_host = urlparse(href).netloc.removeprefix("www.")
    return href_host == base_host or href_host == ""


def _discover_subpage_urls(html: str, base_url: str, max_pages: int = 4) -> list[str]:
    """Find internal nav links worth crawling, prioritized by importance."""
    link_re = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)
    all_hrefs = link_re.findall(html)

    # Priority keywords for subpage discovery
    priority = ["about", "services", "programs", "contact", "pricing",
                "menu", "team", "portfolio", "gallery", "lodging",
                "rooms", "classes", "faq", "testimonials"]

    seen: set[str] = set()
    scored: list[tuple[int, str]] = []

    for href in all_hrefs:
        full = urljoin(base_url, href).split("#")[0].split("?")[0].rstrip("/")
        if full in seen or full == base_url.rstrip("/"):
            continue
        if not _same_domain(base_url, full):
            continue
        if not full.startswith("http"):
            continue
        # Skip assets, files
        ext = full.rsplit(".", 1)[-1].lower() if "." in full.split("/")[-1] else ""
        if ext in ("jpg", "jpeg", "png", "gif", "svg", "pdf", "css", "js", "ico"):
            continue
        seen.add(full)

        href_lower = full.lower()
        score = 0
        for i, kw in enumerate(priority):
            if kw in href_lower:
                score = len(priority) - i  # higher priority = higher score
                break
        scored.append((score, full))

    scored.sort(key=lambda x: -x[0])
    return [url for _, url in scored[:max_pages]]


# ──────────────────────────────────────────────────────────────────────────────
# HTML Structure Parser
# ──────────────────────────────────────────────────────────────────────────────

# Semantic landmark tags that define sections
_LANDMARK_TAGS = {"header", "nav", "main", "section", "article", "aside", "footer"}
# Tags we skip entirely
_SKIP_TAGS = {"script", "style", "noscript", "svg", "path", "defs", "template", "iframe"}
# Section-suggesting class/id patterns
_SECTION_PATTERNS = re.compile(
    r"(hero|banner|feature|service|program|testimonial|review|pricing|price|"
    r"contact|about|team|staff|gallery|portfolio|stats|counter|cta|"
    r"call.?to.?action|faq|footer|header|nav|menu|lodging|room|class)",
    re.IGNORECASE,
)

# Maps detected patterns to section types
_SECTION_TYPE_MAP = {
    "hero": "hero", "banner": "hero",
    "feature": "features", "service": "features", "program": "features",
    "testimonial": "testimonials", "review": "testimonials",
    "pricing": "pricing", "price": "pricing",
    "contact": "contact",
    "about": "content", "team": "team", "staff": "team",
    "gallery": "gallery", "portfolio": "gallery",
    "stats": "stats", "counter": "stats",
    "cta": "cta", "call": "cta",
    "faq": "faq",
    "footer": "footer", "header": "header",
    "nav": "header", "menu": "header",
    "lodging": "features", "room": "features",
    "class": "features",
}


class _StructureParser(HTMLParser):
    """Walk HTML DOM top-to-bottom, building structured section data."""

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url

        # Output
        self.sections: list[dict] = []
        self.all_images: list[dict] = []
        self.all_links: list[dict] = []
        self.nav_links: list[dict] = []
        self.social_links: dict[str, str] = {}
        self.contact: dict[str, str] = {}
        self.logo_candidates: list[dict] = []
        self.fonts_raw: list[str] = []  # raw font-family strings
        self.google_fonts: list[str] = []  # from Google Fonts link
        self.colors_raw: list[str] = []  # hex colors from inline styles
        self.meta: dict[str, str] = {}  # meta tags (description, og:title, etc.)

        # Parser state
        self._tag_stack: list[str] = []
        self._skip_depth: int = 0  # > 0 means we're inside a skip tag
        self._in_head: bool = False
        self._current_section: dict | None = None
        self._section_order: int = 0
        self._text_parts: list[str] = []  # text accumulator for current element
        self._current_tag: str | None = None
        self._current_attrs: dict[str, str] = {}
        self._pending_elements: list[dict] = []  # elements for current section

    def _attrs_dict(self, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {k: v or "" for k, v in attrs}

    # Tags that can define section boundaries (block-level only)
    _SECTION_BOUNDARY_TAGS = {
        "header", "footer", "nav", "main", "section", "article", "aside",
        "div", "form",
    }

    def _classify_section(self, tag: str, attrs: dict[str, str]) -> str | None:
        """Determine section type from tag name and attributes.

        Only block-level tags can start new sections — inline elements (a, span,
        button, img) never trigger section boundaries even if their class contains
        a section keyword like 'cta'.
        """
        # Only block-level tags can be section boundaries
        if tag not in self._SECTION_BOUNDARY_TAGS:
            return None

        # Direct landmark mapping
        if tag == "header":
            return "header"
        if tag == "footer":
            return "footer"
        if tag == "nav":
            return "header"  # nav is part of header

        # Check class and id for section patterns
        class_id = f"{attrs.get('class', '')} {attrs.get('id', '')}".lower()
        match = _SECTION_PATTERNS.search(class_id)
        if match:
            keyword = match.group(1).lower().replace("-", "").replace("_", "")
            for prefix, stype in _SECTION_TYPE_MAP.items():
                if keyword.startswith(prefix):
                    return stype

        # Generic section/article
        if tag in ("section", "article"):
            return "content"

        return None

    def _start_section(self, section_type: str, section_id: str):
        """Finalize current section and start a new one."""
        self._finalize_section()
        self._current_section = {
            "id": section_id,
            "type": section_type,
            "order": self._section_order,
            "elements": {},
        }
        self._section_order += 1
        self._pending_elements = []

    def _finalize_section(self):
        """Save current section if it has content."""
        if self._current_section and self._pending_elements:
            # Build elements dict from pending
            elements = {}
            heading_count = 0
            para_count = 0
            card_items: list[dict] = []
            link_items: list[dict] = []
            image_items: list[dict] = []

            for el in self._pending_elements:
                etype = el.get("_type", "")
                if etype == "heading":
                    key = "heading" if heading_count == 0 else f"subheading"
                    if heading_count <= 1:
                        elements[key] = {
                            "text": el["text"],
                            "tag": el["tag"],
                        }
                    heading_count += 1
                elif etype == "paragraph":
                    if "paragraphs" not in elements:
                        elements["paragraphs"] = []
                    elements["paragraphs"].append(el["text"])
                    para_count += 1
                elif etype == "image":
                    image_items.append({"src": el["src"], "alt": el.get("alt", "")})
                elif etype == "link":
                    if el.get("is_cta"):
                        elements["cta"] = {"text": el["text"], "link": el["href"]}
                    else:
                        link_items.append({"text": el["text"], "link": el["href"]})
                elif etype == "form":
                    elements["form_fields"] = el.get("fields", [])
                elif etype == "list_item":
                    card_items.append(el.get("data", {}))

            if image_items:
                if len(image_items) == 1:
                    elements["image"] = image_items[0]
                else:
                    elements["images"] = image_items
            if link_items:
                elements["links"] = link_items
            if card_items:
                elements["items"] = card_items

            self._current_section["elements"] = elements
            self.sections.append(self._current_section)

        self._current_section = None
        self._pending_elements = []

    def _add_element(self, el: dict):
        """Add element to current section, creating a default section if needed."""
        if self._current_section is None:
            # Auto-create a content section
            self._start_section("content", f"section-{self._section_order}")
        self._pending_elements.append(el)

    # ── HTMLParser callbacks ──

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag = tag.lower()
        self._tag_stack.append(tag)
        ad = self._attrs_dict(attrs)

        # Track head section
        if tag == "head":
            self._in_head = True
            return

        # Skip tags
        if tag in _SKIP_TAGS or self._skip_depth > 0:
            self._skip_depth += 1
            return

        # ── Head-only processing (meta, link) ──
        if self._in_head:
            if tag == "meta":
                name = ad.get("name", ad.get("property", "")).lower()
                content = ad.get("content", "")
                if name and content:
                    self.meta[name] = content
            elif tag == "link":
                href = ad.get("href", "")
                # Google Fonts detection
                if "fonts.googleapis.com" in href or "fonts.gstatic.com" in href:
                    self._extract_google_fonts(href)
                # Typekit / Adobe Fonts
                if "use.typekit.net" in href:
                    self.fonts_raw.append("Adobe Fonts (Typekit)")
            return

        # ── Extract inline style colors and fonts ──
        style = ad.get("style", "")
        if style:
            self._extract_inline_style(style)

        # ── Section detection ──
        section_type = self._classify_section(tag, ad)
        if section_type:
            sid = ad.get("id", "") or f"{section_type}-{self._section_order}"
            self._start_section(section_type, sid)

        # ── Element extraction ──
        self._current_tag = tag
        self._current_attrs = ad
        self._text_parts = []

        # Images
        if tag == "img":
            src = ad.get("src", ad.get("data-src", ad.get("data-lazy-src", "")))
            if src:
                src = urljoin(self.base_url, src)
                alt = ad.get("alt", "")
                img = {"src": src, "alt": alt}
                self.all_images.append(img)
                self._add_element({"_type": "image", "src": src, "alt": alt})

                # Logo detection
                class_id = f"{ad.get('class', '')} {ad.get('id', '')} {alt}".lower()
                if "logo" in class_id or "brand" in class_id:
                    self.logo_candidates.append(img)

        # Links
        if tag == "a":
            href = ad.get("href", "")
            if href:
                full_href = urljoin(self.base_url, href)
                self._detect_social(full_href)
                self._detect_contact(href)

                # Track nav links
                if "nav" in [t for t in self._tag_stack]:
                    pass  # will be captured in handle_endtag

        # Form fields
        if tag in ("input", "textarea", "select"):
            input_type = ad.get("type", "text")
            name = ad.get("name", "")
            placeholder = ad.get("placeholder", "")
            label = ad.get("aria-label", placeholder)
            if name and input_type not in ("hidden", "submit"):
                self._add_element({
                    "_type": "form",
                    "fields": [{"type": input_type, "name": name, "label": label}],
                })

    def handle_endtag(self, tag: str):
        tag = tag.lower()

        if tag == "head":
            self._in_head = False

        if self._skip_depth > 0:
            self._skip_depth -= 1
            if tag in self._tag_stack:
                self._tag_stack.pop()
            return

        # Flush accumulated text
        text = " ".join(self._text_parts).strip()
        text = re.sub(r"\s+", " ", text)

        if text and self._current_tag:
            # Headings
            if self._current_tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._add_element({
                    "_type": "heading",
                    "text": text,
                    "tag": self._current_tag,
                })
            # Paragraphs (only substantial ones)
            elif self._current_tag == "p" and len(text) > 10:
                self._add_element({"_type": "paragraph", "text": text})
            # Links
            elif self._current_tag == "a":
                href = self._current_attrs.get("href", "")
                full_href = urljoin(self.base_url, href)
                link_data = {"text": text, "href": full_href}
                self.all_links.append(link_data)

                # CTA detection
                class_id = f"{self._current_attrs.get('class', '')} {self._current_attrs.get('id', '')}".lower()
                cta_keywords = {"book", "start", "get started", "contact", "sign up",
                                "schedule", "plan", "reserve", "order", "buy", "shop"}
                is_cta = (
                    "btn" in class_id or "button" in class_id or "cta" in class_id
                    or any(kw in text.lower() for kw in cta_keywords)
                )

                if is_cta:
                    self._add_element({"_type": "link", "text": text, "href": full_href, "is_cta": True})

                # Nav link
                if "nav" in [t for t in self._tag_stack]:
                    self.nav_links.append({"text": text, "link": full_href})
            # Button
            elif self._current_tag == "button":
                self._add_element({
                    "_type": "link",
                    "text": text,
                    "href": "#",
                    "is_cta": True,
                })
            # List items (potential cards/features)
            elif self._current_tag == "li" and len(text) > 5:
                self._add_element({"_type": "list_item", "data": {"text": text}})

        # Pop tag stack
        if tag in self._tag_stack:
            self._tag_stack.remove(tag)
        self._text_parts = []

    def handle_data(self, data: str):
        if self._in_head or self._skip_depth > 0:
            return
        stripped = data.strip()
        if stripped:
            self._text_parts.append(stripped)

    def finish(self):
        """Finalize the last open section."""
        self._finalize_section()

    # ── Extraction helpers ──

    def _extract_google_fonts(self, href: str):
        """Extract font family names from a Google Fonts URL."""
        # Format: fonts.googleapis.com/css2?family=Jost:wght@400;700&family=Poppins:wght@300;400
        # or: fonts.googleapis.com/css?family=Playfair+Display|Open+Sans
        family_re = re.compile(r"family=([^&;]+)", re.IGNORECASE)
        matches = family_re.findall(href)
        for match in matches:
            # Handle multiple families separated by |
            for fam in match.split("|"):
                # Remove weight/style suffixes
                name = fam.split(":")[0].replace("+", " ").strip()
                if name and name not in self.google_fonts:
                    self.google_fonts.append(name)

    def _extract_inline_style(self, style: str):
        """Extract colors and fonts from inline CSS."""
        # Colors
        hex_re = re.compile(r"#([0-9a-fA-F]{3,6})\b")
        for m in hex_re.findall(style):
            if len(m) in (3, 6):
                self.colors_raw.append(f"#{m.lower()}")

        # rgb/rgba
        rgb_re = re.compile(r"rgba?\((\d+),\s*(\d+),\s*(\d+)")
        for r, g, b in rgb_re.findall(style):
            hex_val = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            self.colors_raw.append(hex_val)

        # Fonts
        font_re = re.compile(r"font-family:\s*([^;]+)", re.IGNORECASE)
        for m in font_re.findall(style):
            self.fonts_raw.append(m.strip().strip("'\""))

    def _detect_social(self, url: str):
        """Detect social media links."""
        platforms = {
            "instagram.com": "instagram",
            "facebook.com": "facebook",
            "twitter.com": "twitter",
            "x.com": "twitter",
            "youtube.com": "youtube",
            "linkedin.com": "linkedin",
            "tiktok.com": "tiktok",
            "pinterest.com": "pinterest",
            "yelp.com": "yelp",
        }
        url_lower = url.lower()
        for domain, platform in platforms.items():
            if domain in url_lower and platform not in self.social_links:
                self.social_links[platform] = url

    def _detect_contact(self, href: str):
        """Detect contact info from link href."""
        if href.startswith("tel:"):
            phone = href[4:].strip()
            if phone:
                self.contact["phone"] = phone
        elif href.startswith("mailto:"):
            email = href[7:].strip().split("?")[0]
            if email and "@" in email:
                self.contact["email"] = email


# ──────────────────────────────────────────────────────────────────────────────
# CSS extraction (from <style> blocks and linked stylesheets)
# ──────────────────────────────────────────────────────────────────────────────

def _extract_css_data(html: str) -> tuple[list[str], list[str]]:
    """Extract font families and colors from all <style> blocks in HTML."""
    fonts: list[str] = []
    colors: list[str] = []

    # Find all <style> blocks
    style_re = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
    for block in style_re.findall(html):
        # Font families
        font_re = re.compile(r"font-family:\s*([^;}{]+)", re.IGNORECASE)
        for match in font_re.findall(block):
            for font in match.split(","):
                name = font.strip().strip("'\"")
                if name and name.lower() not in ("inherit", "initial", "unset", "sans-serif",
                                                   "serif", "monospace", "system-ui", "cursive",
                                                   "fantasy", "-apple-system", "BlinkMacSystemFont"):
                    if name not in fonts:
                        fonts.append(name)

        # Hex colors
        hex_re = re.compile(r"#([0-9a-fA-F]{3,6})\b")
        for m in hex_re.findall(block):
            if len(m) in (3, 6):
                colors.append(f"#{m.lower()}")

        # RGB colors
        rgb_re = re.compile(r"rgba?\((\d+),\s*(\d+),\s*(\d+)")
        for r, g, b in rgb_re.findall(block):
            hex_val = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            colors.append(hex_val)

    return fonts, colors


def _compute_brand_colors(raw_colors: list[str]) -> dict:
    """Frequency-analyze raw colors to determine primary/secondary/accent."""
    skip = {"#000", "#fff", "#000000", "#ffffff", "#333", "#666", "#999",
            "#ccc", "#ddd", "#eee", "#333333", "#666666", "#999999",
            "#cccccc", "#dddddd", "#eeeeee", "#f5f5f5", "#fafafa",
            "#e5e5e5", "#d4d4d4", "#a3a3a3", "#737373", "#525252",
            "#404040", "#262626", "#171717"}

    # Normalize 3-char to 6-char
    normalized: list[str] = []
    for c in raw_colors:
        c = c.lower()
        if len(c) == 4:  # #abc → #aabbcc
            c = f"#{c[1]*2}{c[2]*2}{c[3]*2}"
        if c not in skip:
            normalized.append(c)

    # Count frequencies
    freq: dict[str, int] = {}
    for c in normalized:
        freq[c] = freq.get(c, 0) + 1

    ranked = sorted(freq.items(), key=lambda x: -x[1])
    all_colors = [c for c, _ in ranked[:10]]

    result: dict = {"all_extracted": all_colors}
    if len(all_colors) >= 1:
        result["primary"] = all_colors[0]
    if len(all_colors) >= 2:
        result["secondary"] = all_colors[1]
    if len(all_colors) >= 3:
        result["accent"] = all_colors[2]

    return result


def _compute_brand_fonts(
    google_fonts: list[str],
    css_fonts: list[str],
    inline_fonts: list[str],
) -> dict:
    """Determine heading and body fonts from all detected font sources."""
    # Google Fonts are highest confidence
    all_fonts = []
    seen: set[str] = set()
    for f in google_fonts + css_fonts + inline_fonts:
        if f not in seen:
            seen.add(f)
            all_fonts.append(f)

    result: dict = {"all_detected": all_fonts}

    if len(all_fonts) >= 1:
        result["heading"] = {
            "family": all_fonts[0],
            "weight": "700",
            "source": "google_fonts" if all_fonts[0] in google_fonts else "css",
        }
    if len(all_fonts) >= 2:
        result["body"] = {
            "family": all_fonts[1],
            "weight": "400",
            "source": "google_fonts" if all_fonts[1] in google_fonts else "css",
        }
    elif len(all_fonts) == 1:
        result["body"] = result["heading"].copy()
        result["body"]["weight"] = "400"

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Contact extraction (phone, email, address from full HTML text)
# ──────────────────────────────────────────────────────────────────────────────

def _extract_contact_from_text(html: str) -> dict[str, str]:
    """Extract phone numbers, emails, and addresses from page text."""
    contact: dict[str, str] = {}

    # Emails
    email_re = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    skip_domains = {"example.com", "sentry.io", "wixpress.com", "wordpress.org",
                    "schema.org", "w3.org", "googleusercontent.com"}
    for m in email_re.findall(html):
        domain = m.lower().split("@")[1]
        if domain not in skip_domains:
            contact["email"] = m.lower()
            break

    # Phone (international format)
    phone_re = re.compile(r"[\+]?[\d\s\-().]{10,20}")
    tel_re = re.compile(r'href=["\']tel:([^"\']+)["\']')
    for m in tel_re.findall(html):
        contact["phone"] = m.strip()
        break

    return contact


# ──────────────────────────────────────────────────────────────────────────────
# Main ingest pipeline
# ──────────────────────────────────────────────────────────────────────────────

async def _ingest_single_page(url: str) -> tuple[dict, _StructureParser]:
    """Ingest a single page and return (page_data, parser_with_metadata)."""
    html = await _fetch(url)

    parser = _StructureParser(url)
    parser.feed(html)
    parser.finish()

    # Extract CSS-level data
    css_fonts, css_colors = _extract_css_data(html)

    # Merge CSS data into parser
    parser.fonts_raw.extend(css_fonts)
    parser.colors_raw.extend(css_colors)

    # Build page data
    page_data = {
        "url": url,
        "title": parser.meta.get("og:title", parser.meta.get("title", "")),
        "description": parser.meta.get("description", parser.meta.get("og:description", "")),
        "sections": parser.sections,
    }

    return page_data, parser


def _build_brand(parsers: list[_StructureParser], pages: list[dict]) -> dict:
    """Aggregate data from all page parsers into a unified brand object."""
    # Merge all data across pages
    all_google_fonts: list[str] = []
    all_css_fonts: list[str] = []
    all_inline_fonts: list[str] = []
    all_colors: list[str] = []
    all_images: list[dict] = []
    social: dict[str, str] = {}
    contact: dict[str, str] = {}
    logo_candidates: list[dict] = []
    nav_links: list[dict] = []
    meta: dict[str, str] = {}

    for p in parsers:
        all_google_fonts.extend(p.google_fonts)
        all_inline_fonts.extend(p.fonts_raw)
        all_colors.extend(p.colors_raw)
        all_images.extend(p.all_images)
        social.update(p.social_links)
        contact.update(p.contact)
        logo_candidates.extend(p.logo_candidates)
        nav_links.extend(p.nav_links)
        meta.update(p.meta)

    # Deduplicate
    seen_fonts: set[str] = set()
    deduped_google: list[str] = []
    for f in all_google_fonts:
        if f not in seen_fonts:
            seen_fonts.add(f)
            deduped_google.append(f)

    brand: dict = {
        "name": meta.get("og:site_name", meta.get("og:title", "")),
        "tagline": meta.get("description", meta.get("og:description", "")),
        "colors": _compute_brand_colors(all_colors),
        "fonts": _compute_brand_fonts(deduped_google, all_css_fonts, all_inline_fonts),
        "logo": {},
        "social": social,
        "contact": contact,
        "images": [],
        "nav": nav_links,
    }

    # Logo: best candidate
    if logo_candidates:
        brand["logo"] = {"primary": logo_candidates[0]}
        if len(logo_candidates) > 1:
            brand["logo"]["variants"] = logo_candidates[1:]

    # Images: deduplicate by src, add context from sections
    seen_srcs: set[str] = set()
    for img in all_images:
        src = img.get("src", "")
        if src and src not in seen_srcs:
            seen_srcs.add(src)
            brand["images"].append(img)
    brand["images"] = brand["images"][:30]  # cap at 30

    return brand


# ──────────────────────────────────────────────────────────────────────────────
# MCP Tools
# ──────────────────────────────────────────────────────────────────────────────

def _storage_dir(project_name: str) -> str:
    """Project storage directory (parent of /site)."""
    safe_name = os.path.basename(project_name.replace("..", "").strip("/")) or "unnamed"
    return os.path.join(settings.STORAGE_PATH, safe_name)


@mcp.tool()
async def ingest_website(
    url: str,
    project_name: str,
    max_subpages: int = 4,
) -> str:
    """Crawl a website and produce structured JSON pseudocode.

    Walks the DOM top-to-bottom for each page, extracting every element in
    chronological order: headers, headings, paragraphs, images, links, buttons,
    forms. Also extracts brand identity: colors (frequency-analyzed), fonts
    (Google Fonts + CSS), logos, social links, and contact info.

    Returns two objects:
    - site_structure: chronological top-to-bottom map of every element on every page
    - brand: extracted brand identity (colors, fonts, logos, contact, social)

    The results are stored in the prospect's raw_data and written to
    {STORAGE_PATH}/{project_name}/ingest.json for the build phase.
    """
    logger.info("ingest_start", url=url, project=project_name)

    # Crawl homepage
    pages: list[dict] = []
    parsers: list[_StructureParser] = []

    try:
        home_page, home_parser = await _ingest_single_page(url)
        pages.append(home_page)
        parsers.append(home_parser)
    except Exception as exc:
        logger.error("ingest_homepage_failed", url=url, error=str(exc)[:300])
        return json.dumps({
            "status": "error",
            "message": f"Failed to fetch homepage: {str(exc)[:200]}",
        })

    # Discover and crawl subpages
    homepage_html = await _fetch(url)  # re-fetch for link discovery (cheap, cached)
    subpage_urls = _discover_subpage_urls(homepage_html, url, max_subpages)

    for sub_url in subpage_urls:
        try:
            sub_page, sub_parser = await _ingest_single_page(sub_url)
            pages.append(sub_page)
            parsers.append(sub_parser)
            logger.info("ingest_subpage", url=sub_url, sections=len(sub_page["sections"]))
        except Exception as exc:
            logger.warning("ingest_subpage_failed", url=sub_url, error=str(exc)[:200])

    # Build unified brand object
    brand = _build_brand(parsers, pages)

    # Also extract contact from full text
    text_contact = _extract_contact_from_text(homepage_html)
    brand["contact"] = {**text_contact, **brand["contact"]}  # parser results take priority

    site_structure = {"pages": pages}

    # Write to filesystem
    storage = _storage_dir(project_name)
    os.makedirs(storage, exist_ok=True)
    ingest_path = os.path.join(storage, "ingest.json")
    with open(ingest_path, "w") as f:
        json.dump({"site_structure": site_structure, "brand": brand}, f, indent=2)

    # Store in prospect record
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.services.prospect_service import get_or_create_prospect

        async with async_session_factory() as session:
            prospect, created = await get_or_create_prospect(session, url=url)
            existing_raw = prospect.raw_data or {}
            prospect.raw_data = {
                **existing_raw,
                "site_structure": site_structure,
                "brand": brand,
            }
            # Also update top-level fields
            if brand.get("name"):
                prospect.company_name = prospect.company_name or brand["name"]
            if brand.get("colors", {}).get("all_extracted"):
                prospect.brand_colors = brand["colors"]["all_extracted"][:5]
            if brand.get("fonts", {}).get("all_detected"):
                prospect.fonts = brand["fonts"]["all_detected"][:4]
            if brand.get("logo", {}).get("primary", {}).get("src"):
                prospect.logo_url = prospect.logo_url or brand["logo"]["primary"]["src"]
            if brand.get("social"):
                prospect.social_links = {**(prospect.social_links or {}), **brand["social"]}
            if brand.get("contact", {}).get("email"):
                existing_emails = prospect.contact_emails or []
                email = brand["contact"]["email"]
                if email not in existing_emails:
                    prospect.contact_emails = existing_emails + [email]

            await session.commit()
            logger.info("ingest_stored", prospect_id=str(prospect.id), pages=len(pages))
    except Exception as exc:
        logger.warning("ingest_db_store_failed", error=str(exc)[:300])

    # Summary
    total_sections = sum(len(p["sections"]) for p in pages)
    total_images = len(brand.get("images", []))

    return json.dumps({
        "status": "complete",
        "pages_crawled": len(pages),
        "total_sections": total_sections,
        "total_images": total_images,
        "fonts_detected": brand.get("fonts", {}).get("all_detected", []),
        "colors_detected": brand.get("colors", {}).get("all_extracted", [])[:5],
        "social_links": list(brand.get("social", {}).keys()),
        "logo_found": bool(brand.get("logo", {}).get("primary")),
        "ingest_path": ingest_path,
        "site_structure": site_structure,
        "brand": brand,
    })


@mcp.tool()
async def store_site_structure(
    project_name: str,
    site_structure: str,
    brand: str,
) -> str:
    """Store refined JSON pseudocode and brand data after agent review.

    The agent calls ingest_website first (automated HTML parsing), then uses
    WebFetch to verify/refine content the parser may have missed (JS-rendered
    content, dynamic elements, etc.), and calls this to store the final version.

    site_structure and brand are JSON strings matching the ingest schema.
    Overwrites the automated ingest data with the agent-refined version.
    """
    try:
        structure_obj = json.loads(site_structure)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid site_structure JSON: {e}"})

    try:
        brand_obj = json.loads(brand)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid brand JSON: {e}"})

    # Write to filesystem
    storage = _storage_dir(project_name)
    os.makedirs(storage, exist_ok=True)
    ingest_path = os.path.join(storage, "ingest.json")
    with open(ingest_path, "w") as f:
        json.dump({"site_structure": structure_obj, "brand": brand_obj}, f, indent=2)

    # Update prospect record if we can find it
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.models.prospect import Prospect
        from openclaw.services.project_service import find_project_by_name
        from sqlalchemy import select

        async with async_session_factory() as session:
            # Find prospect via project
            project = await find_project_by_name(session, project_name)

            if project and project.prospect_id:
                stmt = select(Prospect).where(Prospect.id == project.prospect_id)
                result = await session.execute(stmt)
                prospect = result.scalars().first()
                if prospect:
                    existing_raw = prospect.raw_data or {}
                    prospect.raw_data = {
                        **existing_raw,
                        "site_structure": structure_obj,
                        "brand": brand_obj,
                    }
                    await session.commit()
    except Exception as exc:
        logger.warning("store_site_structure_db_failed", error=str(exc)[:300])

    logger.info("site_structure_stored", project=project_name, path=ingest_path)
    return json.dumps({
        "status": "stored",
        "path": ingest_path,
        "pages": len(structure_obj.get("pages", [])),
        "sections": sum(len(p.get("sections", [])) for p in structure_obj.get("pages", [])),
    })
