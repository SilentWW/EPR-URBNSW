# Railway Deployment Guide for E1 ERP System

## Overview
This guide will help you deploy the E1 ERP System on Railway with MongoDB Atlas (free tier).

**Architecture:**
- **Backend**: FastAPI (Python) - Railway service
- **Frontend**: React (Vite) - Railway static site
- **Database**: MongoDB Atlas (Free 512MB cluster)

---

## Step 1: Create MongoDB Atlas Free Cluster (5 minutes)

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas) and create a free account
2. Click **"Build a Database"**
3. Select **"M0 FREE"** tier (Shared cluster)
4. Choose a cloud provider (AWS recommended) and region closest to you
5. Click **"Create Cluster"**

### Configure Database Access:
1. Go to **"Database Access"** → **"Add New Database User"**
2. Create a user:
   - Username: `erp_admin`
   - Password: Generate a secure password (save this!)
   - Role: "Read and write to any database"
3. Click **"Add User"**

### Configure Network Access:
1. Go to **"Network Access"** → **"Add IP Address"**
2. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - This is needed for Railway's dynamic IPs
3. Click **"Confirm"**

### Get Connection String:
1. Go to **"Database"** → Click **"Connect"**
2. Choose **"Connect your application"**
3. Copy the connection string, it looks like:
   ```
   mongodb+srv://erp_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<password>` with your actual password
5. Add database name: `mongodb+srv://erp_admin:PASSWORD@cluster0.xxxxx.mongodb.net/erp_db?retryWrites=true&w=majority`

---

## Step 2: Deploy Backend to Railway (5 minutes)

### 2.1 Create Railway Account
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub (recommended)

### 2.2 Create New Project
1. Click **"New Project"**
2. Select **"Empty Project"**
3. Click on the project to open it

### 2.3 Deploy Backend
1. Click **"+ New"** → **"GitHub Repo"**
2. Connect your GitHub account and select your repository
3. Railway will auto-detect the project

### 2.4 Configure Backend Service
1. Click on the deployed service
2. Go to **"Settings"** tab
3. Set **Root Directory**: `backend`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

### 2.5 Add Environment Variables
Go to **"Variables"** tab and add:

```
MONGO_URL=mongodb+srv://erp_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/erp_db?retryWrites=true&w=majority
DB_NAME=erp_db
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ENVIRONMENT=production
```

### 2.6 Generate Domain
1. Go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"**
3. You'll get a URL like: `your-backend-production.up.railway.app`
4. **Save this URL** - you'll need it for frontend

---

## Step 3: Deploy Frontend to Railway (5 minutes)

### 3.1 Add Frontend Service
1. In the same project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository

### 3.2 Configure Frontend Service
1. Click on the new service
2. Go to **"Settings"** tab
3. Set **Root Directory**: `frontend`
4. Set **Build Command**: `yarn install && yarn build`
5. Set **Start Command**: `npx serve -s dist -l $PORT`

### 3.3 Add Environment Variables
Go to **"Variables"** tab and add:

```
REACT_APP_BACKEND_URL=https://your-backend-production.up.railway.app
```
(Replace with your actual backend URL from Step 2.6)

### 3.4 Generate Domain
1. Go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"**
3. Or add custom domain: `erp.urbnsw.com`

---

## Step 4: Configure Custom Domain (erp.urbnsw.com)

### 4.1 Add Custom Domain in Railway
1. Go to Frontend service → **"Settings"** → **"Networking"**
2. Click **"+ Custom Domain"**
3. Enter: `erp.urbnsw.com`

### 4.2 Configure DNS at Your Domain Registrar
Add a CNAME record:
- **Type**: CNAME
- **Name**: `erp`
- **Value**: `your-frontend-production.up.railway.app`
- **TTL**: 3600 (or Auto)

Wait 5-10 minutes for DNS propagation.

---

## Step 5: Initialize the Application

After deployment, you need to create your first user:

### Option A: Use the Register Page
1. Go to `https://erp.urbnsw.com/register`
2. Fill in:
   - Email: your-email@example.com
   - Password: your-password
   - Company Name: Urban Streetwear (or your company)
3. This creates an admin account and seeds default Chart of Accounts

### Option B: Seed Demo Data (Optional)
If you want sample data, make this API call:
```bash
curl -X POST https://your-backend.up.railway.app/api/seed-demo-data \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Backend not starting?
- Check Railway logs for errors
- Verify MONGO_URL is correct (no `<password>` placeholder)
- Ensure all environment variables are set

### Frontend not connecting to backend?
- Verify REACT_APP_BACKEND_URL is correct
- URL should include `https://` and NOT have trailing `/`
- Redeploy frontend after changing environment variables

### Database connection issues?
- Verify MongoDB Atlas allows access from anywhere (0.0.0.0/0)
- Check the connection string format
- Test connection using MongoDB Compass

### Custom domain not working?
- Wait 10-30 minutes for DNS propagation
- Use [DNS Checker](https://dnschecker.org) to verify CNAME is set
- Ensure SSL certificate is generated (Railway does this automatically)

---

## Cost Estimation (Railway Free Tier)

Railway offers $5 free credits per month:
- **Backend**: ~$2-3/month (low traffic)
- **Frontend**: ~$1-2/month (static site)
- **Total**: Usually stays within free tier for small teams

MongoDB Atlas M0 is always free (512MB storage).

---

## Files Modified for Railway Deployment

The following files have been created/modified:
- `/backend/Procfile` - Process definition
- `/backend/runtime.txt` - Python version
- `/backend/railway.toml` - Railway backend config
- `/frontend/railway.toml` - Railway frontend config
- `/railway.json` - Project-level config

---

## Support

If you encounter issues:
1. Check Railway Dashboard logs
2. Check MongoDB Atlas metrics
3. Test API endpoints using curl or Postman

**Your ERP will be live at: https://erp.urbnsw.com**
