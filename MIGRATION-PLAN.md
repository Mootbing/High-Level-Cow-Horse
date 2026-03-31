# Migration: Multi-Agent -> Single OpenClaw Agent

## Context

The current Clarmi Design Studio runs 11 Python agents communicating via Redis Streams, with a React dashboard and ClawdBot WhatsApp bridge. The user wants to collapse this into a **single OpenClaw agent** (github.com/openclaw/openclaw) — a self-hosted Node.js AI assistant framework that handles WhatsApp, Claude Code CLI, session management, and cron natively. All agent logic becomes one system prompt; all integrations become tools via a Python **MCP server**.

---

## Architecture

```
OpenClaw Daemon (Node.js)
├── Provider: Anthropic (Claude)
├── Channel: WhatsApp (built-in plugin, replaces ClawdBot)
├── Channel: Claude Code CLI (built-in)
├── System Prompt: system-prompt.md (consolidated from 11 agents)
├── Cron: research (6h), learning (daily 3am)
└── MCP Server: clarmi-tools (Python subprocess, stdio)
    ├── Tools: scrape, design, engineer, QA, email, projects, prospects, research, learning
    ├── Integrations: Firecrawl, GitHub, Vercel, Gmail, Google AI (reused as-is)
    ├── Services: project_service, task_service, prospect_service (reused as-is)
    └── Database: PostgreSQL via SQLAlchemy async (reused as-is)
```

Parallel execution: each project gets its own OpenClaw session. Sessions run in parallel; operations within a session run serially.

---

## Phase 1: Create MCP Server (no destructive changes)

### 1.1 Create `src/openclaw/mcp_server/` package

**`__init__.py`** — empty

**`__main__.py`** — entry point: `python -m openclaw.mcp_server`
- Creates and runs the MCP server via stdio transport

**`server.py`** — MCP server setup
- Creates `mcp.Server("clarmi-tools")` instance
- Initializes DB engine from `openclaw.db.session`
- Registers all tools from tool modules
- Exports `create_server()` function

### 1.2 Create `src/openclaw/mcp_server/tools/` (9 modules, ~22 tools total)

Each tool is a thin wrapper calling existing integration clients and services. No business logic duplication.

**`scraping.py`**
- `scrape_website(url, max_pages=5)` — wraps `firecrawl_client.crawl()`
- `extract_branding(url)` — wraps `firecrawl_client.extract()` with brand schema

**`projects.py`**
- `create_project(name, brief)` — wraps `project_service.create_project()` (provisions GitHub + Vercel)
- `get_project_status(project_name?)` — ports `CEOAgent._get_status()` from `src/openclaw/agents/ceo.py:265-323`
- `update_project_status(project_id, status)` — wraps `project_service.update_project_status()`
- `list_projects(status?)` — wraps `project_service.list_projects()`

**`prospects.py`**
- `store_prospect(url, company_name, brand_colors, fonts, site_problems, ...)` — wraps `prospect_service.get_or_create_prospect()`
- `lookup_prospect(url?, company_name?)` — query Prospect table

**`design.py`**
- `generate_image(prompt, project_name, section)` — calls `google_ai.generate_image()` + `github_client.upload_file()` to `/public/assets/`
- `generate_video(prompt, project_name, duration=8)` — calls `google_ai.generate_video()` + `download_video()` + upload

**`engineering.py`**
- `scaffold_nextjs(project_name)` — ports scaffold logic from `src/openclaw/agents/engineer.py:180-338`
- `write_code(project_name, file_path, code)` — writes file to `{STORAGE_PATH}/{slug}/site/{file_path}`
- `verify_build(project_name)` — runs `npm install && npm run build` in project dir
- `deploy(project_name, commit_message)` — calls `github_client.push_directory()`, returns Vercel URL

**`qa.py`**
- `verify_url(url)` — HTTP check with retry + Vercel deployment state check
- `take_screenshot(url, viewport_widths=[1440,1024,768,375])` — Playwright screenshots
- `run_lighthouse(url)` — `npx lighthouse` headless, returns scores

**`email.py`**
- `draft_email(to, subject, body, project_id?)` — saves EmailLog with status="draft"
- `send_email(email_id)` — loads draft, calls `gmail_client.send_email()`, updates status

**`research.py`**
- `search_design_trends(sources?)` — scrapes trend sites
- `store_knowledge(category, title, content, source_url?, relevance_score?)` — saves to KnowledgeBase

**`learning.py`**
- `analyze_project(project_id)` — fetches project + tasks, returns analysis data
- `log_metrics(avg_lighthouse?, avg_fix_loops?, total_projects?, notes?)` — saves ImprovementMetric

### 1.3 Update `pyproject.toml`

Add: `mcp>=1.0.0`
Remove (Phase 4): `fastapi`, `uvicorn`, `redis`, `pywa`, `pyjwt`, `apscheduler`

---

## Phase 2: Create OpenClaw Configuration

### 2.1 Write `openclaw.json` (project root, copied to `~/.openclaw/` on setup)

Key config sections:
- `models.default` → Anthropic provider, claude-sonnet-4
- `channels.whatsapp` → enabled, ownerOnly
- `mcp.clarmi-tools` → `python -m openclaw.mcp_server`, env vars passed through from `.env`
- `agents.default.systemPrompt` → `./system-prompt.md`
- `cron` → research (0 */6 * * *), learning (0 3 * * *)

### 2.2 Write `system-prompt.md` (~3500 words)

Consolidates all 11 agent system prompts into one. Structure:
1. **Identity**: sole operator of Clarmi Design Studio
2. **Available Tools**: grouped by category with brief descriptions
3. **Website Pipeline**: Step 1 Research → Step 2 Design → Step 3 Build → Step 4 QA → Step 5 Outreach
4. **Owner Message Handling**: intent parsing (build/scrape/email/status)
5. **Quality Standards**: site problems, design direction, engineering standards, email rules
6. **Scoring/Gating**: QA score >= 85 to proceed, verify_build before deploy

Key source files for prompt content:
- `src/openclaw/agents/ceo.py:21-58` (orchestration logic)
- `src/openclaw/agents/inbound.py:11-100` (research expertise)
- `src/openclaw/agents/designer.py:14-73` (design philosophy)
- `src/openclaw/agents/engineer.py:16-79` (engineering standards)
- `src/openclaw/agents/qa.py:12-37` (QA methodology)
- `src/openclaw/agents/outbound.py:11-42` (email outreach)

### 2.3 Write `setup.sh`

1. Check prereqs (node, python3, docker)
2. `npm install -g openclaw@latest`
3. `openclaw onboard --install-daemon`
4. `pip install -e .`
5. `playwright install chromium`
6. `docker compose up -d` (PostgreSQL)
7. `alembic upgrade head`
8. Copy `.env.example` → `.env`, `openclaw.json` → `~/.openclaw/`

---

## Phase 3: Simplify Config & Docker

### 3.1 Update `docker-compose.yml`
Keep only `postgres` service. Remove: redis, api, workers-light, workers-heavy, clawdbot, all extra volumes.

### 3.2 Update `src/openclaw/config.py`
Remove: REDIS_URL, WA_*, OWNER_PHONE, CLAUDE_MODEL, OPENCLAW_CREDENTIALS_PATH, SKILLS_DIR, EC2_PUBLIC_IP, MAX_PARALLEL_PROJECTS, RESEARCH_*, LEARNING_*, DASHBOARD_SECRET, JWT_*, TASK_TIMEOUT_S, HEAVY_TASK_TIMEOUT_S
Keep: DATABASE_URL, GOOGLE_AI_API_KEY, FIRECRAWL_API_KEY, GMAIL_*, GITHUB_PAT, VERCEL_*, STORAGE_PATH, POSTGRES_PASSWORD, DEBUG, LOG_LEVEL

### 3.3 Update `.env.example`
Simplified — only DB + integration API keys.

---

## Phase 4: Remove Deprecated Code

Delete these directories/files:
- `src/openclaw/agents/` — all 13 files (logic in system prompt now)
- `src/openclaw/runtime/` — skill_base.py, skill_loader.py, skill_runner.py
- `src/openclaw/queue/` — producer.py, consumer.py, streams.py
- `src/openclaw/api/` — health.py, webhook.py, projects.py, dashboard.py, auth.py, chat_ws.py
- `src/openclaw/tools/` — messaging.py, whatsapp.py
- `src/openclaw/auth/` — if exists
- `src/openclaw/main.py` — FastAPI app
- `src/openclaw/autoscaler.py`
- `src/openclaw/schemas/` — API schemas
- `skills/` — all 11 skill directories
- `clawdbot/` — WhatsApp bridge
- `frontend/` — React dashboard
- `Dockerfile`, `Caddyfile`, `railway.toml`
- `deploy/`, `scripts/`
- `DEPLOY.md`

---

## Phase 5: Verification

1. `docker compose up -d` — PostgreSQL starts
2. `alembic upgrade head` — migrations run
3. `python -m openclaw.mcp_server` — server starts, lists all tools
4. `openclaw` — daemon starts, WhatsApp QR appears
5. Send "status" via WhatsApp → agent calls `get_project_status`, replies
6. Send "scrape https://example.com" → agent crawls, stores prospect, replies
7. Use Claude Code CLI: `openclaw chat "what projects do I have?"`
8. Full pipeline test: "build a website for [URL]" — runs research → design → build → QA → email draft

---

## Files Modified/Created Summary

| Action | Path |
|--------|------|
| CREATE | `src/openclaw/mcp_server/__init__.py` |
| CREATE | `src/openclaw/mcp_server/__main__.py` |
| CREATE | `src/openclaw/mcp_server/server.py` |
| CREATE | `src/openclaw/mcp_server/tools/__init__.py` |
| CREATE | `src/openclaw/mcp_server/tools/scraping.py` |
| CREATE | `src/openclaw/mcp_server/tools/projects.py` |
| CREATE | `src/openclaw/mcp_server/tools/prospects.py` |
| CREATE | `src/openclaw/mcp_server/tools/design.py` |
| CREATE | `src/openclaw/mcp_server/tools/engineering.py` |
| CREATE | `src/openclaw/mcp_server/tools/qa.py` |
| CREATE | `src/openclaw/mcp_server/tools/email.py` |
| CREATE | `src/openclaw/mcp_server/tools/research.py` |
| CREATE | `src/openclaw/mcp_server/tools/learning.py` |
| CREATE | `openclaw.json` |
| CREATE | `system-prompt.md` |
| CREATE | `setup.sh` |
| EDIT | `src/openclaw/config.py` — remove unused settings |
| EDIT | `docker-compose.yml` — PostgreSQL only |
| EDIT | `.env.example` — simplified |
| EDIT | `pyproject.toml` — add mcp, remove unused deps |
| DELETE | `src/openclaw/agents/`, `runtime/`, `queue/`, `api/`, `tools/`, `main.py`, `autoscaler.py`, `schemas/` |
| DELETE | `skills/`, `clawdbot/`, `frontend/`, `deploy/`, `scripts/` |
| DELETE | `Dockerfile`, `Caddyfile`, `railway.toml`, `DEPLOY.md` |
