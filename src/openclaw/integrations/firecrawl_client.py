"""Firecrawl API client for web scraping and structured data extraction."""

from __future__ import annotations

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()


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
        payload: dict = {
            "url": url,
            "formats": formats or ["markdown", "html"],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.BASE_URL}/scrape",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

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
        payload = {
            "url": url,
            "limit": max_pages,
            "scrapeOptions": {"formats": ["markdown"]},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/crawl",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()


firecrawl_client = FirecrawlClient()
