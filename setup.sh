#!/usr/bin/env bash
set -euo pipefail

echo "=== Clarmi Design Studio — OpenClaw Setup ==="
echo ""

# 1. Check prerequisites
echo "[1/7] Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js required. Install via nvm or nodesource."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3.12+ required."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker required for PostgreSQL."; exit 1; }
echo "  Node.js $(node --version), Python $(python3 --version | cut -d' ' -f2), Docker OK"

# 2. Install OpenClaw globally
echo "[2/7] Installing OpenClaw..."
npm install -g openclaw@latest

# 3. Onboard OpenClaw daemon
echo "[3/7] Setting up OpenClaw daemon..."
openclaw onboard --install-daemon

# 4. Install Python dependencies (MCP server)
echo "[4/7] Installing Python MCP server dependencies..."
pip install -e .

# 5. Install Playwright browsers (for QA screenshots)
echo "[5/7] Installing Playwright Chromium..."
playwright install chromium
playwright install-deps chromium 2>/dev/null || true

# 6. Start PostgreSQL
echo "[6/7] Starting PostgreSQL..."
docker compose up -d postgres

echo "  Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U openclaw >/dev/null 2>&1; do
  sleep 1
done
echo "  PostgreSQL ready."

# 7. Run database migrations
echo "[7/7] Running database migrations..."
alembic upgrade head

# Setup environment
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "  Created .env from template — edit it with your API keys."
fi

# Create local project storage
mkdir -p ./data/projects

# Copy OpenClaw config
mkdir -p ~/.openclaw
if [ ! -f ~/.openclaw/openclaw.json ]; then
  cp openclaw.json ~/.openclaw/openclaw.json
  echo "  Copied openclaw.json to ~/.openclaw/"
else
  echo "  ~/.openclaw/openclaw.json already exists — skipping."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys (ANTHROPIC_API_KEY, FIRECRAWL_API_KEY, etc.)"
echo "  2. Run: openclaw"
echo "  3. Scan QR code for WhatsApp pairing"
echo "  4. Send a test message via WhatsApp, or use: openclaw chat"
echo ""
echo "To test the MCP server directly:"
echo "  python -m openclaw.mcp_server"
