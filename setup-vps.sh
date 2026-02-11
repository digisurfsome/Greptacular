#!/bin/bash
# =============================================================================
# AutoForge VPS Setup Script
# =============================================================================
# Run this on a fresh Ubuntu 22.04+ VPS (DigitalOcean, Vultr, Linode, etc.)
#
# Usage:
#   1. Create a VPS (Ubuntu 22.04, 4GB+ RAM recommended)
#   2. SSH in: ssh root@your-vps-ip
#   3. Run: bash setup-vps.sh
#   4. After setup, run: claude    (to authenticate your subscription)
#   5. Start AutoForge: pm2 start autoforge-8888
#
# Multiple instances:
#   pm2 start autoforge-8888   # First project  → http://your-ip:8888
#   pm2 start autoforge-8889   # Second project → http://your-ip:8889
#   pm2 start autoforge-8890   # Third project  → http://your-ip:8890
# =============================================================================

set -e

echo "============================================"
echo "  AutoForge VPS Setup"
echo "============================================"

# --- System Updates ---
echo "[1/7] Updating system..."
apt-get update && apt-get upgrade -y

# --- Python 3.11 ---
echo "[2/7] Installing Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# --- Node.js 20 ---
echo "[3/7] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# --- Git + essentials ---
echo "[4/7] Installing essentials..."
apt-get install -y git curl wget unzip build-essential

# --- Claude CLI ---
echo "[5/7] Installing Claude CLI..."
npm install -g @anthropic-ai/claude-code

# --- PM2 (process manager - keeps AutoForge running 24/7) ---
echo "[6/7] Installing PM2..."
npm install -g pm2
pm2 startup  # auto-start on reboot

# --- Clone AutoForge ---
echo "[7/7] Setting up AutoForge..."
mkdir -p /opt/autoforge
cd /opt/autoforge

# Clone the repo (update URL to your fork if needed)
git clone https://github.com/digisurfsome/Greptacular.git app
cd app

# Set up Python venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# Build the React UI
cd ui
npm ci
npm run build
cd ..

# --- Create PM2 configs for multiple instances ---
# Each instance runs on a different port

# Instance 1: Port 8888
cat > /opt/autoforge/ecosystem.config.js << 'ECOSYSTEM'
module.exports = {
  apps: [
    {
      name: 'autoforge-8888',
      cwd: '/opt/autoforge/app',
      script: 'venv/bin/python',
      args: '-m uvicorn server.main:app --host 0.0.0.0 --port 8888',
      env: {
        AUTOFORGE_ALLOW_REMOTE: '1',
      },
      auto_restart: true,
      max_memory_restart: '2G',
    },
    {
      name: 'autoforge-8889',
      cwd: '/opt/autoforge/app',
      script: 'venv/bin/python',
      args: '-m uvicorn server.main:app --host 0.0.0.0 --port 8889',
      env: {
        AUTOFORGE_ALLOW_REMOTE: '1',
      },
      auto_restart: true,
      max_memory_restart: '2G',
    },
    {
      name: 'autoforge-8890',
      cwd: '/opt/autoforge/app',
      script: 'venv/bin/python',
      args: '-m uvicorn server.main:app --host 0.0.0.0 --port 8890',
      env: {
        AUTOFORGE_ALLOW_REMOTE: '1',
      },
      auto_restart: true,
      max_memory_restart: '2G',
    },
  ],
}
ECOSYSTEM

# --- Firewall ---
echo "Configuring firewall..."
ufw allow 22/tcp     # SSH
ufw allow 8888/tcp   # AutoForge instance 1
ufw allow 8889/tcp   # AutoForge instance 2
ufw allow 8890/tcp   # AutoForge instance 3
ufw --force enable

# --- Projects directory ---
mkdir -p /opt/autoforge/projects

# --- Save PM2 config ---
pm2 save

echo ""
echo "============================================"
echo "  SETUP COMPLETE!"
echo "============================================"
echo ""
echo "  NEXT STEPS:"
echo ""
echo "  1. Authenticate Claude CLI (one-time):"
echo "     $ claude"
echo "     (This opens a browser link - click it to authorize your subscription)"
echo ""
echo "  2. Start AutoForge:"
echo "     $ cd /opt/autoforge"
echo "     $ pm2 start ecosystem.config.js --only autoforge-8888"
echo ""
echo "  3. Access it at:"
echo "     http://YOUR_VPS_IP:8888"
echo ""
echo "  MULTIPLE INSTANCES:"
echo "     $ pm2 start ecosystem.config.js --only autoforge-8889"
echo "     $ pm2 start ecosystem.config.js --only autoforge-8890"
echo ""
echo "  USEFUL COMMANDS:"
echo "     pm2 list                    # See running instances"
echo "     pm2 logs autoforge-8888     # View logs"
echo "     pm2 restart autoforge-8888  # Restart instance"
echo "     pm2 stop autoforge-8888     # Stop instance"
echo "     pm2 start all               # Start all 3 instances"
echo ""
echo "  Projects are stored in: /opt/autoforge/projects/"
echo "============================================"
