# macOS Server Setup — 24/7 iMessage Agent

How to set up a Mac as an always-on server that receives iMessages and routes `/clarmi` commands to Claude with full MCP tool access.

## Architecture

```
Your iPhone
    |  iMessage (via iCloud)
    v
Mac mini (always on)
    |
    ├── Messages.app          Syncs iMessages via Apple ID
    ├── Photon iMessage Server Reads Messages DB, exposes Socket.IO API on :1234
    ├── Clarmi TS Listener     Connects to Photon, filters /clarmi, forwards to webhook
    ├── Clarmi FastAPI          Webhook at :8000, dispatches to Claude CLI with MCP tools
    └── Claude CLI             Processes messages, calls MCP tools, returns reply
```

## Prerequisites

- **Mac mini** (or any Mac that stays on 24/7) — M1 or later recommended
- **macOS 14+** (Sonoma or later)
- **Apple ID** signed into Messages.app with your phone number
- **iCloud Messages** enabled (Settings > Apple ID > iCloud > Messages)
- **Node.js 18+** — `brew install node`
- **Python 3.12+** — `brew install python@3.12`
- **pm2** — `npm install -g pm2`
- **Claude Code CLI** — `npm install -g @anthropic-ai/claude-code` and authenticated via `claude auth login`
- **Photon iMessage Server** — enterprise license from [photon.codes](https://photon.codes) or use the free [imessage-kit](https://github.com/photon-hq/imessage-kit)

## 1. Mac System Setup

### Prevent Sleep

The Mac must never sleep. Open **System Settings > Energy**:

```
Prevent automatic sleeping when the display is off: ON
Wake for network access: ON
Start up automatically after a power failure: ON
```

Or via terminal:

```bash
# Prevent sleep entirely (survives reboot if set via pmset)
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 0

# Wake on network access
sudo pmset -a womp 1

# Auto-restart after power failure
sudo pmset -a autorestart 1
```

### Enable Auto-Login

System Settings > Users & Groups > Login Options:
- Automatic login: select your user account

This ensures the Mac boots into a logged-in session after power loss, so Messages.app and all services can start.

### Enable SSH (for remote management)

System Settings > General > Sharing > Remote Login: ON

```bash
# Test from another machine
ssh user@mac-mini.local
```

### Configure Messages.app

1. Open Messages.app
2. Sign in with your Apple ID (same one as your iPhone)
3. Settings > iMessage > Enable Messages in iCloud
4. Verify your phone number appears under "You can be reached at"
5. Send a test message from your iPhone — it should appear on the Mac

## 2. Photon iMessage Server

The Photon server is the bridge between Messages.app and the SDK. It reads the Messages database and exposes a Socket.IO + REST API.

### Option A: Photon Enterprise (recommended)

Contact [daniel@photon.codes](mailto:daniel@photon.codes) or visit [photon.codes](https://photon.codes) to get:
- A provisioned iMessage number (or use your own)
- The server binary
- An API key

Install and run:

```bash
# Follow Photon's setup instructions for the server binary
# The server runs on port 1234 by default
```

### Option B: Free imessage-kit Server

The open-source alternative:

```bash
git clone https://github.com/photon-hq/imessage-kit.git
cd imessage-kit
# Follow the imessage-kit README for server setup
```

### Grant Permissions

The iMessage server needs **Full Disk Access** to read the Messages database:

1. System Settings > Privacy & Security > Full Disk Access
2. Add the server binary (or Terminal.app if running from terminal)
3. Also grant **Accessibility** access if prompted

### Verify Server is Running

```bash
curl http://localhost:1234/api/v1/server/info
```

Should return server version and status.

## 3. Clone the Clarmi Repo

```bash
cd /Users/Shared
git clone https://github.com/jason-clarmi/High-Level-Cow-Horse.git
cd High-Level-Cow-Horse
```

## 4. Install Dependencies

```bash
# Python backend
python3 -m pip install -e .

# Build the iMessage SDK (local dependency)
cd advanced-imessage-kit
npm install && npx tsup
cd ..

# iMessage listener
cd src/imessage-agent
npm install
npm run build
cd ../..
```

## 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — the iMessage-specific vars:

```bash
# iMessage Agent
IMESSAGE_SERVER_URL=http://localhost:1234    # Photon server address
IMESSAGE_API_KEY=your-photon-api-key        # Leave empty if no auth
IMESSAGE_WEBHOOK_SECRET=generate-a-secret   # Shared secret between TS listener and FastAPI
OWNER_PHONE=90856665143                     # Your phone number (no +, no dashes)
```

Generate a webhook secret:

```bash
openssl rand -hex 32
```

The TS listener reads from its own `.env` or inherits from the project root. Create `src/imessage-agent/.env`:

```bash
IMESSAGE_SERVER_URL=http://localhost:1234
IMESSAGE_API_KEY=
CLARMI_WEBHOOK_URL=http://localhost:8000/api/v1/imessage/incoming
IMESSAGE_WEBHOOK_SECRET=same-secret-as-above
```

## 6. Database Migration

```bash
alembic upgrade head
```

This adds the `channel` column and renames `wa_message_id` to `external_message_id` in the messages table.

## 7. Authenticate Claude CLI

The agent service shells out to `claude` CLI. It must be authenticated:

```bash
claude auth login
```

Follow the OAuth flow. Verify it works:

```bash
claude -p "Say hello" --output-format json
```

## 8. Start All Services

### Option A: pm2 (recommended)

Create a unified ecosystem file at the project root:

```bash
cat > ecosystem.config.cjs << 'EOF'
module.exports = {
  apps: [
    {
      name: "clarmi-api",
      script: "python3",
      args: "-m uvicorn openclaw.api.app:app --host 0.0.0.0 --port 8000",
      cwd: "/Users/Shared/High-Level-Cow-Horse",
      env: {
        PYTHONPATH: "src",
      },
      autorestart: true,
      max_restarts: 20,
      restart_delay: 5000,
    },
    {
      name: "clarmi-imessage",
      script: "dist/index.js",
      cwd: "/Users/Shared/High-Level-Cow-Horse/src/imessage-agent",
      autorestart: true,
      max_restarts: 50,
      restart_delay: 5000,
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};
EOF
```

Start everything:

```bash
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup
```

`pm2 startup` generates a launchd command — run the command it outputs to auto-start pm2 on boot.

### Option B: launchd (native macOS)

Create a plist for each service. Example for the iMessage listener:

```bash
cat > ~/Library/LaunchAgents/com.clarmi.imessage-agent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clarmi.imessage-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>/Users/Shared/High-Level-Cow-Horse/src/imessage-agent/dist/index.js</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/High-Level-Cow-Horse/src/imessage-agent</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/clarmi-imessage.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/clarmi-imessage.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>NODE_ENV</key>
        <string>production</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.clarmi.imessage-agent.plist
```

## 9. Verify Everything Works

### Check services are running

```bash
pm2 status
```

Expected output:

```
┌────┬──────────────────────┬──────┬────────┬───────┐
│ id │ name                 │ mode │ status │ cpu   │
├────┼──────────────────────┼──────┼────────┼───────┤
│ 0  │ clarmi-api           │ fork │ online │ 0.5%  │
│ 1  │ clarmi-imessage      │ fork │ online │ 0.1%  │
└────┴──────────────────────┴──────┴────────┴───────┘
```

### Check the API

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok"}
```

### Check the iMessage listener

```bash
pm2 logs clarmi-imessage --lines 10
# Should show: [clarmi-agent] Connected to iMessage server at http://localhost:1234
# Should show: [clarmi-agent] Listening for messages...
```

### Send a test message

From your phone, send an iMessage to the Mac's number:

```
/clarmi show projects
```

You should get a reply within 30-60 seconds with your project list.

### Test client access

Set a client's phone on a project:

```sql
UPDATE projects SET client_phone = '5551234567' WHERE slug = 'test-project';
```

Send `/clarmi what's my project status` from that number. The agent should respond with the project's status, scoped to that project only.

## 10. Monitoring

### Logs

```bash
# All logs
pm2 logs

# Just the iMessage agent
pm2 logs clarmi-imessage

# Just the API
pm2 logs clarmi-api

# Log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

### Process health

```bash
pm2 monit     # Real-time CPU/memory dashboard
pm2 status    # Quick status check
```

### Restart after updates

```bash
cd /Users/Shared/High-Level-Cow-Horse

# Pull latest code
git pull

# Rebuild TS listener
cd src/imessage-agent && npm run build && cd ../..

# Restart services
pm2 restart all
```

## Troubleshooting

### iMessage listener won't connect

```
[clarmi-agent] SDK error: connect ECONNREFUSED 127.0.0.1:1234
```

The Photon iMessage server isn't running. Start it and check it's on port 1234.

### Messages not arriving on the Mac

1. Open Messages.app on the Mac — can you see messages there?
2. Check iCloud Messages is enabled on both iPhone and Mac
3. Verify the Apple ID is the same on both devices
4. Try toggling Messages in iCloud off and on

### "I don't recognize this number"

The sender's phone doesn't match any project's `client_phone`. Either:
- Link the phone: update the project's `client_phone` in the dashboard or DB
- The phone format doesn't match — the agent normalizes `+1(555)123-4567` to `5551234567`, make sure `client_phone` is stored in a compatible format

### Claude CLI fails

```
claude_cli_failed: Claude CLI failed (exit 1)
```

Check:
- `claude auth login` has been run and credentials are valid
- The `ANTHROPIC_API_KEY` env var is NOT set (we strip it so the CLI uses OAuth instead)
- Try running manually: `claude -p "test" --output-format json`

### Webhook returns 403

The `IMESSAGE_WEBHOOK_SECRET` in the TS listener `.env` doesn't match the one in the project root `.env`. They must be identical.

### Mac went to sleep

```bash
# Check if sleep prevention is active
pmset -g
# Look for: sleep 0, displaysleep 0, disksleep 0

# If sleep settings were lost after update
sudo pmset -a sleep 0 disksleep 0 displaysleep 0
```

### After macOS update

macOS updates can reset permissions and sleep settings:

1. Re-grant Full Disk Access to the Photon server
2. Re-check sleep prevention: `sudo pmset -a sleep 0`
3. Verify auto-login is still enabled
4. Run `pm2 resurrect` to restart services

## Security Notes

- The Mac should be on a private network or behind a firewall — ports 1234 and 8000 should not be exposed to the internet
- The webhook secret prevents unauthorized access to the FastAPI endpoint
- Owner phone is hardcoded in config, not in the database, so a DB compromise can't escalate to admin access
- Client tool access is scoped to 8 safe MCP tools — they cannot access other clients' projects
- SSH access should use key-based auth, not passwords
