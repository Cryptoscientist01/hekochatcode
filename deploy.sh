#!/bin/bash

# AI Companion - Hostinger VPS Deployment Script
# Run this script on your VPS after uploading the files

set -e

echo "=========================================="
echo "AI Companion - Deployment Script"
echo "=========================================="

# Configuration
APP_DIR="/var/www/hekochat"
DOMAIN=${1:-"hekochat.ai"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (sudo ./deploy.sh)"
    exit 1
fi

echo ""
echo "Step 1: Updating system packages..."
apt update && apt upgrade -y
print_status "System updated"

echo ""
echo "Step 2: Installing dependencies..."
apt install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git curl gnupg
print_status "Dependencies installed"

echo ""
echo "Step 3: Installing MongoDB..."
if ! command -v mongod &> /dev/null; then
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt update
    apt install -y mongodb-org
fi
systemctl start mongod
systemctl enable mongod
print_status "MongoDB installed and running"

echo ""
echo "Step 4: Installing PM2 and Yarn..."
npm install -g pm2 yarn
print_status "PM2 and Yarn installed"

echo ""
echo "Step 5: Setting up Backend..."
cd $APP_DIR/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || print_warning "emergentintegrations may need manual install"

deactivate
print_status "Backend dependencies installed"

echo ""
echo "Step 6: Building Frontend..."
cd $APP_DIR/frontend

# Update .env for production
if [ -f .env ]; then
    sed -i "s|REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=https://$DOMAIN|g" .env
fi

yarn install
yarn build
print_status "Frontend built"

echo ""
echo "Step 7: Configuring PM2..."
cd $APP_DIR

# Start backend with PM2
pm2 delete hekochat-backend 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd -u root --hp /root
print_status "PM2 configured"

echo ""
echo "Step 8: Configuring Nginx..."

# Copy nginx config
cp $APP_DIR/nginx.conf /etc/nginx/sites-available/hekochat
ln -sf /etc/nginx/sites-available/hekochat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
nginx -t
systemctl restart nginx
print_status "Nginx configured"

echo ""
echo "Step 9: Setting up Firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
print_status "Firewall configured"

echo ""
echo "Step 10: Setting up SSL..."
print_warning "Running Certbot for SSL certificate..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || print_warning "SSL setup may require manual intervention"

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Your app should be available at:"
echo "  https://$DOMAIN"
echo ""
echo "Useful commands:"
echo "  pm2 status              - Check backend status"
echo "  pm2 logs                - View logs"
echo "  pm2 restart all         - Restart backend"
echo "  systemctl restart nginx - Restart nginx"
echo ""
echo "Don't forget to:"
echo "  1. Update backend/.env with your API keys"
echo "  2. Update frontend/.env with correct backend URL"
echo "  3. Rebuild frontend after .env changes: cd frontend && yarn build"
echo ""
