# Lead Generation Pipeline — Reference Guide

## Overview

The lead generation pipeline discovers businesses with good reputations but bad websites, making them ideal prospects for Clarmi Design Studio. It runs on top of the existing Google Places API integration and website scoring heuristics.

## Architecture

```
discover_prospects()     →  Google Places API  →  raw business list
        ↓
audit_prospect_website() →  httpx fetch + HTML analysis  →  scores + problems
        ↓
run_lead_generation()    →  discover + audit + score  →  stored Prospect records
        ↓
get_lead_pipeline()      →  query DB  →  ranked lead list
        ↓
promote_lead()           →  create Project  →  full build pipeline
```

## Tools

### 1. `discover_prospects(industry, location, max_results=10, radius_m=10000)`

Pure discovery — searches Google Places and returns businesses with websites.

**Input:**
- `industry`: Business type (e.g., "restaurant", "hair salon", "dental office")
- `location`: City or area name (auto-geocoded via Google Places)
- `max_results`: Cap at 20 per API limits
- `radius_m`: Search radius from geocoded center

**Output:**
- List of businesses with name, website, rating, review_count, address, lat/lng
- Flags businesses already in the database (`already_in_db: true`)
- Does NOT store anything

**Cost:** ~$0.032 per search (Google Places Text Search)

### 2. `audit_prospect_website(url, company_name?, industry?)`

Fetches a single website and produces a detailed audit.

**Scoring dimensions** (each 1-10):
- `technical`: HTTPS, viewport, charset, script bloat, modern framework detection
- `mobile_friendly`: viewport meta, flexbox/grid usage, media queries, table layouts
- `visual_design`: custom fonts, gradients, animations, CSS frameworks
- `ux_navigation`: semantic HTML (nav/header/footer), CTAs, link density
- `content_quality`: H1 tags, testimonials, images, paragraphs, lorem ipsum

**Weighted overall:** `visual*0.20 + ux*0.25 + content*0.20 + tech*0.15 + mobile*0.20`

**Also extracts:**
- Tech stack (WordPress, Wix, Squarespace, React, Next.js, etc.)
- Site problems as punchy statements (up to 8)
- Brand colors from CSS hex values
- Contact emails from HTML
- Page title and meta description
- Content metrics (HTML size, image count, link count)

### 3. `run_lead_generation(industry, location, max_results=10, radius_m=10000, min_opportunity_score=2.5)`

Full pipeline — the main workhorse tool.

**Pipeline:**
1. Geocode location
2. Search Google Places for businesses
3. Filter to those with websites
4. Skip businesses already in DB
5. For each new business: fetch website → score → extract problems → compute opportunity
6. Store qualified leads (above threshold) as Prospect records
7. Return ranked list

**Opportunity score formula:**
```
business_quality = rating/5 * 0.6 + log10(reviews+1)/3 * 0.4
website_weakness = (10 - website_overall) / 10
opportunity = business_quality * website_weakness * 10
```

**Stored in `prospect.raw_data`:**
- `lead_source: "auto_discovery"` — flag for filtering
- `lead_batch: "20260401-091523"` — batch ID for grouping
- `lead_score: 6.8` — opportunity score
- `lead_industry: "restaurant"` — search industry
- `lead_location: "Austin TX"` — search location
- `website_scores: {...}` — dimension breakdown
- `website_overall: 4.2` — weighted score
- `google_rating: 4.5` — from Google Places
- `google_review_count: 234` — from Google Places
- `site_problems: [...]` — punchy problem statements
- `discovered_at: "2026-04-01T09:15:23Z"` — timestamp

### 4. `get_lead_pipeline(industry?, location?, min_score?, limit=20, include_promoted=False)`

Query the lead pipeline with filters.

**Filters:**
- `industry`: Filter by the industry used during discovery
- `location`: Filter by discovery location
- `min_score`: Minimum opportunity score
- `include_promoted`: Include leads that already have projects

**Returns:** Leads sorted by opportunity score descending, with key metrics and top 3 problems.

### 5. `promote_lead(prospect_id, auto_create_project=True)`

Move a lead into the full build pipeline.

**Actions:**
1. Validate prospect exists and is auto-discovered
2. Check for existing project (prevent duplicates)
3. Create project with auto-generated brief from lead data
4. Link prospect to project
5. Mark prospect as promoted

**The created project:**
- Has the prospect linked via `prospect_id`
- Brief includes: website score, top 3 problems, Google rating
- GitHub repo + Vercel project auto-provisioned (via `create_project`)
- Ready for pitch → design → build pipeline

### 6. `batch_lead_generation(industries?, locations?, max_per_search=5, min_opportunity_score=2.5)`

Run lead generation across multiple industry+location combinations.

**Uses configured defaults** when params not provided:
- `PROSPECTING_INDUSTRIES` env var (comma-separated)
- `PROSPECTING_LOCATIONS` env var (comma-separated)
- `PROSPECTING_DAILY_LIMIT` env var (caps total results)

**Returns:** Aggregate summary + per-search breakdown.

## Website Problem Detection

The audit identifies problems in these categories:

| Category | Detection Method | Example Problem |
|----------|-----------------|-----------------|
| Tech/Performance | CMS detection, script count, HTTPS | "WordPress with 12+ plugins — bloated, slow, security risk" |
| Mobile | Viewport meta, CSS layout | "No mobile viewport — site is unusable on phones" |
| Navigation/UX | Link count, CTA detection | "No clear call-to-action — visitors leave without converting" |
| Content | H1, testimonials, images | "No testimonials or reviews — missing social proof" |
| Design | Font detection, marquee/blink | "No custom fonts — using default system fonts looks generic" |
| Freshness | Copyright year regex | "Copyright says 2019 — site appears abandoned" |

## Cost Estimates

| API Call | Cost |
|----------|------|
| Google Places Text Search | ~$0.032 per search |
| Google Places geocode | ~$0.032 per location |
| Website fetch (httpx) | Free |
| Total per `run_lead_generation` | ~$0.064 + free audits |
| Total per `batch_lead_generation` (4 combos) | ~$0.32 |
| Daily limit of 50 prospects | ~$0.64/day max |

## Deduplication

- Prospects are deduplicated by normalized URL (strip www, trailing slash, lowercase)
- `run_lead_generation` skips businesses already in the database
- `promote_lead` prevents creating duplicate projects for the same prospect
- `discover_prospects` flags existing records but doesn't skip them (discovery-only)

## Integration Points

The lead gen pipeline integrates with existing tools:

- **Google Places API** (`integrations/google_places.py`): Business discovery
- **Prospect model** (`models/prospect.py`): Lead storage
- **prospect_service** (`services/prospect_service.py`): CRUD operations
- **project_service** (`services/project_service.py`): Project creation on promote
- **Email tools** (`tools/email.py`): Outreach after promotion
- **Competitor tools** (`tools/competitors.py`): Run competitor analysis on promoted leads
