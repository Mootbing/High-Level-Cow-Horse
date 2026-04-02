# New Worker Setup

You've got the project cloned and dependencies installed (see SETUP.md). This guide covers setting up a new worker machine — getting your own API keys, connecting MCP tools, and verifying everything works.

## What you need

A "worker" is any machine running Claude Code against this repo. Each worker needs its own set of API keys in `.env`. The project code and database are shared, but keys are per-worker.

## 1. Get your API keys

### Required keys

| Key | What it does | How to get it |
|-----|-------------|---------------|
| `ANTHROPIC_API_KEY` | Powers the Claude agent | [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key |
| `GITHUB_PAT` | Creates repos for client sites, pushes code | GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained token. **Scopes needed:** `repo` (full), `read:org`. Set resource owner to the `jason-clarmi` org. |
| `VERCEL_TOKEN` | Deploys client sites to Vercel | [vercel.com/account/tokens](https://vercel.com/account/tokens) → Create Token. Must have access to the `jason-8343s-projects` team. |
| `GOOGLE_AI_API_KEY` | Generates images (Nano Banana) and videos (Veo 3.1) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Create API Key |
| `DATABASE_URL` | Shared project database (Neon PostgreSQL) | Ask the project owner for the connection string. Format: `postgresql+asyncpg://user:pass@host/db?ssl=require` |

### Optional keys

| Key | What it does | How to get it |
|-----|-------------|---------------|
| `GOOGLE_PLACES_API_KEY` | Competitor analysis + lead discovery | [console.cloud.google.com](https://console.cloud.google.com) → Enable "Places API" → Create credentials → API Key |
| `GMAIL_CLIENT_ID` | Email outreach (drafting + sending) | Google Cloud Console → OAuth2 → Create credentials for Gmail API |
| `GMAIL_CLIENT_SECRET` | Email outreach | Same as above |
| `GMAIL_REFRESH_TOKEN` | Email outreach | Run the OAuth2 flow once to get a refresh token |
| `GMAIL_SENDER_EMAIL` | The "from" address on outreach emails | Your Gmail/Google Workspace address |

Without the optional keys, the agent still builds sites — it just can't do competitor analysis, lead generation, or email outreach.

## 2. Create your `.env`

```bash
cp .env.example .env
```

Fill in your keys. At minimum:

```bash
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=AIzaSy...
GITHUB_PAT=ghp_...
VERCEL_TOKEN=vcp_...
DATABASE_URL=postgresql+asyncpg://...

# Leave these as-is unless you have a reason to change them
STORAGE_PATH=/tmp/openclaw-projects
DEPLOY_DOMAIN=openclaw.site
```

## 3. Verify GitHub PAT

```bash
# Check the token works and shows the right user/org
curl -s -H "Authorization: token YOUR_PAT" https://api.github.com/user | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'User: {d[\"login\"]}')"

# Check org access
curl -s -H "Authorization: token YOUR_PAT" https://api.github.com/orgs/jason-clarmi | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Org: {d.get(\"login\", \"NO ACCESS\")}')"
```

If the org check fails, the PAT needs to be created with `jason-clarmi` as the resource owner.

## 4. Verify Vercel token

```bash
vercel whoami --token YOUR_TOKEN
vercel teams list --token YOUR_TOKEN
```

You should see `jason-8343s-projects` in the teams list. If not, ask the project owner to invite your Vercel account to the team.

## 5. Verify MCP tools connect

Open the project in Claude Code. The `.mcp.json` file auto-registers two MCP servers:

- **clarmi-tools** — The Python tool server (ingest, build, deploy, design, QA, etc.)
- **reactbits** — Component library for animated React components

Check they're connected by asking Claude Code:

```
list_projects()
```

If you get a response (even an empty list), the MCP server is working.

### If clarmi-tools fails to connect

1. Make sure Python deps are installed: `pip install -e .`
2. Test the server directly: `PYTHONPATH=src python3 -m openclaw.mcp_server`
3. Check the database is reachable: `PYTHONPATH=src python3 -c "from openclaw.config import settings; print(settings.database_url)"`

### If reactbits fails to connect

```bash
npx reactbits-dev-mcp-server
```

If it errors, install it: `npm install -g reactbits-dev-mcp-server`

## 6. Set up Playwright (for QA)

```bash
playwright install chromium
playwright install-deps chromium
```

On headless Linux servers you may also need:

```bash
apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1
```

Note: Playwright running as root requires `--no-sandbox` mode. The QA tools handle this automatically.

## 7. Create project storage

```bash
mkdir -p /tmp/openclaw-projects
```

Or set `STORAGE_PATH` in `.env` to a persistent directory if you want project files to survive reboots.

## 8. Test the full pipeline

Run a quick test to verify everything works end-to-end:

1. Open the project in Claude Code
2. Say: `list_projects()` — should return a list
3. Say: `create_project("test-worker-check", "Verify worker setup")` — should create a GitHub repo + Vercel project
4. Delete the test project from GitHub and Vercel when done

## Summary

| What | Shared or per-worker |
|------|---------------------|
| Database (Neon) | Shared — all workers read/write the same DB |
| GitHub org (`jason-clarmi`) | Shared — all workers create repos here |
| Vercel team | Shared — all workers deploy here |
| `.env` keys | Per-worker — each machine has its own |
| `STORAGE_PATH` files | Per-worker — local project files |
| CLAUDE.md / templates | Shared — checked into the repo |

## GitHub PAT permissions cheat sheet

When creating a fine-grained PAT for this project:

- **Resource owner:** `jason-clarmi` (not your personal account)
- **Repository access:** All repositories
- **Permissions:**
  - Contents: Read and write
  - Metadata: Read-only
  - Administration: Read and write (needed for repo creation)
