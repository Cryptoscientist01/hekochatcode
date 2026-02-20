# AI Companion - Hostinger VPS Deployment Guide

## Prerequisites
- Hostinger VPS Plan (Ubuntu 22.04 recommended)
- Domain pointed to your VPS IP
- SSH access to your VPS

---

## Step 1: Initial VPS Setup

SSH into your VPS:
```bash
ssh root@your-vps-ip
```

Update system and install dependencies:
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git curl
```

Install MongoDB:
```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update
apt install -y mongodb-org
systemctl start mongod
systemctl enable mongod
```

Install PM2 (process manager):
```bash
npm install -g pm2 yarn
```

---

## Step 2: Upload Application Files

Create app directory:
```bash
mkdir -p /var/www/aicompanion
cd /var/www/aicompanion
```

Upload your files via SFTP or Git:
```bash
# Option 1: Clone from Git (if you have a repo)
git clone https://github.com/yourusername/ai-companion.git .

# Option 2: Upload via SFTP using FileZilla or similar
# Connect to your VPS and upload all files to /var/www/aicompanion/
```

---

## Step 3: Setup Backend

```bash
cd /var/www/aicompanion/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Create production .env file
nano .env
```

Add to `.env`:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=aicompanion_prod
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
EMERGENT_LLM_KEY=your-emergent-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=admin@yourdomain.com
STRIPE_API_KEY=sk_live_your-stripe-key
JWT_SECRET=your-super-secret-jwt-key-change-this
```

Test backend:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001
# Press Ctrl+C after confirming it works
```

---

## Step 4: Setup Frontend

```bash
cd /var/www/aicompanion/frontend

# Install dependencies
yarn install

# Create production .env
nano .env
```

Add to `.env`:
```
REACT_APP_BACKEND_URL=https://yourdomain.com
REACT_APP_VAPID_PUBLIC_KEY=your-vapid-public-key
```

Build for production:
```bash
yarn build
```

---

## Step 5: Configure PM2 Process Manager

Create PM2 ecosystem file:
```bash
cd /var/www/aicompanion
nano ecosystem.config.js
```

Add this content:
```javascript
module.exports = {
  apps: [
    {
      name: 'aicompanion-backend',
      cwd: '/var/www/aicompanion/backend',
      script: 'venv/bin/uvicorn',
      args: 'server:app --host 127.0.0.1 --port 8001',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    }
  ]
};
```

Start the backend:
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## Step 6: Configure Nginx

Create Nginx config:
```bash
nano /etc/nginx/sites-available/aicompanion
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend (React build)
    location / {
        root /var/www/aicompanion/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        root /var/www/aicompanion/frontend/build;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/aicompanion /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

---

## Step 7: Setup SSL (HTTPS)

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to get free SSL from Let's Encrypt.

---

## Step 8: Configure Firewall

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

---

## Step 9: Verify Deployment

1. Visit `https://yourdomain.com` - Should show the app
2. Visit `https://yourdomain.com/api/characters` - Should return JSON
3. Test login/signup functionality
4. Test chat with AI characters

---

## Useful Commands

```bash
# View backend logs
pm2 logs aicompanion-backend

# Restart backend
pm2 restart aicompanion-backend

# Check status
pm2 status

# Restart Nginx
systemctl restart nginx

# View Nginx logs
tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Backend not starting
```bash
cd /var/www/aicompanion/backend
source venv/bin/activate
python -c "import server"  # Check for import errors
```

### MongoDB connection issues
```bash
systemctl status mongod
mongosh  # Test connection
```

### Nginx 502 Bad Gateway
- Check if backend is running: `pm2 status`
- Check backend logs: `pm2 logs aicompanion-backend`

### SSL Certificate renewal
```bash
certbot renew --dry-run  # Test renewal
# Certbot auto-renews via cron
```

---

## Updating the Application

```bash
cd /var/www/aicompanion

# Pull latest code (if using Git)
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart aicompanion-backend

# Update frontend
cd ../frontend
yarn install
yarn build

# Restart Nginx
systemctl restart nginx
```
