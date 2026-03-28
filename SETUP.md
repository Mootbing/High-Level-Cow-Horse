# OpenClaw Setup Guide

Complete step-by-step setup. Follow in order — each step depends on the previous one.

---

## What You're Building

```
YOU (WhatsApp message)
 → CEO Agent (parses your intent)
   → PM Agent (creates task plan)
     → Designer (Nano Banana keyframes + Veo hero videos)
     → Engineer (builds Next.js site, deploys to Vercel)
     → QA (Playwright testing + Lighthouse audit)
   → Inbound Agent (Firecrawl: scrapes prospect websites)
   → Outbound Agent (Gmail: sends cold outreach emails)
   → Research Agent (auto every 6h: scrapes design trends)
   → Learning Agent (auto: improves prompts from past projects)
```

All running on Railway. Auto-scales when you have multiple projects in progress.

---

## What You'll Need

Accounts to create (all have free tiers):

- [ ] **Railway** account — https://railway.app
- [ ] **Anthropic** API key — https://console.anthropic.com
- [ ] **Google AI Studio** API key — https://aistudio.google.com/apikey
- [ ] **Firecrawl** API key — https://firecrawl.dev
- [ ] **Vercel** account + token — https://vercel.com
- [ ] **Meta Developer** account — https://developers.facebook.com
- [ ] **Google Cloud** project (for Gmail API) — https://console.cloud.google.com

Budget: ~$5-10/mo for Railway infra + API costs based on usage.

---

## Part 1: Get Your API Keys

Do this first so you have everything ready when Railway asks for env vars.

### 1.1 — Anthropic API Key

1. Go to https://console.anthropic.com/settings/keys
2. Click **Create Key**
3. Save it: `sk-ant-api03-...`

### 1.2 — Google AI API Key (for Nano Banana + Veo)

1. Go to https://aistudio.google.com/apikey
2. Click **Create API Key**
3. Save it: `AIza...`

### 1.3 — Firecrawl API Key

1. Go to https://firecrawl.dev
2. Sign up → go to https://firecrawl.dev/app/api-keys
3. Create a key
4. Save it: `fc-...`

### 1.4 — Vercel Token

1. Go to https://vercel.com/account/tokens
2. Create a token with full access
3. Save it

### 1.5 — WhatsApp Business Setup

This is the longest step (~15 min). You need a Meta Business account.

1. Go to https://developers.facebook.com
2. Click **My Apps** → **Create App**
3. Choose **Business** type → name it "OpenClaw" → Create
4. On the app dashboard, find **WhatsApp** → click **Set Up**
5. You'll see a test phone number. Go to **WhatsApp → API Setup**:
   - Copy the **Phone Number ID** → save as `WA_PHONE_NUMBER_ID`
6. Get a permanent token:
   - Go to **Business Settings** (business.facebook.com) → **System Users**
   - Click **Add** → name it "openclaw-bot" → role: Admin
   - Click **Generate Token** → select your app → check `whatsapp_business_messaging`
   - Copy the token → save as `WA_ACCESS_TOKEN`
7. Get the App Secret:
   - In your app dashboard → **Settings** → **Basic**
   - Show and copy **App Secret** → save as `WA_APP_SECRET`
8. Pick any random string for `WA_VERIFY_TOKEN` (e.g., `openclaw-verify-2024`)
   - You'll use this exact string later when setting up the webhook

### 1.6 — Gmail API Setup

1. Go to https://console.cloud.google.com
2. Create a new project called "openclaw"
3. Go to **APIs & Services** → **Enable APIs** → search for **Gmail API** → Enable
4. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Name: "openclaw"
   - Click Create
   - Copy **Client ID** → save as `GMAIL_CLIENT_ID`
   - Copy **Client Secret** → save as `GMAIL_CLIENT_SECRET`
5. Go to **OAuth consent screen** → set to **External** → add your email as test user
6. Get a refresh token:
   - Go to https://developers.google.com/oauthplayground
   - Click the **gear icon** (top right) → check **"Use your own OAuth credentials"**
   - Paste your Client ID and Client Secret
   - In the left panel, scroll to **Gmail API v1** → select `https://www.googleapis.com/auth/gmail.send`
   - Click **Authorize APIs** → sign in → grant access
   - Click **Exchange authorization code for tokens**
   - Copy the **Refresh Token** → save as `GMAIL_REFRESH_TOKEN`

---

## Part 2: Deploy to Railway

### 2.1 — Create the Project

1. Go to https://railway.app → sign in with GitHub
2. Click **New Project** → **Empty Project**
3. Name it `openclaw`

### 2.2 — Add PostgreSQL

1. In your project, click **+ New** → **Database** → **PostgreSQL**
2. Wait for it to provision (~10 seconds)
3. Click the Postgres service → **Connect** tab
4. Copy the **DATABASE_URL** — it looks like:
   ```
   postgresql://postgres:AbCdEf@monorail.proxy.rlwy.net:12345/railway
   ```
5. **Important:** You'll need to change `postgresql://` to `postgresql+asyncpg://` when pasting into env vars

### 2.3 — Add Redis

1. Click **+ New** → **Database** → **Redis**
2. Wait for provision
3. Click the Redis service → **Connect** tab
4. Copy the **REDIS_URL**

### 2.4 — Deploy the API

1. Click **+ New** → **GitHub Repo**
2. Select **Mootbing/High-Level-Cow-Horse**
3. Railway starts building (takes ~3 min first time due to Playwright + Node.js)
4. While it builds, click the service → **Settings**:
   - Change **Service Name** to `api`
   - Set **Start Command** to:
     ```
     uvicorn openclaw.main:app --host 0.0.0.0 --port $PORT
     ```
   - Click **Generate Domain** → you'll get something like `openclaw-production-abc.up.railway.app`
   - **Save this URL** — you need it for the WhatsApp webhook

### 2.5 — Deploy Light Workers

1. Click **+ New** → **GitHub Repo** → select the same repo again
2. Click the service → **Settings**:
   - **Service Name**: `workers-light`
   - **Start Command**:
     ```
     python -m openclaw.agents.worker --tier light
     ```
   - Do NOT generate a domain (this service doesn't need one)

### 2.6 — Deploy Heavy Workers

1. Click **+ New** → **GitHub Repo** → select the same repo again
2. Click the service → **Settings**:
   - **Service Name**: `workers-heavy`
   - **Start Command**:
     ```
     python -m openclaw.agents.worker --tier heavy
     ```
   - Do NOT generate a domain
3. **Copy the Service ID** from the URL bar. When you click on this service, the URL looks like:
   ```
   https://railway.app/project/xxxx/service/THIS-IS-THE-SERVICE-ID
   ```
   Save this ID — you need it for auto-scaling.

### 2.7 — Add Storage Volumes

Generated assets (images, videos, site builds) need persistent storage:

1. Click **workers-light** → **Settings** → scroll to **Volumes** → **+ Add Volume**
   - Mount Path: `/data/projects`
2. Click **workers-heavy** → **Settings** → **Volumes** → **+ Add Volume**
   - Mount Path: `/data/projects`

### 2.8 — Get Railway API Token (for auto-scaling)

1. Go to https://railway.app/account/tokens
2. Create a new token called "openclaw-autoscaler"
3. Save it

---

## Part 3: Set Environment Variables

### 3.1 — Prepare your env vars

Fill in this template with all the keys you collected:

```env
# Database (from Railway Postgres — CHANGE THE SCHEME)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway

# Redis (from Railway Redis — paste as-is)
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST:PORT

# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# Google AI
GOOGLE_AI_API_KEY=AIza...

# Firecrawl
FIRECRAWL_API_KEY=fc-...

# Vercel
VERCEL_TOKEN=your-vercel-token
DEPLOY_DOMAIN=openclaw.site

# WhatsApp
WA_VERIFY_TOKEN=openclaw-verify-2024
WA_ACCESS_TOKEN=EAAG...
WA_PHONE_NUMBER_ID=123456789012345
WA_APP_SECRET=abcdef123456
OWNER_PHONE=+12125551234

# Gmail
GMAIL_CLIENT_ID=123456-abc.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-...
GMAIL_REFRESH_TOKEN=1//0abc...
GMAIL_SENDER_EMAIL=you@gmail.com

# Storage
STORAGE_PATH=/data/projects
```

### 3.2 — Paste into all 3 services

Go to **each service** (api, workers-light, workers-heavy) → **Variables** tab → **Raw Editor** → paste the block above.

### 3.3 — Add auto-scaling vars to workers-light ONLY

Go to **workers-light** → **Variables** → add these additional vars:

```env
RAILWAY_API_TOKEN=your-railway-token-from-step-2.8
RAILWAY_HEAVY_SERVICE_ID=the-service-id-from-step-2.6
AUTOSCALE_ENABLED=true
AUTOSCALE_MIN_REPLICAS=1
AUTOSCALE_MAX_REPLICAS=5
AUTOSCALE_QUEUE_THRESHOLD=3
AUTOSCALE_POLL_SECONDS=60
```

### 3.4 — Redeploy

After setting all env vars, each service will auto-redeploy. Wait for all 3 to show **green/active**.

---

## Part 4: Connect WhatsApp Webhook

1. Go to https://developers.facebook.com → your app → **WhatsApp** → **Configuration**
2. Under **Webhook**, click **Edit**
3. Set:
   - **Callback URL**: `https://YOUR-RAILWAY-URL.up.railway.app/api/webhook`
   - **Verify token**: paste your `WA_VERIFY_TOKEN` (e.g., `openclaw-verify-2024`)
4. Click **Verify and Save**
   - If it fails: check the API service is running and the URL is correct
5. Under **Webhook fields**, click **Manage** → subscribe to **messages**

---

## Part 5: Test Everything

### 5.1 — Health check

Open in browser or curl:
```
https://YOUR-RAILWAY-URL.up.railway.app/api/health
```

You should see:
```json
{"status": "healthy", "checks": {"api": "ok", "postgres": "ok", "redis": "ok"}}
```

If postgres or redis say error → double-check your DATABASE_URL and REDIS_URL env vars.

### 5.2 — Send your first WhatsApp message

Send a message to your WhatsApp Business number:

> Hello, what can you do?

The CEO agent should reply in 10-30 seconds.

### 5.3 — Try real commands

- **Build a website**: "Build a landing page for CryptoVault, dark theme with a vault opening hero video"
- **Scrape a prospect**: "Scrape https://stripe.com and extract their branding"
- **Send outreach**: "Send an outreach email to the stripe.com contact"
- **Check status**: "What's the status of all projects?"

---

## Part 6: Ongoing Operations

### View logs
Railway Dashboard → click any service → **Logs** tab

### Redeploy after code changes
```bash
git push origin main
```
Railway auto-deploys all 3 services.

### Monitor auto-scaling
Check **workers-light** logs — you'll see:
```
autoscaler_started  poll_seconds=60  min=1  max=5  threshold=3
autoscaler_check    depths={"designer": 0, "engineer": 0, "qa": 0}  total=0  replicas=1
```

When projects are running:
```
scaling  depths={"designer": 2, "engineer": 3, "qa": 1}  total=6  current=1  desired=2
replicas_set  count=2
```

### Manually scale
If you want to force more heavy workers:
- Click **workers-heavy** → **Settings** → increase replicas
- Or set `AUTOSCALE_MIN_REPLICAS=2` in workers-light env vars

### Database backup
Railway Dashboard → PostgreSQL → **Data** tab → **Backup**

### Check costs
Railway Dashboard → **Usage** tab → see per-service breakdown

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| WhatsApp message sent but no reply | Check workers-light logs. Is ANTHROPIC_API_KEY set? |
| Webhook verification fails | Check API service is running. URL must be HTTPS. WA_VERIFY_TOKEN must match exactly. |
| "postgres: error" in health check | DATABASE_URL must start with `postgresql+asyncpg://` (not `postgresql://`) |
| Build takes forever | Normal for first build (~3 min). Playwright + Node.js install is large. |
| Workers crash loop | Check logs — usually a missing env var or bad API key |
| Auto-scaling not working | Check RAILWAY_API_TOKEN and RAILWAY_HEAVY_SERVICE_ID are set on workers-light |
| Generated images/videos lost after redeploy | Make sure volumes are attached (Step 2.7) |

---

## Cost Estimate

| What | Cost |
|------|------|
| Railway (Hobby plan) | $5/mo |
| PostgreSQL + Redis | ~$2/mo |
| API service | ~$2-5/mo |
| Workers-light (always on) | ~$3-8/mo |
| Workers-heavy (scales to demand) | ~$2-15/mo |
| **Railway subtotal** | **~$15-35/mo** |
| Anthropic API | $20-100/mo (usage) |
| Google AI (Nano Banana + Veo) | $10-50/mo (usage) |
| Firecrawl | Free (500 pages/mo) |
| Vercel | Free (100 deploys/mo) |
| WhatsApp | Free (1,000 convos/mo) |
| Gmail | Free |
| **Total** | **~$45-185/mo** |

Scales with how many websites you're building. If you're idle, it's ~$20/mo.
