#!/bin/bash
set -euo pipefail

echo "=== OpenClaw EC2 Setup ==="

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Install Caddy
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

# Create openclaw user
useradd -m -s /bin/bash openclaw || true
usermod -aG docker openclaw

# Set up project directory
INSTALL_DIR=/opt/openclaw
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone repo (user should replace with their repo URL)
echo "Place your code in $INSTALL_DIR"
echo "Copy your .env file to $INSTALL_DIR/.env"

# Create data directories
mkdir -p /data/projects

# Set up Caddy
cat > /etc/caddy/Caddyfile << 'CADDY'
{$DOMAIN:openclaw.example.com} {
    reverse_proxy localhost:8000
}
CADDY
systemctl restart caddy

# Set up log rotation
cat > /etc/logrotate.d/openclaw << 'LOGROTATE'
/opt/openclaw/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
}
LOGROTATE

# Set up health check cron
cat > /etc/cron.d/openclaw-health << 'CRON'
* * * * * root cd /opt/openclaw && docker compose exec -T api python scripts/healthcheck.py >> /opt/openclaw/logs/health.log 2>&1
CRON
mkdir -p /opt/openclaw/logs

# Enable Docker to start on boot
systemctl enable docker

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Place your code in $INSTALL_DIR"
echo "2. Copy .env.example to .env and fill in API keys"
echo "3. Update /etc/caddy/Caddyfile with your domain"
echo "4. Run: cd $INSTALL_DIR && docker compose up -d"
echo "5. Set Meta webhook URL to https://yourdomain.com/api/webhook"
echo "6. Run: caddy reload --config /etc/caddy/Caddyfile"
