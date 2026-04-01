# Competitor Analysis Agent — Specification

This document specifies the complete competitor analysis feature for Clarmi Design Studio. The agent discovers nearby competing businesses via the Google Places API, scrapes and scores their websites, and produces a standalone HTML comparison deck at `/competitors/` in the project repository.

---

## Pipeline Position

Runs after **Step 1 (Research)** and in parallel with **Step 2 (Pitch)**. Does not block Steps 3–6.

```
Research → [Competitor Analysis] → Pitch → Design → Build → QA → Outreach
              (async)               (async)
```

The competitor analysis informs the Build step — recommendations from the report guide website design decisions.

---

## Step-by-Step Workflow

### 1. Discover Competitors

Call `find_competitors(project_name)` after `store_prospect()` completes.

The tool:
- Looks up the prospect's latitude, longitude, and industry from the database
- Auto-generates a search query: `"{industry} near {company_name}"` (or uses a custom query if provided)
- Calls the Google Places API (New) Text Search endpoint
- Filters out the prospect itself (by URL/name match)
- Scores each result for **relevance** using a weighted algorithm:
  - **Type match (40%)** — overlap between competitor types and prospect industry
  - **Proximity (25%)** — closer businesses are more relevant competitors
  - **Price match (20%)** — same price tier = direct competitor
  - **Review volume (15%)** — similar scale; penalizes large chains with 5000+ reviews
- Returns top 10 ranked by relevance
- Stores results in `prospect.raw_data["competitors"]`

### 2. Analyze Competitor Websites

Call `analyze_competitor_websites(project_name)`.

The tool takes the top 5 competitors and for each one that has a website:
- Fetches the homepage HTML (max 50KB, 15s timeout)
- Scores on 5 dimensions (1–10 each):
  - **Visual Design** — custom fonts, gradients, animations, modern CSS framework
  - **UX/Navigation** — `<nav>`, `<header>`, `<footer>`, CTAs (book/order/contact), search
  - **Content Quality** — `<h1>`, testimonials, images, paragraphs, no lorem ipsum
  - **Technical** — HTTPS, viewport meta, charset, script count, modern vs WordPress/Wix
  - **Mobile Friendly** — `width=device-width`, flexbox/grid, media queries, no table-based layout
- Computes weighted overall score:
  ```
  overall = visual*0.20 + ux*0.25 + content*0.20 + technical*0.15 + mobile*0.20
  ```
- Generates up to 3 strengths and 3 weaknesses as SHORT PUNCHY statements
- Stores enriched data in `prospect.raw_data["competitor_analysis"]`

Competitors without a website get score 0 and weakness: "No website — invisible to online customers."

### 3. Generate the Report

Call `generate_competitor_report(project_name)`.

This returns:
- Full competitor analysis data (all 5 competitors with scores, strengths, weaknesses)
- Prospect data (name, industry, brand colors, site problems)
- Market stats (avg rating, avg website score, price distribution)
- Common competitor weaknesses (for gap analysis)
- Paths to the template reference and base CSS

### 4. Build the HTML Deck

The agent then:
1. Reads `templates/competitors/reference.md` for the generation guide
2. Reads `templates/pitch/viewport-base.css` — embeds its FULL contents inline in `<style>`
3. Generates the HTML following the reference, using actual competitor data
4. Calls `write_code(project_name, "public/competitors/index.html", html)`
5. Calls `deploy(project_name, "Add competitor analysis")`

The deck becomes live at `https://[deployed_url]/competitors/`.

---

## New Files

### Integration Client: `src/openclaw/integrations/google_places.py`

Async httpx client for the Google Places API (New). Three functions:

**`search_nearby_competitors(query, latitude, longitude, radius_m, max_results)`**
- `POST https://places.googleapis.com/v1/places:searchText`
- Headers: `X-Goog-Api-Key`, `X-Goog-FieldMask`
- Field mask requests: id, displayName, formattedAddress, location, rating, userRatingCount, priceLevel, types, websiteUri, googleMapsUri, primaryType, primaryTypeDisplayName
- Request body: `textQuery`, `locationBias` (circle around lat/lng), `maxResultCount`, `languageCode`
- Returns normalized list of place dicts

**`get_place_details(place_id)`**
- `GET https://places.googleapis.com/v1/places/{place_id}`
- Returns full place details (reviews, photos, hours)
- Used for optional deeper analysis

**`haversine_distance(lat1, lon1, lat2, lon2)`**
- Pure math, no API call
- Returns distance in meters between two coordinates
- Used for proximity scoring and display ("0.3 mi away")

**`score_relevance(place, prospect_lat, prospect_lng, prospect_types, prospect_price_level, radius_m)`**
- Returns float 0.0–1.0
- Weighted: type_match (0.40), proximity (0.25), price_match (0.20), review_volume (0.15)
- Type match: set intersection of place types vs prospect types
- Proximity: linear decay from 1.0 at 0m to 0.0 at radius
- Price match: 1.0 for exact level, 0.5 for one off, 0.0 for two+ off
- Review volume: 1.0 for 50–1000, lower for extremes

### MCP Tools: `src/openclaw/mcp_server/tools/competitors.py`

Three `@mcp.tool()` functions:

1. **`find_competitors(project_name, search_query?, radius_m?)`** — discovery + relevance scoring
2. **`analyze_competitor_websites(project_name)`** — website scraping + quality scoring
3. **`generate_competitor_report(project_name)`** — data assembly for HTML generation

Plus a shared helper:
- **`_get_prospect_for_project(project_name)`** — resolves project → prospect via DB

### Template: `templates/competitors/reference.md`

Already written. Defines the 10-slide HTML deck format, all CSS components (score bars, stars, price levels, comparison grid), design direction, animation patterns, and rules.

---

## Modified Files

### `src/openclaw/config.py`

Add:
```python
# Google Places API (New)
GOOGLE_PLACES_API_KEY: str = ""
```

### `src/openclaw/mcp_server/server.py`

Add import:
```python
import openclaw.mcp_server.tools.competitors  # noqa: F401
```

### `openclaw.json`

Add to `mcp.clarmi-tools.env`:
```json
"GOOGLE_PLACES_API_KEY": "${GOOGLE_PLACES_API_KEY}"
```

### `CLAUDE.md`

Insert Step 1.5 between Research (Step 1) and Pitch (Step 2):

```markdown
### Step 1.5: Competitor Analysis (async — does not block Steps 2-6)

Analyze the local competitive landscape after research completes.

1. Call `find_competitors(project_name)` — discovers nearby similar businesses via Google Places
2. Call `analyze_competitor_websites(project_name)` — scrapes and scores top 5 competitor websites
3. Call `generate_competitor_report(project_name)` — returns template + data
4. Read `templates/competitors/reference.md` for the full generation guide
5. Read `templates/pitch/viewport-base.css` — embed its FULL contents inline in the HTML `<style>`
6. Generate the HTML following the reference guide using actual competitor data
7. Use `write_code(project_name, "public/competitors/index.html", ...)` to create the report
8. Call `deploy(project_name, "Add competitor analysis")` — static file, no build needed
```

Also update the Outreach email CTA to link to both `/pitch` and `/competitors`.

### `system-prompt.md`

Mirror the CLAUDE.md Step 1.5 addition between Step 1 (Research) and Step 2 (Design).

### `.env.example`

Add:
```
GOOGLE_PLACES_API_KEY=
```

---

## Data Storage

All competitor data lives in the existing `prospect.raw_data` JSON column — **no new database tables or migrations**.

| Key | Set by | Contents |
|-----|--------|----------|
| `raw_data["competitors"]` | `find_competitors` | Top 10 places from Google Places API with relevance scores, distance |
| `raw_data["competitor_analysis"]` | `analyze_competitor_websites` | Top 5 enriched with website scores (5 dimensions), strengths, weaknesses |
| `raw_data["place_types"]` | `store_prospect` (updated) | Prospect's own place types for type-match scoring |
| `raw_data["price_level"]` | `store_prospect` (updated) | Prospect's own price level for price-match scoring |

---

## Google Places API Details

### Endpoint
```
POST https://places.googleapis.com/v1/places:searchText
```

### Required Headers
```
X-Goog-Api-Key: {GOOGLE_PLACES_API_KEY}
X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.types,places.websiteUri,places.googleMapsUri,places.primaryType,places.primaryTypeDisplayName
Content-Type: application/json
```

### Request Body
```json
{
    "textQuery": "Italian restaurants near Bella Vista Trattoria",
    "locationBias": {
        "circle": {
            "center": {"latitude": 40.7128, "longitude": -74.0060},
            "radius": 5000.0
        }
    },
    "maxResultCount": 20,
    "languageCode": "en"
}
```

### Price Level Enum
- `PRICE_LEVEL_FREE` → 0 ($)
- `PRICE_LEVEL_INEXPENSIVE` → 1 ($)
- `PRICE_LEVEL_MODERATE` → 2 ($$)
- `PRICE_LEVEL_EXPENSIVE` → 3 ($$$)
- `PRICE_LEVEL_VERY_EXPENSIVE` → 4 ($$$$)

### Billing
- Text Search (Basic): $32 per 1000 requests
- Place Details: $17 per 1000 requests
- Typical usage: 1 search + 0–5 detail lookups per project ≈ $0.12/project

---

## Website Quality Scoring Heuristics

The `analyze_competitor_websites` tool uses HTML signal detection (not Lighthouse) for fast automated scoring. Each dimension starts at 5/10 and adjusts based on detected signals:

### Technical (weight: 0.15)
| Signal | Effect |
|--------|--------|
| HTTPS | +1 |
| viewport meta | +1 |
| charset declaration | +0.5 |
| > 15 script tags | -1 (bloated) |
| WordPress/wp-content detected | -0.5 |
| Wix/Squarespace detected | -0.5 |
| Next.js/React/Vue detected | +1 |

### Mobile Friendly (weight: 0.20)
| Signal | Effect |
|--------|--------|
| `width=device-width` in viewport | +2 |
| flexbox or grid CSS | +1 |
| `@media` queries | +1 |
| > 3 `<table>` elements | -2 |

### Visual Design (weight: 0.20)
| Signal | Effect |
|--------|--------|
| Custom font-family or Google Fonts | +1 |
| CSS gradients or animations | +1 |
| Rich color/background styling | +0.5 |
| `<marquee>` or `<blink>` | -3 |
| Tailwind or Bootstrap | +0.5 |

### UX/Navigation (weight: 0.25)
| Signal | Effect |
|--------|--------|
| `<nav>` element | +1 |
| `tel:` or `mailto:` links | +1 |
| `<footer>` element | +0.5 |
| `<header>` element | +0.5 |
| > 50 links | -1 (cluttered) |
| Search functionality | +0.5 |
| 2+ CTA keywords (book/order/contact/call/reserve) | +1 |
| 0 CTA keywords | -1 |

### Content Quality (weight: 0.20)
| Signal | Effect |
|--------|--------|
| `<h1>` present | +1 |
| Testimonial/review text | +1 |
| 3+ images | +0.5 |
| < 3 paragraphs | -1 |
| "About" + "team" text | +0.5 |
| "Lorem ipsum" detected | -3 |

All scores clamped to [1, 10].

---

## Relevance Scoring Algorithm

```
relevance = (
    type_match   * 0.40    # Set intersection of place types
  + proximity    * 0.25    # Linear decay: 1.0 at 0m → 0.0 at radius_m
  + price_match  * 0.20    # 1.0 = exact, 0.5 = one level off, 0.0 = two+ off
  + review_score * 0.15    # 1.0 for 50–1000 reviews, lower for extremes
)
```

### Review Volume Scoring
| Review Count | Score | Rationale |
|-------------|-------|-----------|
| > 5000 | 0.3 | Likely a chain — less relevant as direct competitor |
| 1001–5000 | 0.6 | Large operation — somewhat comparable |
| 51–1000 | 1.0 | Sweet spot — similar scale to most local businesses |
| 11–50 | 0.8 | Small but established |
| ≤ 10 | 0.5 | Very new or low-traffic |

---

## Implementation Order

1. **Config** — `GOOGLE_PLACES_API_KEY` in config.py, .env.example, openclaw.json
2. **Integration** — `google_places.py` (search, details, haversine, relevance scoring)
3. **MCP Tools** — `competitors.py` (3 tools + helper)
4. **Server** — import in server.py
5. **Template** — `reference.md` (already written)
6. **Pipeline docs** — CLAUDE.md and system-prompt.md

---

## Verification

1. `python -c "from openclaw.integrations.google_places import search_nearby_competitors"` — import check
2. `python -c "from openclaw.mcp_server.tools.competitors import find_competitors"` — tool registration check
3. End-to-end: research a prospect → find_competitors → analyze_competitor_websites → generate_competitor_report → write HTML → deploy → visit `/competitors/`
4. Open generated HTML in browser: verify scroll-snap, keyboard nav, score bar animations, mobile layout
