# OpenClaw EC2 Deployment Guide

## Prerequisites

Before you start, have these ready:
- AWS account with EC2 access
- A domain name (e.g., `openclaw.yourdomain.com`)
- API keys for: Anthropic, Google AI, Firecrawl, Vercel, Meta WhatsApp Business

---

## Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. Settings:
   - **Name**: `openclaw`
   - **AMI**: Ubuntu 24.04 LTS (64-bit)
   - **Instance type**: `t3.medium` (2 vCPU, 4GB RAM) — ~$30/mo
   - **Key pair**: Create or select one (you'll need this to SSH in)
   - **Security group**: Allow these inbound rules:
     - SSH (port 22) — your IP only
     - HTTP (port 80) — anywhere
     - HTTPS (port 443) — anywhere
   - **Storage**: 30 GB gp3
3. Click **Launch Instance**
4. Note the **Public IP** (e.g., `54.123.45.67`)

---

## Step 2: Point Your Domain

Go to your DNS provider (Cloudflare, Namecheap, Route53, etc.):

```
Type: A
Name: openclaw (or whatever subdomain)
Value: 54.123.45.67  ← your EC2 public IP
TTL: Auto
```

Wait a few minutes for DNS propagation.

---

## Step 3: SSH In and Run Setup

```bash
ssh -i your-key.pem ubuntu@54.123.45.67
```

Once connected:

```bash
# Clone the repo
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/Mootbing/High-Level-Cow-Horse.git /tmp/openclaw
sudo mv /tmp/openclaw /opt/openclaw
cd /opt/openclaw

# Run the bootstrap script (installs Docker, Caddy, everything)
sudo bash scripts/setup-ec2.sh
```

---

## Step 4: Configure Environment

```bash
cd /opt/openclaw
cp .env.example .env
nano .env
```

Fill in ALL these values:

```env
# === REQUIRED ===

# Anthropic (https://console.anthropic.com/settings/keys)
ANTHROPIC_API_KEY=sk-ant-...

# Google AI — for Nano Banana + Veo (https://aistudio.google.com/apikey)
GOOGLE_AI_API_KEY=AIza...

# Firecrawl (https://firecrawl.dev/app/api-keys)
FIRECRAWL_API_KEY=fc-...

# Vercel (https://vercel.com/account/tokens)
VERCEL_TOKEN=...
DEPLOY_DOMAIN=openclaw.site

# WhatsApp Business — see Step 5 below
WA_VERIFY_TOKEN=pick-any-secret-string
WA_ACCESS_TOKEN=EAAG...
WA_PHONE_NUMBER_ID=1234567890
WA_APP_SECRET=abc123...
OWNER_PHONE=+1234567890  ← your WhatsApp number, with country code

# Gmail (https://console.cloud.google.com → APIs → Gmail)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_SENDER_EMAIL=you@gmail.com

# Database password (pick something strong)
POSTGRES_PASSWORD=pick-a-strong-password-here
DATABASE_URL=postgresql+asyncpg://openclaw:pick-a-strong-password-here@postgres:5432/openclaw
```

---

## Step 5: Set Up WhatsApp Business

1. Go to **https://developers.facebook.com** → Create App → Business type
2. Add the **WhatsApp** product
3. In WhatsApp → Getting Started:
   - Note your **Phone Number ID** → `WA_PHONE_NUMBER_ID`
   - Note your **WhatsApp Business Account ID**
4. Generate a **permanent access token**:
   - Go to Business Settings → System Users → Add
   - Generate token with `whatsapp_business_messaging` permission → `WA_ACCESS_TOKEN`
5. Note the **App Secret** (Settings → Basic) → `WA_APP_SECRET`
6. Pick any string for `WA_VERIFY_TOKEN` (you'll use this in Step 7)

---

## Step 6: Set Up Gmail API

1. Go to **https://console.cloud.google.com**
2. Create a project → Enable **Gmail API**
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials → note `client_id` and `client_secret`
5. Get a refresh token using the OAuth playground:
   - Go to https://developers.google.com/oauthplayground
   - Settings gear → Use your own OAuth credentials → paste client_id/secret
   - Authorize `https://www.googleapis.com/auth/gmail.send`
   - Exchange authorization code for tokens
   - Copy the **refresh_token** → `GMAIL_REFRESH_TOKEN`

---

## Step 7: Configure Caddy (HTTPS)

```bash
# Update Caddy with your actual domain
sudo nano /etc/caddy/Caddyfile
```

Replace the contents with:
```
openclaw.yourdomain.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl reload caddy
```

Caddy will auto-provision a Let's Encrypt SSL certificate. Takes ~30 seconds.

---

## Step 8: Launch OpenClaw

```bash
cd /opt/openclaw

# Start everything
sudo docker compose up -d

# Watch the logs to verify startup
sudo docker compose logs -f api agent-ceo
```

You should see:
```
api       | INFO: Uvicorn running on http://0.0.0.0:8000
agent-ceo | worker_started agent=ceo consumer=ceo-a1b2c3d4
```

Wait ~60 seconds for all 12 containers to start, then verify:

```bash
# Check all services are running
sudo docker compose ps

# Test the health endpoint
curl https://openclaw.yourdomain.com/api/health
```

Expected: `{"status": "healthy", "checks": {"api": "ok", "postgres": "ok", "redis": "ok"}}`

---

## Step 9: Configure WhatsApp Webhook

1. Go to **Meta Developer Dashboard → WhatsApp → Configuration**
2. Webhook URL: `https://openclaw.yourdomain.com/api/webhook`
3. Verify token: paste the same string you put in `WA_VERIFY_TOKEN`
4. Click **Verify and Save**
5. Subscribe to the `messages` webhook field

---

## Step 10: Test It

Send a WhatsApp message to your business phone number:

> "Hello, what can you do?"

The CEO agent should respond within 10-30 seconds.

Try these commands:
- `"Build a landing page for CryptoVault, dark theme, vault opening hero video"`
- `"Scrape https://example.com"`
- `"What's the status of all projects?"`

---

## Ongoing Operations

### View logs
```bash
sudo docker compose logs -f agent-ceo       # CEO agent
sudo docker compose logs -f agent-designer   # Designer agent
sudo docker compose logs -f agent-engineer   # Engineer agent
sudo docker compose logs -f                  # All services
```

### Restart a service
```bash
sudo docker compose restart agent-ceo
```

### Restart everything
```bash
cd /opt/openclaw
sudo docker compose down
sudo docker compose up -d
```

### Update code
```bash
cd /opt/openclaw
git pull origin main
sudo docker compose build
sudo docker compose up -d
```

### Check disk space
```bash
df -h
sudo docker system prune -f  # Clean unused images
```

### Database backup
```bash
sudo docker compose exec postgres pg_dump -U openclaw openclaw > backup-$(date +%Y%m%d).sql
```

---

## Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| EC2 t3.medium | ~$30 |
| Anthropic API (Claude Sonnet) | ~$20-100 (usage-based) |
| Google AI (Nano Banana + Veo) | ~$10-50 (usage-based) |
| Firecrawl | Free tier: 500 pages/mo |
| Vercel | Free tier: 100 deploys/mo |
| WhatsApp Business | Free: 1,000 conversations/mo |
| Gmail API | Free |
| Domain | ~$10/yr |
| **Total** | **~$60-190/mo** |

---

## Troubleshooting

**Agent not responding on WhatsApp:**
```bash
# Check CEO agent is running
sudo docker compose ps agent-ceo
sudo docker compose logs --tail=50 agent-ceo

# Check webhook is reachable
curl https://openclaw.yourdomain.com/api/health
```

**Container keeps restarting:**
```bash
sudo docker compose logs --tail=100 <service-name>
# Usually a missing env var or wrong API key
```

**Out of memory:**
```bash
# Upgrade to t3.large (8GB RAM) if running many concurrent projects
# Or add swap:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**SSL certificate not working:**
```bash
sudo systemctl status caddy
sudo caddy validate --config /etc/caddy/Caddyfile
# Make sure DNS is pointing to this server's IP
```
