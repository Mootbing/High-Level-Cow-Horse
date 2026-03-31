#!/usr/bin/env bash
# ============================================================================
# OpenClaw EC2 Setup Script
# Run as: sudo bash setup.sh
#
# Provisions a fresh Ubuntu 22.04/24.04 EC2 instance with everything needed
# to run OpenClaw: Docker, Node.js, Python, Playwright deps, nginx, certbot.
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    fail "This script must be run as root (sudo bash setup.sh)"
fi

info "Starting OpenClaw EC2 setup..."
echo ""

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
info "Updating system packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    unzip \
    jq \
    htop \
    tmux \
    ufw \
    fail2ban
ok "System packages updated"

# ---------------------------------------------------------------------------
# 2. Docker + Docker Compose v2
# ---------------------------------------------------------------------------
if command -v docker &>/dev/null; then
    ok "Docker already installed: $(docker --version)"
else
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | bash
    ok "Docker installed: $(docker --version)"
fi

# Ensure Docker Compose v2 plugin is available
if docker compose version &>/dev/null; then
    ok "Docker Compose v2 available: $(docker compose version --short)"
else
    info "Installing Docker Compose v2 plugin..."
    apt-get install -y -qq docker-compose-plugin
    ok "Docker Compose v2 installed"
fi

systemctl enable docker
systemctl start docker

# ---------------------------------------------------------------------------
# 3. Node.js 22 (for engineer skill npm builds)
# ---------------------------------------------------------------------------
if command -v node &>/dev/null && [[ "$(node -v)" == v22* ]]; then
    ok "Node.js 22 already installed: $(node -v)"
else
    info "Installing Node.js 22..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
    ok "Node.js installed: $(node -v)"
fi

# ---------------------------------------------------------------------------
# 4. Python 3.12
# ---------------------------------------------------------------------------
if command -v python3.12 &>/dev/null; then
    ok "Python 3.12 already installed: $(python3.12 --version)"
else
    info "Installing Python 3.12..."
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip
    ok "Python 3.12 installed: $(python3.12 --version)"
fi

# ---------------------------------------------------------------------------
# 5. Playwright system dependencies (for QA skill)
# ---------------------------------------------------------------------------
info "Installing Playwright system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2t64 \
    libwayland-client0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    xvfb
ok "Playwright dependencies installed"

# ---------------------------------------------------------------------------
# 6. Nginx
# ---------------------------------------------------------------------------
if command -v nginx &>/dev/null; then
    ok "Nginx already installed: $(nginx -v 2>&1)"
else
    info "Installing Nginx..."
    apt-get install -y -qq nginx
    systemctl enable nginx
    ok "Nginx installed"
fi

# ---------------------------------------------------------------------------
# 7. Certbot for SSL (Let's Encrypt)
# ---------------------------------------------------------------------------
if command -v certbot &>/dev/null; then
    ok "Certbot already installed: $(certbot --version 2>&1)"
else
    info "Installing Certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
    ok "Certbot installed"
fi

# ---------------------------------------------------------------------------
# 8. Firewall setup
# ---------------------------------------------------------------------------
info "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
ok "Firewall configured (SSH, HTTP, HTTPS allowed)"

# ---------------------------------------------------------------------------
# 9. Create openclaw user and directories
# ---------------------------------------------------------------------------
OPENCLAW_USER="openclaw"
OPENCLAW_HOME="/opt/openclaw"
DATA_DIR="/data/projects"

if id "$OPENCLAW_USER" &>/dev/null; then
    ok "User '$OPENCLAW_USER' already exists"
else
    info "Creating user '$OPENCLAW_USER'..."
    useradd -r -m -d "$OPENCLAW_HOME" -s /bin/bash "$OPENCLAW_USER"
    usermod -aG docker "$OPENCLAW_USER"
    ok "User '$OPENCLAW_USER' created and added to docker group"
fi

info "Creating directories..."
mkdir -p "$OPENCLAW_HOME"
mkdir -p "$DATA_DIR"
mkdir -p "$OPENCLAW_HOME/.openclaw"
mkdir -p "$OPENCLAW_HOME/frontend/dist"

chown -R "$OPENCLAW_USER":"$OPENCLAW_USER" "$OPENCLAW_HOME"
chown -R "$OPENCLAW_USER":"$OPENCLAW_USER" "$DATA_DIR"
chmod 700 "$OPENCLAW_HOME/.openclaw"
ok "Directories created: $OPENCLAW_HOME, $DATA_DIR"

# ---------------------------------------------------------------------------
# 10. Clone repo or print instructions
# ---------------------------------------------------------------------------
REPO_DIR="$OPENCLAW_HOME/app"

if [[ -d "$REPO_DIR/.git" ]]; then
    ok "Repository already cloned at $REPO_DIR"
else
    info "Repository not found at $REPO_DIR"
    echo ""
    echo "  Clone the repo or copy it manually:"
    echo "    sudo -u $OPENCLAW_USER git clone <your-repo-url> $REPO_DIR"
    echo "  Or scp it:"
    echo "    scp -r ./High-Level-Cow-Horse ec2-user@<ip>:$REPO_DIR"
    echo ""
fi

# ---------------------------------------------------------------------------
# 11. Install systemd service for Docker Compose autostart
# ---------------------------------------------------------------------------
info "Installing openclaw systemd service..."
cat > /etc/systemd/system/openclaw.service << 'SYSTEMD_EOF'
[Unit]
Description=OpenClaw Multi-Agent System
Documentation=https://github.com/your-org/openclaw
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=openclaw
Group=openclaw
WorkingDirectory=/opt/openclaw/app
Environment=COMPOSE_FILE=deploy/ec2/docker-compose.yml
Environment=HOME=/opt/openclaw

ExecStartPre=/usr/bin/docker compose pull --quiet
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose up -d --remove-orphans

# Restart policy
Restart=on-failure
RestartSec=30

# Give containers time to start and stop
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl daemon-reload
systemctl enable openclaw.service
ok "Systemd service installed and enabled"

# ---------------------------------------------------------------------------
# 12. Copy nginx config if it exists in deploy/ec2/
# ---------------------------------------------------------------------------
if [[ -f "$REPO_DIR/deploy/ec2/nginx.conf" ]]; then
    info "Installing nginx configuration..."
    cp "$REPO_DIR/deploy/ec2/nginx.conf" /etc/nginx/sites-available/openclaw
    ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/openclaw
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    ok "Nginx configuration installed"
else
    warn "nginx.conf not found at $REPO_DIR/deploy/ec2/nginx.conf — install it manually later"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "============================================================================"
echo -e "${GREEN}  OpenClaw EC2 setup complete!${NC}"
echo "============================================================================"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Clone/copy the repo to $REPO_DIR (if not done)"
echo ""
echo "  2. Copy and fill in environment variables:"
echo "     sudo -u $OPENCLAW_USER cp $REPO_DIR/deploy/ec2/.env.example $REPO_DIR/.env"
echo "     sudo -u $OPENCLAW_USER nano $REPO_DIR/.env"
echo ""
echo "  3. Authenticate with Claude (no API key needed!):"
echo "     sudo -u $OPENCLAW_USER bash"
echo "     cd $REPO_DIR && pip install -e . && openclaw login"
echo ""
echo "  4. Start OpenClaw:"
echo "     sudo systemctl start openclaw"
echo "     # Or manually:"
echo "     cd $REPO_DIR && docker compose -f deploy/ec2/docker-compose.yml up -d"
echo ""
echo "  5. Set up SSL with Let's Encrypt:"
echo "     Install nginx config first:"
echo "       cp $REPO_DIR/deploy/ec2/nginx.conf /etc/nginx/sites-available/openclaw"
echo "       ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/openclaw"
echo "       rm -f /etc/nginx/sites-enabled/default"
echo "       nginx -t && systemctl reload nginx"
echo "     Then run certbot:"
echo "       certbot --nginx -d your-domain.com"
echo ""
echo "  6. Configure WhatsApp webhook URL:"
echo "     Set webhook URL in Meta Developer Console to:"
echo "       https://your-domain.com/api/webhook/whatsapp"
echo "     Verify token: the WA_VERIFY_TOKEN value from your .env"
echo ""
echo "  7. View logs:"
echo "     cd $REPO_DIR && docker compose -f deploy/ec2/docker-compose.yml logs -f"
echo ""
echo "============================================================================"
