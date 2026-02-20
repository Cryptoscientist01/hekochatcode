# HekoChat.ai - Hostinger VPS Deployment Guide

## Prerequisites
- Hostinger VPS Plan (KVM 2 or higher recommended)
- Ubuntu 22.04 LTS
- Domain `hekochat.ai` pointed to your VPS IP
- SSH access to your VPS

---

## Quick Start (Automated)

### Step 1: Get Your VPS
1. Purchase Hostinger VPS (KVM 2 recommended - $5.99/month)
2. Select Ubuntu 22.04 LTS
3. Note your VPS IP address

### Step 2: Point Your Domain
In your domain registrar (or Hostinger DNS):
```
A Record: hekochat.ai → YOUR_VPS_IP
A Record: www.hekochat.ai → YOUR_VPS_IP
```
Wait 5-10 minutes for DNS propagation.

### Step 3: Connect to VPS
```bash
ssh root@YOUR_VPS_IP
```

### Step 4: Upload Files
Option A - Using Git:
```bash
mkdir -p /var/www/hekochat
cd /var/www/hekochat
git clone YOUR_REPO_URL .
```

Option B - Using SFTP (FileZilla):
1. Connect to your VPS via SFTP
2. Upload all files to `/var/www/hekochat/`

### Step 5: Run Deployment Script
```bash
cd /var/www/hekochat
chmod +x deploy.sh
sudo ./deploy.sh
```

### Step 6: Configure Environment Variables
```bash
nano /var/www/hekochat/backend/.env
```

Add your production values:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=hekochat_prod
CORS_ORIGINS=https://hekochat.ai,https://www.hekochat.ai
EMERGENT_LLM_KEY=your-emergent-llm-key
VAPID_PUBLIC_KEY=BMpQT6udu_oCEeMA3TzLdekSj0194hIy6wuYD2fCg4JZmje3VCgLL2W1pTEy-UIqeugpzfVtRytCxqzyQ7qGdBI
VAPID_PRIVATE_KEY=DvFTPTQaqR3AuOQeKABufKFXVgGbJdJ6ROk_PiLnLuQ
VAPID_CLAIMS_EMAIL=admin@hekochat.ai
STRIPE_API_KEY=sk_live_your-stripe-key
JWT_SECRET=generate-a-long-random-string-here
```

### Step 7: Restart Backend
```bash
pm2 restart hekochat-backend
```

### Step 8: Verify
Visit https://hekochat.ai 🎉

---

## Manual Installation (If Script Fails)

### 1. Update System
```bash
apt update && apt upgrade -y
```

### 2. Install Dependencies
```bash
apt install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git curl gnupg
```

### 3. Install MongoDB
```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update
apt install -y mongodb-org
systemctl start mongod
systemctl enable mongod
```

### 4. Install PM2 & Yarn
```bash
npm install -g pm2 yarn
```

### 5. Setup Backend
```bash
cd /var/www/hekochat/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
deactivate
```

### 6. Setup Frontend
```bash
cd /var/www/hekochat/frontend
yarn install
yarn build
```

### 7. Configure PM2
```bash
cd /var/www/hekochat
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 8. Configure Nginx
```bash
cp /var/www/hekochat/nginx.conf /etc/nginx/sites-available/hekochat
ln -sf /etc/nginx/sites-available/hekochat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### 9. Setup SSL
```bash
certbot --nginx -d hekochat.ai -d www.hekochat.ai
```

### 10. Configure Firewall
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

---

## File Structure on VPS

```
/var/www/hekochat/
├── backend/
│   ├── .env              # Your API keys (edit this!)
│   ├── requirements.txt
│   ├── server.py
│   └── venv/             # Python virtual environment
├── frontend/
│   ├── .env
│   ├── build/            # Production build (served by Nginx)
│   ├── package.json
│   └── src/
├── deploy.sh
├── ecosystem.config.js
└── nginx.conf
```

---

## Useful Commands

### Backend Management
```bash
pm2 status                    # Check if backend is running
pm2 logs hekochat-backend     # View backend logs
pm2 restart hekochat-backend  # Restart backend
pm2 stop hekochat-backend     # Stop backend
```

### Nginx Management
```bash
nginx -t                      # Test config
systemctl restart nginx       # Restart Nginx
systemctl status nginx        # Check status
tail -f /var/log/nginx/hekochat_error.log  # View errors
```

### MongoDB Management
```bash
systemctl status mongod       # Check MongoDB status
mongosh                       # Open MongoDB shell
mongosh hekochat_prod         # Connect to your database
```

### SSL Certificate
```bash
certbot renew --dry-run       # Test renewal
certbot renew                 # Renew certificates
```

---

## Updating Your App

### Quick Update
```bash
cd /var/www/hekochat

# Pull latest code (if using Git)
git pull

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
pm2 restart hekochat-backend

# Rebuild frontend
cd ../frontend
yarn install
yarn build

# Done!
```

### Update Script
```bash
#!/bin/bash
cd /var/www/hekochat
git pull
cd backend && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd ../frontend && yarn install && yarn build
pm2 restart hekochat-backend
echo "Update complete!"
```

---

## Troubleshooting

### Backend Won't Start
```bash
cd /var/www/hekochat/backend
source venv/bin/activate
python -c "import server"  # Check for import errors
uvicorn server:app --host 0.0.0.0 --port 8001  # Test manually
```

### 502 Bad Gateway
1. Check if backend is running: `pm2 status`
2. Check backend logs: `pm2 logs hekochat-backend`
3. Restart backend: `pm2 restart hekochat-backend`

### MongoDB Connection Failed
```bash
systemctl status mongod       # Check if running
systemctl start mongod        # Start if stopped
mongosh                       # Test connection
```

### SSL Certificate Issues
```bash
certbot --nginx -d hekochat.ai -d www.hekochat.ai --force-renewal
```

### Permission Issues
```bash
chown -R www-data:www-data /var/www/hekochat/frontend/build
chmod -R 755 /var/www/hekochat
```

---

## Security Recommendations

1. **Change SSH Port** (optional):
   ```bash
   nano /etc/ssh/sshd_config
   # Change Port 22 to Port 2222
   systemctl restart sshd
   ufw allow 2222
   ```

2. **Setup Fail2Ban**:
   ```bash
   apt install fail2ban
   systemctl enable fail2ban
   ```

3. **Regular Updates**:
   ```bash
   apt update && apt upgrade -y
   ```

4. **Backup MongoDB**:
   ```bash
   mongodump --db hekochat_prod --out /backup/$(date +%Y%m%d)
   ```

---

## Cost Summary

| Item | Cost |
|------|------|
| Hostinger VPS KVM 2 | ~$5.99/month |
| Domain (hekochat.ai) | ~$10-15/year |
| SSL Certificate | FREE (Let's Encrypt) |
| MongoDB | FREE (local) |

**Total: ~$6-7/month**

---

## Support

If you encounter issues:
1. Check logs: `pm2 logs` and `/var/log/nginx/hekochat_error.log`
2. Verify all environment variables are set
3. Ensure DNS is properly configured
4. Check firewall: `ufw status`
