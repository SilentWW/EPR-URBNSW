# Railway Deployment Guide - E1 ERP System

## Overview
This guide will help you deploy the E1 ERP System on Railway's free tier.

**⚠️ Free Tier Limitations:**
- 0.5 GB RAM (may cause slowdowns)
- $5 credits (lasts ~2-4 weeks with moderate use)
- App sleeps after inactivity

---

## Prerequisites
1. GitHub account
2. Railway account (sign up at [railway.app](https://railway.app))
3. MongoDB Atlas account (free tier) - **REQUIRED** since Railway free tier doesn't include MongoDB

---

## Step 1: Set Up MongoDB Atlas (Free - 512MB)

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free account or sign in
3. Create a new **FREE** cluster:
   - Click "Build a Database"
   - Select **M0 FREE** tier
   - Choose a region close to you
   - Click "Create"

4. Set up database access:
   - Go to "Database Access" → "Add New Database User"
   - Username: `erp_user`
   - Password: (generate a strong password, **save it!**)
   - Role: "Read and write to any database"
   - Click "Add User"

5. Set up network access:
   - Go to "Network Access" → "Add IP Address"
   - Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Click "Confirm"

6. Get your connection string:
   - Go to "Database" → "Connect" → "Connect your application"
   - Copy the connection string, it looks like:
   ```
   mongodb+srv://erp_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   - Replace `<password>` with your actual password
   - Add database name: `mongodb+srv://erp_user:yourpassword@cluster0.xxxxx.mongodb.net/erp_db?retryWrites=true&w=majority`

---

## Step 2: Push Code to GitHub

### Option A: Using Emergent Platform (Recommended)
1. In the Emergent chat, click "Save to GitHub" button
2. Follow the prompts to create/select a repository
3. Your code will be pushed automatically

### Option B: Manual Push
```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit for Railway deployment"

# Create a new repo on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy Backend on Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)

2. Click **"New Project"** → **"Deploy from GitHub repo"**

3. Select your repository

4. Railway will auto-detect the project. Wait for initial build.

5. **Add Environment Variables:**
   - Click on your service → "Variables" tab
   - Add these variables:

   | Variable | Value |
   |----------|-------|
   | `MONGO_URL` | `mongodb+srv://erp_user:yourpassword@cluster0.xxxxx.mongodb.net/erp_db?retryWrites=true&w=majority` |
   | `DB_NAME` | `erp_db` |
   | `JWT_SECRET` | `your-super-secret-key-change-this-123` |
   | `PORT` | `8000` |

6. **Configure Build Settings:**
   - Go to "Settings" tab
   - Root Directory: `/` (leave empty or `/`)
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`

7. Click **"Deploy"** and wait for the build to complete (5-10 minutes)

8. Once deployed, click **"Generate Domain"** to get your backend URL
   - Example: `https://your-app-backend.up.railway.app`

---

## Step 4: Deploy Frontend on Railway

1. In the same project, click **"New"** → **"GitHub Repo"**

2. Select the same repository again

3. **Configure for Frontend:**
   - Go to "Settings" tab
   - Root Directory: `frontend`
   - Build Command: `yarn install && yarn build`
   - Start Command: `npx serve -s build -l $PORT`

4. **Add Environment Variables:**
   
   | Variable | Value |
   |----------|-------|
   | `REACT_APP_BACKEND_URL` | `https://your-app-backend.up.railway.app` (your backend URL from Step 3) |

5. Click **"Deploy"**

6. Once deployed, click **"Generate Domain"** for your frontend URL
   - Example: `https://your-app-frontend.up.railway.app`

---

## Step 5: Test Your Deployment

1. Open your frontend URL in browser
2. Register a new account or login with existing credentials
3. Test basic functionality:
   - Dashboard loads
   - Can create products
   - Finance module works

---

## Troubleshooting

### Build Fails
- Check "Deploy Logs" for error messages
- Common issues:
  - Missing environment variables
  - Wrong root directory
  - Dependency conflicts

### App Crashes (Out of Memory)
- Free tier has only 0.5GB RAM
- Solution: Upgrade to Hobby plan ($5/month)
- Or reduce MongoDB operations

### Database Connection Fails
- Verify MongoDB Atlas whitelist includes `0.0.0.0/0`
- Check MONGO_URL format is correct
- Ensure password has no special characters that need URL encoding

### Frontend Can't Connect to Backend
- Verify `REACT_APP_BACKEND_URL` is set correctly
- Ensure backend is running (check health endpoint)
- Check CORS settings allow your frontend domain

---

## Cost Estimation (Free Tier)

| Usage | Estimated Duration |
|-------|-------------------|
| Light (demo/testing) | 3-4 weeks |
| Moderate (daily use) | 2 weeks |
| Heavy (production) | 1 week |

**Recommendation:** For production use, upgrade to Hobby plan (~$10-15/month)

---

## Quick Commands Reference

**Check Backend Health:**
```bash
curl https://your-app-backend.up.railway.app/api/health
```

**View Logs:**
- Railway Dashboard → Your Service → "Logs" tab

---

## File Structure for Railway

```
/app
├── railway.json          # Railway configuration
├── nixpacks.toml         # Build configuration
├── Procfile              # Process configuration
├── backend/
│   ├── server.py         # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
└── frontend/
    ├── package.json      # Node dependencies
    └── src/              # React source code
```

---

## Support

- Railway Docs: https://docs.railway.app
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com
- For app-specific issues: Check the Documentation page in the app

---

*Last Updated: March 8, 2026*
