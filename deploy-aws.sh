#!/usr/bin/env bash
#
# SPEAR AWS Deployment Script
# Run this ON the Lightsail/EC2 instance after SSH-ing in.
#
# Prerequisites:
#   - Ubuntu 22.04+ instance
#   - Domain DNS pointing to this instance's IP
#   - .env.prod created with API keys
#
set -e

DOMAIN="YOURDOMAIN.com"
EMAIL="you@example.com"

echo "============================================"
echo "  SPEAR AWS Deployment"
echo "============================================"

# --- Preflight ---
if [ "$DOMAIN" = "YOURDOMAIN.com" ]; then
    echo "ERROR: Edit this script and set DOMAIN and EMAIL first."
    exit 1
fi

if [ ! -f .env.prod ]; then
    echo "ERROR: Create .env.prod with your API keys first."
    echo "  cp .env.prod.example .env.prod && nano .env.prod"
    exit 1
fi

# --- Step 1: Install Docker ---
echo "[1/6] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "  Docker installed. You may need to log out and back in."
    echo "  Then re-run this script."
    # Check if we can run docker without sudo
    if ! docker info &>/dev/null; then
        echo "  Run: newgrp docker && bash deploy-aws.sh"
        exit 0
    fi
fi

# --- Step 2: Install Docker Compose plugin ---
echo "[2/6] Checking Docker Compose..."
if ! docker compose version &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-compose-plugin
fi

# --- Step 3: Create directories ---
echo "[3/6] Setting up directories..."
mkdir -p data/chroma_db data/nougat_merged_md data/chat_logs certbot/conf certbot/www

if [ ! -f data/users.yaml ]; then
    cp chatbot/users.yaml data/users.yaml 2>/dev/null || cp data/users.yaml data/users.yaml 2>/dev/null || true
    echo "  Default admin account: admin / ChangeMe123"
fi

# --- Step 4: Configure nginx domain ---
echo "[4/6] Configuring nginx for $DOMAIN..."
sed -i "s/YOURDOMAIN.com/$DOMAIN/g" nginx.conf

# --- Step 5: Get SSL certificate ---
echo "[5/6] Setting up HTTPS..."

# Create temporary self-signed cert so nginx can start
mkdir -p certbot/conf/live/$DOMAIN
if [ ! -f certbot/conf/live/$DOMAIN/fullchain.pem ]; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout certbot/conf/live/$DOMAIN/privkey.pem \
        -out certbot/conf/live/$DOMAIN/fullchain.pem \
        -subj "/CN=$DOMAIN" 2>/dev/null
fi

# Start nginx for ACME challenge
docker compose -f docker-compose.prod.yml up -d nginx
sleep 3

# Get real certificate from Let's Encrypt
docker compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot -w /var/www/certbot \
    --email "$EMAIL" --agree-tos --no-eff-email \
    -d "$DOMAIN" --force-renewal

# --- Step 6: Build and launch ---
echo "[6/6] Building and starting SPEAR (this takes a few minutes)..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "============================================"
echo "  SPEAR is live at: https://$DOMAIN"
echo "============================================"
echo ""
echo "  Default login:  admin / ChangeMe123"
echo "  CHANGE THE PASSWORD after first login!"
echo ""
echo "  --- Useful commands ---"
echo "  Add user:    docker exec -it spear-chatbot python /app/chatbot/manage_users.py add <username>"
echo "  View logs:   docker compose -f docker-compose.prod.yml logs -f spear"
echo "  Restart:     docker compose -f docker-compose.prod.yml restart"
echo "  Stop:        docker compose -f docker-compose.prod.yml down"
echo "  SSL renew:   Automatic (certbot container runs every 12h)"
echo ""
