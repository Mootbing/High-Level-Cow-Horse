"""Integration tests for lead generation tools — mocked external APIs."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PLACES = [
    {
        "name": "Joe's BBQ",
        "website": "https://www.joesbbq.com",
        "address": "123 Main St, Austin, TX 78701",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "rating": 4.7,
        "review_count": 342,
        "price_level": "PRICE_LEVEL_MODERATE",
        "types": ["restaurant", "food"],
        "primary_type": "restaurant",
        "primary_type_display": "Restaurant",
        "google_maps_url": "https://maps.google.com/?cid=123",
    },
    {
        "name": "Bland Burgers",
        "website": "https://blandburgers.com",
        "address": "456 Oak Ave, Austin, TX 78702",
        "latitude": 30.2700,
        "longitude": -97.7400,
        "rating": 3.2,
        "review_count": 15,
        "price_level": "PRICE_LEVEL_INEXPENSIVE",
        "types": ["restaurant"],
        "primary_type": "restaurant",
        "primary_type_display": "Restaurant",
        "google_maps_url": "https://maps.google.com/?cid=456",
    },
    {
        "name": "No Website Cafe",
        "address": "789 Elm St, Austin, TX 78703",
        "latitude": 30.2750,
        "longitude": -97.7500,
        "rating": 4.0,
        "review_count": 50,
        "website": None,  # No website
        "types": ["cafe"],
        "primary_type": "cafe",
    },
]

MOCK_HTML_BAD = """
<html>
<head><title>Joe's BBQ - Best BBQ in Austin</title></head>
<body>
<link rel="stylesheet" href="/wp-content/themes/starter/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin1/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin2/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin3/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin4/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin5/style.css">
<link rel="stylesheet" href="/wp-content/plugins/plugin6/style.css">
<div class="menu">
<a href="/">Home</a><a href="/menu">Menu</a><a href="/about">About</a>
</div>
<p>Welcome to Joe's BBQ</p>
<p>We serve the best BBQ in Austin</p>
<img src="/hero.jpg">
<span>info@joesbbq.com</span>
<style>.header { color: #ff5733; background: #2a9d8f; }</style>
<footer>&copy; 2020 Joe's BBQ</footer>
</body>
</html>
"""

MOCK_HTML_GOOD = """
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Modern burger restaurant in Austin">
<title>Bland Burgers</title>
<link href="https://fonts.googleapis.com/css?family=Inter" rel="stylesheet">
</head>
<body>
<nav><a href="/">Home</a><a href="/menu">Menu</a></nav>
<header><h1>Bland Burgers</h1></header>
<script src="/_next/static/chunks/main.js"></script>
<p>Fresh burgers daily</p>
<p>Our customers love us</p>
<p>testimonial: "Best burgers ever!" - John D.</p>
<img src="/a.png"><img src="/b.png"><img src="/c.png">
<a href="tel:5551234">Call us</a>
<a href="mailto:info@blandburgers.com">Email</a>
<button>Book a Table</button>
<button>Order Online</button>
<style>
@media (max-width: 768px) { .flex { display: flex; } .grid { display: grid; } }
.hero { background: linear-gradient(#000, #333); animation: fade 1s; }
</style>
<footer>&copy; 2026 Bland Burgers</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Helper function tests (no mocking needed)
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_normalize_url(self):
        from openclaw.mcp_server.tools.lead_gen import _normalize_url

        assert _normalize_url("https://www.example.com/") == "example.com"
        assert _normalize_url("http://Example.COM/path") == "example.com"
        assert _normalize_url("https://sub.domain.com") == "sub.domain.com"

    def test_detect_tech_stack_wordpress(self):
        from openclaw.mcp_server.tools.lead_gen import _detect_tech_stack

        stack = _detect_tech_stack(MOCK_HTML_BAD)
        assert "WordPress" in stack

    def test_detect_tech_stack_nextjs(self):
        from openclaw.mcp_server.tools.lead_gen import _detect_tech_stack

        stack = _detect_tech_stack(MOCK_HTML_GOOD)
        assert "Next.js" in stack

    def test_detect_tech_stack_empty(self):
        from openclaw.mcp_server.tools.lead_gen import _detect_tech_stack

        assert _detect_tech_stack("<html></html>") == []

    def test_score_bad_website(self):
        from openclaw.mcp_server.tools.lead_gen import _score_website_quality

        result = _score_website_quality(MOCK_HTML_BAD, is_https=False)
        assert result["overall"] < 6.0  # Bad site should score low
        assert all(1 <= v <= 10 for v in result["scores"].values())

    def test_score_good_website(self):
        from openclaw.mcp_server.tools.lead_gen import _score_website_quality

        result = _score_website_quality(MOCK_HTML_GOOD, is_https=True)
        assert result["overall"] > 5.0  # Good site should score higher
        # Good site should beat bad site
        bad = _score_website_quality(MOCK_HTML_BAD, is_https=False)
        assert result["overall"] > bad["overall"]

    def test_extract_problems_wordpress(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_site_problems

        problems = _extract_site_problems(MOCK_HTML_BAD, ["WordPress"], is_https=False)
        assert len(problems) >= 3
        assert any("WordPress" in p for p in problems)
        assert any("HTTPS" in p or "Secure" in p for p in problems)

    def test_extract_problems_capped(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_site_problems

        problems = _extract_site_problems(MOCK_HTML_BAD, ["WordPress"], is_https=False)
        assert len(problems) <= 8  # Capped at 8

    def test_opportunity_score_hot_lead(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        # Great business (4.8 stars, 200 reviews) + terrible website (3.0/10)
        score = _compute_opportunity_score(4.8, 200, 3.0)
        assert score > 4.0

    def test_opportunity_score_cold_lead(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        # Bad business + good website
        score = _compute_opportunity_score(2.0, 5, 8.0)
        assert score < 2.0

    def test_opportunity_score_range(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        # Test extreme cases stay in bounds
        assert 0 <= _compute_opportunity_score(5.0, 10000, 0.0) <= 10
        assert 0 <= _compute_opportunity_score(0.0, 0, 10.0) <= 10
        assert 0 <= _compute_opportunity_score(None, 0, 5.0) <= 10

    def test_extract_brand_colors(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_brand_colors

        colors = _extract_brand_colors(MOCK_HTML_BAD)
        assert "#ff5733" in colors
        assert "#2a9d8f" in colors
        # Should skip #000000
        colors2 = _extract_brand_colors("<style>color: #000000; bg: #ffffff;</style>")
        assert len(colors2) == 0

    def test_extract_contact_emails(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_contact_emails

        emails = _extract_contact_emails(MOCK_HTML_BAD)
        assert "info@joesbbq.com" in emails

    def test_extract_contact_emails_skips_system(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_contact_emails

        emails = _extract_contact_emails("test@schema.org test@w3.org test@example.com")
        assert len(emails) == 0

    def test_copyright_year_detection(self):
        from openclaw.mcp_server.tools.lead_gen import _extract_site_problems

        old_html = "<footer>&copy; 2018 Old Corp</footer>"
        problems = _extract_site_problems(old_html, [], is_https=True)
        assert any("2018" in p for p in problems)

        current_html = "<footer>&copy; 2026 New Corp</footer>"
        problems2 = _extract_site_problems(current_html, [], is_https=True)
        assert not any("2026" in p for p in problems2)


# ---------------------------------------------------------------------------
# Tool-level integration tests (mocked DB + API)
# ---------------------------------------------------------------------------

class TestDiscoverProspects:
    @pytest.mark.asyncio
    async def test_discover_with_results(self):
        from openclaw.mcp_server.tools.lead_gen import discover_prospects

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Create a proper async context manager for the session factory
        mock_factory = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = False
        mock_factory.return_value = mock_ctx

        with (
            patch(
                "openclaw.mcp_server.tools.lead_gen._geocode_location",
                new_callable=AsyncMock,
                return_value=(30.2672, -97.7431),
            ),
            patch(
                "openclaw.integrations.google_places.search_nearby_competitors",
                new_callable=AsyncMock,
                return_value=MOCK_PLACES,
            ),
            patch(
                "openclaw.db.session.async_session_factory",
                mock_factory,
            ),
        ):
            result_json = await discover_prospects("restaurant", "Austin TX")
            result = json.loads(result_json)

            assert result["status"] == "discovered"
            assert result["total_places_found"] == 3
            assert result["with_websites"] == 2  # 1 has no website
            assert result["without_websites"] == 1

    @pytest.mark.asyncio
    async def test_discover_bad_location(self):
        from openclaw.mcp_server.tools.lead_gen import discover_prospects

        with patch(
            "openclaw.mcp_server.tools.lead_gen._geocode_location",
            return_value=(None, None),
        ):
            result_json = await discover_prospects("restaurant", "xyznotaplace")
            result = json.loads(result_json)
            assert result["status"] == "error"
            assert "geocode" in result["message"].lower()


class TestAuditProspectWebsite:
    @pytest.mark.asyncio
    async def test_audit_bad_website(self):
        from openclaw.mcp_server.tools.lead_gen import audit_prospect_website

        with patch(
            "openclaw.mcp_server.tools.lead_gen._fetch_page",
            new_callable=AsyncMock,
            return_value=(MOCK_HTML_BAD, "http://joesbbq.com", False, 200),
        ):
            result_json = await audit_prospect_website("http://joesbbq.com", "Joe's BBQ")
            result = json.loads(result_json)

            assert result["status"] == "audited"
            assert result["is_https"] is False
            assert "WordPress" in result["tech_stack"]
            assert result["website_overall"] < 6.0
            assert len(result["site_problems"]) >= 3
            assert "info@joesbbq.com" in result["contact_emails"]

    @pytest.mark.asyncio
    async def test_audit_good_website(self):
        from openclaw.mcp_server.tools.lead_gen import audit_prospect_website

        with patch(
            "openclaw.mcp_server.tools.lead_gen._fetch_page",
            new_callable=AsyncMock,
            return_value=(MOCK_HTML_GOOD, "https://blandburgers.com", True, 200),
        ):
            result_json = await audit_prospect_website("https://blandburgers.com")
            result = json.loads(result_json)

            assert result["status"] == "audited"
            assert result["is_https"] is True
            assert "Next.js" in result["tech_stack"]
            assert result["website_overall"] > 5.0

    @pytest.mark.asyncio
    async def test_audit_unreachable(self):
        from openclaw.mcp_server.tools.lead_gen import audit_prospect_website

        with patch(
            "openclaw.mcp_server.tools.lead_gen._fetch_page",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused"),
        ):
            result_json = await audit_prospect_website("http://deadsite.com")
            result = json.loads(result_json)

            assert result["status"] == "error"
            assert "deadsite.com" in result["url"]

    @pytest.mark.asyncio
    async def test_audit_non_200(self):
        from openclaw.mcp_server.tools.lead_gen import audit_prospect_website

        with patch(
            "openclaw.mcp_server.tools.lead_gen._fetch_page",
            new_callable=AsyncMock,
            return_value=("", "http://example.com", False, 404),
        ):
            result_json = await audit_prospect_website("http://example.com/missing")
            result = json.loads(result_json)

            assert result["status"] == "error"
            assert "404" in result["message"]


class TestComputeOpportunity:
    def test_scoring_relationships(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        # Better business + worse website should always score higher
        hot = _compute_opportunity_score(4.8, 300, 2.0)
        warm = _compute_opportunity_score(4.0, 100, 5.0)
        cold = _compute_opportunity_score(2.5, 10, 8.0)

        assert hot > warm > cold

    def test_perfect_website_zero_opportunity(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        # Perfect 10/10 website = no opportunity (no website weakness)
        score = _compute_opportunity_score(5.0, 1000, 10.0)
        assert score == 0.0

    def test_no_reviews_still_scores(self):
        from openclaw.mcp_server.tools.lead_gen import _compute_opportunity_score

        score = _compute_opportunity_score(4.0, 0, 3.0)
        assert score > 0


class TestGeocode:
    @pytest.mark.asyncio
    async def test_geocode_success(self):
        from openclaw.mcp_server.tools.lead_gen import _geocode_location

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [
                {"location": {"latitude": 30.2672, "longitude": -97.7431}}
            ]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("openclaw.mcp_server.tools.lead_gen.httpx.AsyncClient", return_value=mock_client):
            lat, lng = await _geocode_location("Austin TX")
            assert lat == pytest.approx(30.2672)
            assert lng == pytest.approx(-97.7431)

    @pytest.mark.asyncio
    async def test_geocode_no_results(self):
        from openclaw.mcp_server.tools.lead_gen import _geocode_location

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"places": []}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("openclaw.mcp_server.tools.lead_gen.httpx.AsyncClient", return_value=mock_client):
            lat, lng = await _geocode_location("xyznotaplace")
            assert lat is None
            assert lng is None

    @pytest.mark.asyncio
    async def test_geocode_api_error(self):
        from openclaw.mcp_server.tools.lead_gen import _geocode_location

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("openclaw.mcp_server.tools.lead_gen.httpx.AsyncClient", return_value=mock_client):
            lat, lng = await _geocode_location("Austin TX")
            assert lat is None
            assert lng is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
