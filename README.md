# Clarmi Design Studio

AI-powered digital design agency built on [OpenClaw](https://openclaw.com). A single autonomous agent handles the full website pipeline — research, design, build, QA, and outreach — communicating with you over WhatsApp or CLI.

## How It Works

Clarmi operates as an OpenClaw agent with a Python MCP tool server. You send it a message like _"build a website for example.com"_ and it runs the full pipeline:

1. **Research** — Crawls the prospect's site with WebFetch, extracts branding, audits for problems
2. **Pitch** — Auto-generates a personalized pitch page at `/pitch` with site audit, proposed improvements, live demo link, and pricing
3. **Design** — Generates images and video assets via Google AI
4. **Build** — Scaffolds a Next.js app (App Router, GSAP, Tailwind), writes code, deploys to Vercel
5. **QA** — Takes screenshots at multiple viewports, runs Lighthouse (must score >= 85 to proceed)
6. **Outreach** — Drafts a personalized cold email linking to the pitch page

Cron jobs run design research (every 6 hours) and project learning (daily at 3 AM).

## Prerequisites

- Python 3.12+
- Node.js
- Docker

## Quick Start

```bash
bash setup.sh
```

This installs OpenClaw, Python dependencies, Playwright Chromium, starts PostgreSQL, and runs database migrations.

After setup, edit `.env` with your API keys:

```
ANTHROPIC_API_KEY=
GOOGLE_AI_API_KEY=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_EMAIL=
GITHUB_PAT=
VERCEL_TOKEN=
```

Then start the agent:

```bash
openclaw
```

Scan the QR code for WhatsApp pairing, or use `openclaw chat` for CLI mode.

## Project Structure

```
src/openclaw/
  mcp_server/          # MCP tool server
    tools/             # Tool definitions
      research.py      #   Knowledge storage
      prospects.py     #   Prospect management
      design.py        #   Image/video generation (Google AI)
      engineering.py   #   Scaffold, write code, verify builds
      projects.py      #   Project CRUD & status
      qa.py            #   Screenshots, Lighthouse
      email.py         #   Gmail drafts & sending
      learning.py      #   Trend research, metrics
  integrations/        # External service clients
    github_client.py
    gmail_client.py
    google_ai.py
    vercel_client.py
    whatsapp_client.py
  services/            # Business logic
  models/              # SQLAlchemy models
  db/                  # Database session & utilities
  config.py            # Pydantic settings
alembic/               # Database migrations
templates/             # Email templates
tests/                 # Test suite
openclaw.json          # OpenClaw agent config
system-prompt.md       # Agent system prompt
docker-compose.yml     # PostgreSQL
```

## Development

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check src/ tests/
```

Test the MCP server directly:

```bash
python -m openclaw.mcp_server
```

## License

Proprietary.
