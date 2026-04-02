# Setup Guide

How to get Clarmi Design Studio running on a new machine.

## Prerequisites

- **Python 3.12+** — `python3 --version`
- **Node.js 20+** — `node --version`
- **Docker** — for local PostgreSQL (or use a hosted Neon database)
- **Git** — `git --version`

## 1. Clone the repo

```bash
git clone https://github.com/jason-clarmi/High-Level-Cow-Horse.git
cd High-Level-Cow-Horse
```

## 2. Install Python dependencies

```bash
python3 -m pip install -e .
```

This installs the MCP tool server and all Python dependencies (FastAPI, SQLAlchemy, Playwright, httpx, etc.).

## 3. Install Playwright browsers

The QA tools use Playwright for screenshots and Lighthouse audits:

```bash
playwright install chromium
playwright install-deps chromium
```

## 4. Install OpenClaw

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

## 5. Set up the database

**Option A: Local PostgreSQL (Docker)**

```bash
docker compose up -d postgres
```

Wait for it to be ready, then run migrations:

```bash
alembic upgrade head
```

**Option B: Neon (hosted PostgreSQL)**

Create a project at [neon.tech](https://neon.tech), copy the connection string, and put it in `.env` as `DATABASE_URL`. Then run migrations:

```bash
alembic upgrade head
```

## 6. Configure environment variables

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...          # Claude API key (anthropic.com)
GOOGLE_AI_API_KEY=AIzaSy...           # Google AI Studio key (for Nano Banana + Veo 3.1)
GITHUB_PAT=ghp_...                    # GitHub Personal Access Token (repo scope)
VERCEL_TOKEN=vcp_...                  # Vercel token (vercel.com/account/tokens)
DATABASE_URL=postgresql+asyncpg://... # PostgreSQL connection string

# Email outreach (optional — needed for Step 6: Outreach)
GMAIL_CLIENT_ID=...                   # Google OAuth2 client ID
GMAIL_CLIENT_SECRET=...               # Google OAuth2 client secret
GMAIL_REFRESH_TOKEN=...               # OAuth2 refresh token
GMAIL_SENDER_EMAIL=you@domain.com     # Sender email address

# Competitor analysis (optional — needed for Step 1.5)
GOOGLE_PLACES_API_KEY=...             # Google Places API key

# Lead generation (optional)
PROSPECTING_ENABLED=false
PROSPECTING_INDUSTRIES=restaurant,salon,dentist
PROSPECTING_LOCATIONS=Austin TX,Dallas TX
PROSPECTING_DAILY_LIMIT=50

# Deployment
DEPLOY_DOMAIN=openclaw.site           # Custom domain for Vercel projects
STORAGE_PATH=/tmp/openclaw-projects   # Where project files are stored locally
```

### How to get each key

| Key | Where to get it |
|-----|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GOOGLE_AI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) → Get API Key |
| `GOOGLE_PLACES_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Places API |
| `GITHUB_PAT` | GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained → repo permissions |
| `VERCEL_TOKEN` | [vercel.com/account/tokens](https://vercel.com/account/tokens) → Create Token |
| `GMAIL_*` | Google Cloud Console → OAuth2 credentials → Gmail API scope. See [Gmail OAuth2 guide](https://developers.google.com/gmail/api/auth/web-server) |

## 7. Configure MCP servers

The `.mcp.json` file defines two MCP servers that Claude Code connects to:

```json
{
  "mcpServers": {
    "clarmi-tools": {
      "command": "python3",
      "args": ["-m", "openclaw.mcp_server"],
      "env": { "PYTHONPATH": "src" }
    },
    "reactbits": {
      "command": "npx",
      "args": ["reactbits-dev-mcp-server"]
    }
  }
}
```

This file is already in the repo. Claude Code reads it automatically when you open the project.

## 8. Start the agent

**WhatsApp mode** (pair via QR code):

```bash
openclaw
```

**CLI mode** (chat directly in terminal):

```bash
openclaw chat
```

**Claude Code mode** (use as MCP tools inside Claude Code):

Just open the project directory in Claude Code. The `.mcp.json` file auto-registers the tools.

## 9. Verify it works

Test the MCP server directly:

```bash
PYTHONPATH=src python3 -m openclaw.mcp_server
```

Or in Claude Code, try:

```
list_projects()
```

If it returns an empty list (or your existing projects), the MCP server is connected.

## Project Storage

Client website projects are stored in `STORAGE_PATH` (default: `/tmp/openclaw-projects`). Each project gets a subdirectory with:

```
/tmp/openclaw-projects/{project-name}/
  ingest.json          # Extracted site structure + brand data
  site/                # Next.js project files
    app/
    components/
    package.json
    ...
```

For persistence across reboots, change `STORAGE_PATH` to a non-tmp directory:

```bash
STORAGE_PATH=/home/you/clarmi-projects
```

## Troubleshooting

**MCP server won't start**
- Check `PYTHONPATH=src` is set when running outside Claude Code
- Verify `DATABASE_URL` is reachable: `python3 -c "import asyncpg; print('OK')"`

**Playwright fails**
- Run `playwright install-deps chromium` for system-level dependencies
- On Linux servers, you may need: `apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1`

**Vercel deployment fails**
- Verify token: `vercel whoami --token $VERCEL_TOKEN`
- Check scope: `vercel teams list --token $VERCEL_TOKEN`

**GitHub repo creation fails**
- Verify PAT has `repo` scope: `curl -H "Authorization: token $GITHUB_PAT" https://api.github.com/user`
- For org repos, the PAT owner must be an org member with create-repo permission

**Database connection fails**
- Local: `docker compose ps` to check PostgreSQL is running
- Neon: verify the connection string includes `?ssl=require`
- Run `alembic upgrade head` after any model changes
