# HekoChat.ai - Split Architecture Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      hekochat.ai                            │
│              (Hostinger Business Hosting)                   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              React Frontend (Static)                │   │
│   │         /public_html/build files                    │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              api.hekochat.ai (or subdomain)                 │
│                  (Railway / Render)                         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              FastAPI Backend                        │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Database Connection
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   MongoDB Atlas                             │
│                  (Free M0 Cluster)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: MongoDB Atlas Setup (Free)

### Step 1: Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up for free
3. Create a new project called "HekoChat"

### Step 2: Create Free Cluster
1. Click "Build a Database"
2. Select **M0 FREE** tier
3. Choose a cloud provider (AWS recommended)
4. Select region closest to your users
5. Name your cluster: `hekochat-cluster`

### Step 3: Setup Database Access
1. Go to "Database Access" in sidebar
2. Click "Add New Database User"
3. Create user:
   - Username: `hekochat_admin`
   - Password: (generate a strong password, save it!)
   - Role: "Read and write to any database"

### Step 4: Setup Network Access
1. Go to "Network Access" in sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Required for Railway/Render to connect

### Step 5: Get Connection String
1. Go to "Database" → Click "Connect"
2. Choose "Connect your application"
3. Copy the connection string, it looks like:
   ```
   mongodb+srv://hekochat_admin:<password>@hekochat-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<password>` with your actual password

---

## Part 2: Backend Deployment (Railway - Recommended)

### Option A: Railway (Recommended - $5 free credit/month)

#### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub

#### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo" or "Empty Project"

#### Step 3: If using GitHub:
1. Push your backend folder to GitHub
2. Connect the repo to Railway
3. Railway auto-detects Python

#### Step 4: If deploying manually:
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. In your backend folder: `railway init`
4. Deploy: `railway up`

#### Step 5: Add Environment Variables
In Railway dashboard → Variables, add:
```
MONGO_URL=mongodb+srv://hekochat_admin:YOUR_PASSWORD@hekochat-cluster.xxxxx.mongodb.net/hekochat_prod?retryWrites=true&w=majority
DB_NAME=hekochat_prod
CORS_ORIGINS=https://hekochat.ai,https://www.hekochat.ai
EMERGENT_LLM_KEY=your-emergent-key
VAPID_PUBLIC_KEY=BMpQT6udu_oCEeMA3TzLdekSj0194hIy6wuYD2fCg4JZmje3VCgLL2W1pTEy-UIqeugpzfVtRytCxqzyQ7qGdBI
VAPID_PRIVATE_KEY=DvFTPTQaqR3AuOQeKABufKFXVgGbJdJ6ROk_PiLnLuQ
VAPID_CLAIMS_EMAIL=admin@hekochat.ai
STRIPE_API_KEY=sk_live_your-stripe-key
JWT_SECRET=your-super-secret-jwt-key
PORT=8001
```

#### Step 6: Get Your Backend URL
Railway will give you a URL like: `https://hekochat-backend-production.up.railway.app`

You can also add a custom domain: `api.hekochat.ai`

---

### Option B: Render (Free tier available)

#### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub

#### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repo or use "Deploy from Git URL"

#### Step 3: Configure Service
- Name: `hekochat-backend`
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

#### Step 4: Add Environment Variables
Same as Railway (see above)

#### Step 5: Deploy
Click "Create Web Service"

Your URL will be: `https://hekochat-backend.onrender.com`

---

## Part 3: Frontend Deployment (Hostinger Business Hosting)

### Step 1: Update Frontend Environment
Before building, update `/frontend/.env`:
```
REACT_APP_BACKEND_URL=https://your-railway-url.up.railway.app
REACT_APP_VAPID_PUBLIC_KEY=BMpQT6udu_oCEeMA3TzLdekSj0194hIy6wuYD2fCg4JZmje3VCgLL2W1pTEy-UIqeugpzfVtRytCxqzyQ7qGdBI
```

### Step 2: Build React App
```bash
cd frontend
yarn install
yarn build
```

### Step 3: Upload to Hostinger
1. Login to Hostinger hPanel
2. Go to File Manager
3. Navigate to `public_html`
4. Delete default files (index.html, etc.)
5. Upload ALL contents from `frontend/build/` folder to `public_html/`

### Step 4: Upload .htaccess
Upload the `.htaccess` file (created below) to `public_html/`

### Step 5: Verify
Visit https://hekochat.ai - should show your app!

---

## Part 4: DNS Configuration

### If using custom subdomain for API (api.hekochat.ai):

1. In Hostinger DNS settings, add:
   - Type: CNAME
   - Name: api
   - Target: your-railway-url.up.railway.app

2. In Railway, add custom domain: api.hekochat.ai

3. Update frontend .env:
   ```
   REACT_APP_BACKEND_URL=https://api.hekochat.ai
   ```

---

## Troubleshooting

### CORS Errors
Make sure `CORS_ORIGINS` in backend includes your frontend domain:
```
CORS_ORIGINS=https://hekochat.ai,https://www.hekochat.ai
```

### 404 on Page Refresh
Make sure `.htaccess` is uploaded to `public_html/`

### API Connection Failed
1. Check Railway/Render logs for errors
2. Verify MongoDB connection string
3. Verify environment variables

### MongoDB Connection Issues
1. Check "Network Access" allows 0.0.0.0/0
2. Verify password is correct in connection string
3. Check cluster is active (not paused)

---

## Cost Summary

| Service | Cost |
|---------|------|
| Hostinger Business | Your existing plan |
| Railway | Free $5/month credit |
| MongoDB Atlas | Free M0 tier |
| **Total** | **$0 extra** |

---

## Maintenance Commands

### Railway
```bash
railway logs          # View logs
railway up            # Deploy updates
railway variables     # Manage env vars
```

### Render
- Use web dashboard for logs and deploys

### Update Frontend
1. Make changes locally
2. Run `yarn build`
3. Upload new `build/` contents to Hostinger
