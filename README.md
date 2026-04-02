# Clarmi Design Studio

AI-powered digital design agency. A single autonomous agent handles the entire website pipeline — research, competitor analysis, pitch decks, design, build, QA, and outreach — communicating with you over WhatsApp or CLI.

Built on [OpenClaw](https://openclaw.com) with a Python MCP tool server, Next.js client sites, and Vercel deployments.

## What It Does

Send a message like _"revamp schooloftheworld.org"_ and the agent runs the full pipeline:

| Step | What happens |
|------|-------------|
| **1. Research** | Crawls the prospect's site, extracts content/branding, audits for problems |
| **1.5 Competitors** | Finds nearby competitors via Google Places, scores their websites, generates a comparison deck |
| **2. Pitch** | Generates a personalized HTML slide deck at `/pitch/` with audit, improvements, and pricing |
| **3. Design** | Generates hero video keyframes (Nano Banana) and transition videos (Veo 3.1) for scroll-controlled playback |
| **4. Build** | Spawns parallel sub-agents to build sections simultaneously, assembles a Next.js site, deploys to Vercel |
| **5. QA** | Screenshots at 4 viewports, Lighthouse audit (must score >= 85) |
| **6. Outreach** | Drafts a cold email linking to the pitch deck and live demo |

### Lead Generation

Two modes for finding prospects:

- **Revamp** — Finds businesses with good reputations but bad websites
- **Adventure** — Finds businesses with no website at all, builds one from scratch using Google Places, Yelp, Instagram, and Facebook data

Leads are scored 0-10. Hot leads (7+) auto-promote into the build pipeline.

### Client Funnel

When a client requests revisions, the agent handles it autonomously — reads the code, makes edits, deploys a preview branch, sends the preview URL, and merges to production on approval.

## Architecture

```
src/openclaw/
  mcp_server/              # MCP tool server (13 tool modules)
    tools/
      ingest.py            #   Website crawling + structure extraction
      orchestration.py     #   Build coordination, superprompts, section tracking
      competitors.py       #   Google Places discovery + website scoring
      design.py            #   Image generation (Nano Banana) + video (Veo 3.1)
      engineering.py       #   Next.js scaffold, code read/write/edit, build, deploy
      lead_gen.py          #   Lead discovery, scoring, batch prospecting
      projects.py          #   Project CRUD + status tracking
      prospects.py         #   Prospect data management
      qa.py                #   Screenshots (Playwright) + Lighthouse audits
      email.py             #   Gmail draft + send
      research.py          #   Knowledge storage
      learning.py          #   Project analytics + metrics
  integrations/            # External API clients
    github_client.py       #   Repo creation, file management
    gmail_client.py        #   OAuth2 email
    google_ai.py           #   Nano Banana (images) + Veo 3.1 (video)
    google_places.py       #   Competitor + lead discovery
    vercel_client.py       #   Project creation, deployment, domains
    whatsapp_client.py     #   Message handling
  services/                # Business logic layer
  models/                  # SQLAlchemy ORM (projects, prospects, assets, deployments, etc.)
  db/                      # Async database session
  config.py                # Pydantic settings from .env

templates/
  prompts/                 # 14 design/engineering prompt templates
    immersive-site.md      #   Master design system (scroll video + GSAP + ReactBits)
    section-agent.md       #   Sub-agent prompt template for parallel builds
    section-choreography.md#   Section flow, rhythm, composition templates
    effect-catalog.md      #   200+ GSAP animation patterns
    three-js-scene.md      #   React Three Fiber recipes by industry
    hero-section.md        #   Scroll-controlled video hero patterns
    scroll-video-section.md#   ScrollVideo component patterns
    branding-to-design.md  #   Convert prospect data to design spec
    video-prompt-library.md#   Pre-written Veo/Nano Banana prompts
    responsive-patterns.md #   Mobile fallbacks, fluid typography
    shader-backgrounds.md  #   GLSL shader backgrounds
    scroll-animation.md    #   Scroll-driven animation recipes
    full-site.md           #   Full site generation template
    page-transitions.md    #   Page transition animations
  pitch/                   #   Pitch deck templates + viewport-base.css
  competitors/             #   Competitor analysis deck templates
  lead-gen/                #   Lead generation email templates

website/                   # Clarmi showcase site (Next.js 15, GSAP, Three.js)
dashboard/                 # Internal management dashboard (Next.js 16, Recharts, Leaflet)

openclaw.json              # Agent config: model, channels, MCP tools, cron jobs
.mcp.json                  # Claude Code MCP server definitions
docker-compose.yml         # Local PostgreSQL
alembic/                   # Database migrations
```

## Tech Stack

**Backend:** Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL (Neon), Playwright

**Client sites:** Next.js 15/16, TypeScript, Tailwind CSS 4, GSAP + ScrollTrigger, Lenis, React Three Fiber (optional)

**External services:** Anthropic (Claude), Google AI (Nano Banana + Veo 3.1), Google Places, GitHub, Vercel, Gmail

**MCP servers:** clarmi-tools (Python, custom), ReactBits (135+ animated React components)

## Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| Design research | Every 6 hours | Scrapes Awwwards, Dribbble, CSS-Tricks for trends |
| Daily learning | 3 AM daily | Analyzes completed projects, logs metrics |
| Lead prospecting | 9 AM weekdays (disabled by default) | Batch lead generation across configured industries/locations |

## Development

```bash
pip install -e ".[dev]"    # Install with dev deps
pytest                      # Run tests
ruff check src/ tests/      # Lint
python -m openclaw.mcp_server  # Test MCP server directly
```

## License

Proprietary.
