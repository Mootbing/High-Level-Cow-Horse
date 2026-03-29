"""Firecrawl API client for web scraping and structured data extraction."""

from __future__ import annotations

import time
import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

# In-memory cache: url -> (timestamp, result)
_scrape_cache: dict[str, tuple[float, dict]] = {}
_crawl_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_get(cache: dict, key: str) -> dict | None:
    """Get from cache if not expired."""
    if key in cache:
        ts, result = cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            logger.info("firecrawl_cache_hit", url=key)
            return result
        del cache[key]
    return None


class FirecrawlClient:
    """Firecrawl API client for web scraping and data extraction."""

    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self) -> None:
        self.api_key = settings.FIRECRAWL_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def scrape(self, url: str, formats: list[str] | None = None) -> dict:
        """Scrape a single URL and return structured content."""
        cached = _cache_get(_scrape_cache, url)
        if cached is not None:
            return cached

        payload: dict = {
            "url": url,
            "formats": formats or ["markdown", "html"],
            "waitFor": 3000,  # Wait 3s for JS rendering (Wix, Squarespace, etc.)
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self.BASE_URL}/scrape",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()
            _scrape_cache[url] = (time.time(), result)
            return result

    async def extract(
        self, urls: list[str], schema: dict, prompt: str | None = None
    ) -> dict:
        """Extract structured data from URLs using LLM."""
        payload: dict = {
            "urls": urls,
            "schema": schema,
        }
        if prompt:
            payload["prompt"] = prompt
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/extract",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def crawl(self, url: str, max_pages: int = 5) -> dict:
        """Crawl a website starting from URL."""
        max_pages = min(max_pages, 5)  # Hard cap at 5 to conserve credits
        cached = _cache_get(_crawl_cache, url)
        if cached is not None:
            return cached

        payload = {
            "url": url,
            "limit": max_pages,
            "scrapeOptions": {
                "formats": ["markdown"],
                "waitFor": 3000,  # Wait 3s for JS rendering (Wix, Squarespace, etc.)
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/crawl",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()
            _crawl_cache[url] = (time.time(), result)
            return result


firecrawl_client = FirecrawlClient()
