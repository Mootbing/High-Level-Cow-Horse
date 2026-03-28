# OpenClaw — Railway Deployment Guide

Deploy the entire agency in ~10 minutes. No servers to manage.

---

## Architecture on Railway

```
Railway Project
├── PostgreSQL (plugin — managed)
├── Redis (plugin — managed)
├── api (service — FastAPI webhook + health)
└── workers (service — all 10 agents in one process)
```

Just 2 services + 2 plugins. Cost: ~$10-30/mo depending on API usage.

---

## Step 1: Create Railway Project

1. Go to **https://railway.app** → sign in with GitHub
2. Click **New Project → Empty Project**
3. Name it `openclaw`

---

## Step 2: Add PostgreSQL

1. Click **+ New** → **Database** → **PostgreSQL**
2. Done. Railway provisions it automatically.
3. Click the PostgreSQL service → **Variables** tab → copy `DATABASE_URL`
   - It looks like: `postgresql://postgres:xxx@xxx.railway.internal:5432/railway`
   - You'll need to change the scheme to `postgresql+asyncpg://` when setting env vars

---

## Step 3: Add Redis

1. Click **+ New** → **Database** → **Redis**
2. Done. Copy the `REDIS_URL` from the Variables tab.

---

## Step 4: Deploy the API Service

1. Click **+ New** → **GitHub Repo** → select `Mootbing/High-Level-Cow-Horse`
2. Railway will detect the Dockerfile and start building
3. Click the service → **Settings**:
   - **Service Name**: `api`
   - **Start Command**: `uvicorn openclaw.main:app --host 0.0.0.0 --port $PORT`
   - **Generate Domain**: click this to get a public URL (e.g., `openclaw-xxx.up.railway.app`)
4. Go to **Variables** tab → **Raw Editor** → paste all env vars (see Step 6)

---

## Step 5: Deploy the Workers Service

1. Click **+ New** → **GitHub Repo** → select `Mootbing/High-Level-Cow-Horse` again
2. Click the service → **Settings**:
   - **Service Name**: `workers`
   - **Start Command**: `python -m openclaw.agents.worker --all`
   - Do NOT generate a domain (workers don't need one)
3. Go to **Variables** tab → **Raw Editor** → paste the same env vars as the API

---

## Step 6: Set Environment Variables

Go to each service (api + workers) → **Variables** → **Raw Editor**, paste:

```env
# Database — copy from Railway PostgreSQL plugin, change scheme
# IMPORTANT: Replace "postgresql://" with "postgresql+asyncpg://"
DATABASE_URL=postgresql+asyncpg://postgres:xxx@xxx.railway.internal:5432/railway

# Redis — copy from Railway Redis plugin
REDIS_URL=redis://default:xxx@xxx.railway.internal:6379

# Anthropic (https://console.anthropic.com/settings/keys)
ANTHROPIC_API_KEY=sk-ant-...

# Google AI (https://aistudio.google.com/apikey)
GOOGLE_AI_API_KEY=AIza...

# Firecrawl (https://firecrawl.dev/app/api-keys)
FIRECRAWL_API_KEY=fc-...

# Vercel (https://vercel.com/account/tokens)
VERCEL_TOKEN=...
DEPLOY_DOMAIN=openclaw.site

# WhatsApp Business (see "WhatsApp Setup" below)
WA_VERIFY_TOKEN=pick-any-secret-string-here
WA_ACCESS_TOKEN=EAAG...
WA_PHONE_NUMBER_ID=1234567890
WA_APP_SECRET=abc123def...
OWNER_PHONE=+1234567890

# Gmail (see "Gmail Setup" below)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_SENDER_EMAIL=you@gmail.com

# Storage (Railway volume mount)
STORAGE_PATH=/data/projects
```

**Tip:** Railway lets you reference other services' variables. In the API and workers services, you can use:
- `${{Postgres.DATABASE_URL}}` — but remember to change the scheme manually
- `${{Redis.REDIS_URL}}`

---

## Step 7: Add Persistent Storage (Volume)

Both `api` and `workers` services need a volume for generated assets:

1. Click the **workers** service → **Settings** → **Volumes**
2. Click **+ Add Volume**
   - **Mount Path**: `/data/projects`
3. Repeat for the **api** service with the same mount path

---

## Step 8: Set Up WhatsApp Business

1. Go to **https://developers.facebook.com** → Create App → Business type
2. Add the **WhatsApp** product
3. In WhatsApp → Getting Started:
   - Note your **Phone Number ID** → `WA_PHONE_NUMBER_ID`
4. Generate a **permanent access token**:
   - Business Settings → System Users → Add
   - Generate token with `whatsapp_business_messaging` permission → `WA_ACCESS_TOKEN`
5. Note the **App Secret** (Settings → Basic) → `WA_APP_SECRET`
6. Pick any string for `WA_VERIFY_TOKEN`

---

## Step 9: Set Up Gmail API

1. Go to **https://console.cloud.google.com**
2. Create project → Enable **Gmail API**
3. Create OAuth 2.0 credentials (Desktop app type)
4. Note `client_id` and `client_secret`
5. Get refresh token:
   - Go to https://developers.google.com/oauthplayground
   - Settings gear → Use your own OAuth credentials
   - Authorize `https://www.googleapis.com/auth/gmail.send`
   - Exchange code for tokens → copy `refresh_token`

---

## Step 10: Configure WhatsApp Webhook

1. Get your API service URL from Railway (e.g., `https://openclaw-xxx.up.railway.app`)
2. Go to **Meta Developer Dashboard → WhatsApp → Configuration**
3. **Webhook URL**: `https://openclaw-xxx.up.railway.app/api/webhook`
4. **Verify token**: paste the same string from `WA_VERIFY_TOKEN`
5. Click **Verify and Save**
6. Subscribe to the **messages** webhook field

---

## Step 11: Test It

Send a WhatsApp message to your business number:

> "Hello, what can you do?"

The CEO agent should respond in 10-30 seconds.

Try:
- `"Build a landing page for CryptoVault, dark theme, vault opening hero video"`
- `"Scrape https://example.com"`
- `"Status update"`

---

## Verify Health

```bash
curl https://openclaw-xxx.up.railway.app/api/health
```

Expected:
```json
{"status": "healthy", "checks": {"api": "ok", "postgres": "ok", "redis": "ok"}}
```

---

## Ongoing Operations

### View logs
- Railway Dashboard → click any service → **Logs** tab

### Redeploy
- Just `git push` — Railway auto-deploys from GitHub

### Scale up
- Click a service → **Settings** → adjust vCPU / RAM
- Workers default: 1 vCPU / 1GB RAM (sufficient for most usage)
- If running many concurrent projects, bump workers to 2 vCPU / 2GB RAM

### Database backup
- Railway Dashboard → PostgreSQL service → **Data** tab → **Backup**

---

## Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| Railway Hobby plan | $5 |
| PostgreSQL (500MB) | ~$1 |
| Redis (50MB) | ~$1 |
| API service (idle most of the time) | ~$2-5 |
| Workers service (spikes during projects) | ~$5-15 |
| Anthropic API | ~$20-100 (usage) |
| Google AI | ~$10-50 (usage) |
| Firecrawl | Free tier: 500 pages/mo |
| Vercel | Free tier: 100 deploys/mo |
| WhatsApp Business | Free: 1,000 convos/mo |
| Gmail API | Free |
| **Total** | **~$45-175/mo** |

---

## Troubleshooting

**Agent not responding:**
- Check workers service logs in Railway dashboard
- Verify all env vars are set (especially `ANTHROPIC_API_KEY`)
- Check Redis is connected (health endpoint)

**Webhook verification failing:**
- Make sure the API service has a public domain generated
- Verify `WA_VERIFY_TOKEN` matches in both Railway env vars and Meta dashboard

**Build failing:**
- Check build logs in Railway — usually a missing dependency
- Playwright install can be slow (~2 min) but works

**Out of memory:**
- Bump workers service to 2GB RAM in Railway settings
- Railway auto-restarts crashed services
