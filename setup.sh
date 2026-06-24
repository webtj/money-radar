#!/bin/bash
set -e

echo "=== Money Radar Setup ==="
echo ""

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found. Install Docker first."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "ERROR: docker compose not found. Install Docker Compose plugin."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found."; exit 1; }

# Clone feeds.fun if not exists
if [ ! -d "feeds.fun" ]; then
    echo "[1/5] Cloning feeds.fun..."
    git clone --depth 1 https://github.com/Tiendil/feeds.fun.git
else
    echo "[1/5] feeds.fun already exists, skipping clone."
fi

cd feeds.fun

# Copy custom docker-compose override (adds RSSHub)
echo "[2/7] Setting up docker-compose with RSSHub..."
cp ../docker-compose.override.yml . 2>/dev/null || true

# Copy custom tag processors config (Chinese LLM prompt)
echo "[3/7] Setting up Chinese LLM prompt..."
mkdir -p .configs
cp ../config/tag_processors.toml .configs/

# Install license system
echo "[4/7] Installing license system..."
python3 ../scripts/install_license.py --feedsfun-dir . --source-dir ..

# Install frontend customizations
echo "[5/7] Installing Chinese UI and design system..."
bash ../scripts/install_frontend.sh . ..

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "[6/7] Creating .env from template..."
    cp ../.env.example .env
    echo ""
    echo ">>> IMPORTANT: Edit .env file before starting! <<<"
    echo ">>> Set your DeepSeek API key and passwords. <<<"
    echo ""
else
    echo "[6/7] .env already exists, skipping."
fi

# Build and start
echo "[7/7] Building Docker images..."
docker compose build

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env file:  vim feeds.fun/.env"
echo "  2. Start services:  cd feeds.fun && docker compose --profile single-user up -d"
echo "  3. Open browser:    http://your-server-ip"
echo ""
echo "To import RSSHub feeds after startup:"
echo "  python3 ../scripts/import_rsshub.py --rsshub http://localhost:1200"
echo ""
