# Complete Deployment Guide: Render + MongoDB Atlas
## For Beginners - No Command Line Required!

---

# 📋 Overview

| What | Where | Cost |
|------|-------|------|
| Database | MongoDB Atlas | FREE |
| Backend API | Render.com | FREE |
| Frontend | Render.com | FREE |
| Custom Domain | erp.urbnsw.com | FREE (you own domain) |

**Total Time:** ~45 minutes
**Difficulty:** Easy (just clicking and copy-pasting)

---

# PART 1: MongoDB Atlas Setup (15 minutes)

## Step 1.1: Create MongoDB Atlas Account

1. Open your browser and go to: **https://www.mongodb.com/atlas**

2. Click the green button **"Try Free"**

3. Fill in the registration form:
   - Full Name: Your name
   - Email: Your email
   - Password: Create a strong password
   
4. Click **"Create Your Atlas Account"**

5. Check your email and click the verification link

6. You'll be asked some questions - just select:
   - "I'm learning MongoDB" 
   - Skip any other questions by clicking "Finish"

---

## Step 1.2: Create FREE Database Cluster

1. After login, you'll see "Deploy your database" page

2. Select **"M0 FREE"** option (it's on the right side, says FREE forever)

3. Choose a cloud provider and region:
   - Provider: **AWS** (recommended)
   - Region: Select one close to you or your users
     - If you're in Sri Lanka: Choose **Singapore** or **Mumbai**
   
4. Cluster Name: Leave as "Cluster0" or type "erp-cluster"

5. Click **"Create Deployment"** (green button)

6. Wait 1-3 minutes for cluster to be created (you'll see "Creating..." status)

---

## Step 1.3: Create Database User

A popup will appear asking to create a database user:

1. **Username:** Type `erp_admin`

2. **Password:** Click **"Autogenerate Secure Password"**

3. **⚠️ IMPORTANT: Click "Copy" button next to the password and save it somewhere safe!**
   - Open Notepad and paste it there
   - You'll need this password later
   - Example: `Xy7kL9mN2pQr`

4. Click **"Create Database User"**

---

## Step 1.4: Allow Network Access (Allow Connections)

1. The popup will show "Where would you like to connect from?"

2. Click **"Add My Current IP Address"** 
   
3. Then click **"+ Add a Different IP Address"**

4. In the IP Address field, type: `0.0.0.0/0`
   - This allows connections from anywhere (needed for Render)

5. Click **"Add Entry"**

6. Click **"Finish and Close"**

---

## Step 1.5: Get Your Connection String

1. On the left sidebar, click **"Database"** (under DEPLOYMENT)

2. Find your cluster and click **"Connect"** button

3. A popup appears - click **"Drivers"** (under "Connect your application")

4. You'll see a connection string that looks like:
   ```
   mongodb+srv://erp_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

5. Click **"Copy"** button to copy this string

6. **Open Notepad and edit the string:**
   
   - Replace `<password>` with your actual password (from Step 1.3)
   - Add database name `erp_db` before the `?`
   
   **Before:**
   ```
   mongodb+srv://erp_admin:<password>@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   ```
   
   **After (example):**
   ```
   mongodb+srv://erp_admin:Xy7kL9mN2pQr@cluster0.abc123.mongodb.net/erp_db?retryWrites=true&w=majority
   ```

7. **Save this connection string! You'll need it for Render setup.**

---

## ✅ MongoDB Atlas Complete!

Your database is ready. Keep your Notepad open with:
- [ ] Password: `Xy7kL9mN2pQr` (your actual password)
- [ ] Connection String: `mongodb+srv://erp_admin:Xy7kL9mN2pQr@cluster0.abc123.mongodb.net/erp_db?retryWrites=true&w=majority`

---

# PART 2: Push Code to GitHub (10 minutes)

## Step 2.1: Save to GitHub from Emergent

1. In the Emergent chat window, look at the bottom

2. Find and click **"Save to GitHub"** button

3. If not logged in to GitHub:
   - Click "Connect GitHub"
   - Login to your GitHub account
   - Authorize Emergent

4. Choose repository option:
   - Select **"Create new repository"**
   - Name: `erp-system` (or any name you want)
   - Make it **Private** (recommended)

5. Click **"Save"** or **"Push"**

6. Wait for the upload to complete (you'll see a success message)

7. **Note your repository URL:** `https://github.com/YOUR_USERNAME/erp-system`

---

# PART 3: Deploy Backend on Render (10 minutes)

## Step 3.1: Create Render Account

1. Go to: **https://render.com**

2. Click **"Get Started for Free"**

3. Click **"GitHub"** to sign up with GitHub (easiest!)

4. Authorize Render to access your GitHub

5. You're now in the Render Dashboard

---

## Step 3.2: Create Backend Service

1. Click **"New +"** button (top right)

2. Select **"Web Service"**

3. Connect your repository:
   - Find `erp-system` in the list
   - Click **"Connect"**
   - If you don't see it, click "Configure account" and give Render access

4. Configure the service:

   | Setting | Value |
   |---------|-------|
   | **Name** | `erp-backend` |
   | **Region** | Singapore (or closest to you) |
   | **Branch** | `main` |
   | **Root Directory** | `backend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Select **"Free"** |

5. **Add Environment Variables:**
   
   Scroll down to "Environment Variables" section and click **"Add Environment Variable"** for each:

   | Key | Value |
   |-----|-------|
   | `MONGO_URL` | Your MongoDB connection string from Part 1 |
   | `DB_NAME` | `erp_db` |
   | `JWT_SECRET` | `erp-secret-key-urbansw-2024-secure` |

   Example for MONGO_URL:
   ```
   mongodb+srv://erp_admin:Xy7kL9mN2pQr@cluster0.abc123.mongodb.net/erp_db?retryWrites=true&w=majority
   ```

6. Click **"Create Web Service"**

7. **Wait for deployment (5-10 minutes)**
   - You'll see build logs scrolling
   - Wait until you see "Your service is live 🎉"

8. **Copy your backend URL:**
   - Look at the top of the page
   - You'll see something like: `https://erp-backend-xxxx.onrender.com`
   - **Save this URL!**

---

## Step 3.3: Test Backend

1. Open a new browser tab

2. Go to: `https://erp-backend-xxxx.onrender.com/api/health`
   (Replace with your actual URL)

3. You should see:
   ```json
   {"status":"healthy","database":"connected"}
   ```

4. If you see this, your backend is working! ✅

---

# PART 4: Deploy Frontend on Render (10 minutes)

## Step 4.1: Create Frontend Service

1. Go back to Render Dashboard: https://dashboard.render.com

2. Click **"New +"** button (top right)

3. Select **"Static Site"** (Frontend is static files)

4. Connect your repository:
   - Find `erp-system` again
   - Click **"Connect"**

5. Configure the service:

   | Setting | Value |
   |---------|-------|
   | **Name** | `erp-frontend` |
   | **Branch** | `main` |
   | **Root Directory** | `frontend` |
   | **Build Command** | `yarn install && yarn build` |
   | **Publish Directory** | `build` |

6. **Add Environment Variable:**

   Click **"Add Environment Variable"**:

   | Key | Value |
   |-----|-------|
   | `REACT_APP_BACKEND_URL` | Your backend URL from Part 3 (e.g., `https://erp-backend-xxxx.onrender.com`) |

7. Click **"Create Static Site"**

8. **Wait for deployment (3-5 minutes)**

9. **Copy your frontend URL:**
   - Example: `https://erp-frontend-xxxx.onrender.com`

---

## Step 4.2: Test Frontend

1. Open your frontend URL in browser

2. You should see the ERP login page!

3. Register a new account or login

---

# PART 5: Setup Custom Domain (erp.urbnsw.com) (10 minutes)

## Step 5.1: Add Custom Domain in Render

### For Frontend (main site):

1. In Render Dashboard, click on your **`erp-frontend`** service

2. Click **"Settings"** tab

3. Scroll down to **"Custom Domains"**

4. Click **"Add Custom Domain"**

5. Enter: `erp.urbnsw.com`

6. Click **"Save"**

7. Render will show you DNS settings. You'll see something like:
   ```
   Type: CNAME
   Name: erp
   Value: erp-frontend-xxxx.onrender.com
   ```
   
   **Copy these values!**

---

## Step 5.2: Add DNS Record in Your Domain Provider

You need to add a DNS record where you bought your domain (OrangeHost, GoDaddy, Namecheap, etc.)

### For OrangeHost/cPanel:

1. Login to your **OrangeHost cPanel**

2. Find and click **"Zone Editor"** or **"DNS Zone Editor"**
   - (It might be under "Domains" section)

3. Select your domain: `urbnsw.com`

4. Click **"+ Add Record"** or **"Manage"**

5. Add a **CNAME Record**:

   | Field | Value |
   |-------|-------|
   | Type | `CNAME` |
   | Name | `erp` |
   | Target/Points to | `erp-frontend-xxxx.onrender.com` (your Render URL) |
   | TTL | `14400` (or Auto) |

6. Click **"Add Record"** or **"Save"**

---

## Step 5.3: Wait for DNS Propagation

1. DNS changes take **5 minutes to 48 hours** to work worldwide
   - Usually works within 5-30 minutes

2. Go back to Render Dashboard → `erp-frontend` → Settings → Custom Domains

3. Wait until you see a **green checkmark** ✅ next to your domain

4. Once green, visit: **https://erp.urbnsw.com**

5. Your ERP is now live on your custom domain! 🎉

---

## Step 5.4: (Optional) Add Custom Domain for Backend API

If you want API at `api.urbnsw.com`:

1. In Render, go to `erp-backend` service

2. Settings → Custom Domains → Add `api.urbnsw.com`

3. Add another CNAME record in cPanel:
   - Name: `api`
   - Target: `erp-backend-xxxx.onrender.com`

4. Update your frontend environment variable:
   - Go to `erp-frontend` → Environment
   - Change `REACT_APP_BACKEND_URL` to `https://api.urbnsw.com`
   - Click Save → Render will redeploy automatically

---

# PART 6: Final Testing Checklist

## Test Your Live ERP:

- [ ] Open `https://erp.urbnsw.com`
- [ ] Login page appears
- [ ] Can register new account
- [ ] Can login
- [ ] Dashboard loads with data
- [ ] Can create a product
- [ ] Can view Chart of Accounts
- [ ] Can run payroll functions

---

# 📝 Your Important Information (Save This!)

Fill in and save these details:

```
=== MY ERP DEPLOYMENT DETAILS ===

MongoDB Atlas:
- Login: https://cloud.mongodb.com
- Cluster: Cluster0
- Database: erp_db
- Username: erp_admin
- Password: _______________

Render:
- Dashboard: https://dashboard.render.com
- Backend URL: https://erp-backend-xxxx.onrender.com
- Frontend URL: https://erp-frontend-xxxx.onrender.com

Custom Domain:
- ERP URL: https://erp.urbnsw.com
- API URL: https://api.urbnsw.com (if configured)

GitHub:
- Repository: https://github.com/YOUR_USERNAME/erp-system
```

---

# ⚠️ Important Notes

## Free Tier Limitations:

1. **App Sleeps After 15 Minutes of Inactivity**
   - First visit after sleep takes ~30 seconds to load
   - This is normal for free tier
   - The app will wake up and work normally

2. **750 Free Hours Per Month**
   - Enough for personal use
   - If you need more, upgrade to $7/month

3. **MongoDB Atlas 512MB Limit**
   - Enough for thousands of records
   - Monitor usage in Atlas dashboard

## To Keep App Awake (Optional):

Use a free service like UptimeRobot to ping your site every 14 minutes:
1. Go to https://uptimerobot.com (free account)
2. Add a monitor for `https://erp.urbnsw.com`
3. Set interval to 5 minutes
4. Your app will rarely sleep!

---

# 🆘 Troubleshooting

## Problem: "Application Error" on Render

**Solution:**
1. Go to Render Dashboard
2. Click on the service (backend or frontend)
3. Click "Logs" tab
4. Look for red error messages
5. Common fixes:
   - Check environment variables are correct
   - Make sure MONGO_URL has real password (not `<password>`)
   - Check MongoDB Atlas IP whitelist includes `0.0.0.0/0`

## Problem: "Cannot connect to database"

**Solution:**
1. Go to MongoDB Atlas
2. Click "Network Access" (left sidebar)
3. Make sure `0.0.0.0/0` is in the list
4. If not, click "Add IP Address" and add `0.0.0.0/0`

## Problem: Frontend shows blank page

**Solution:**
1. Check browser console (Press F12 → Console tab)
2. Usually means `REACT_APP_BACKEND_URL` is wrong
3. Go to Render → erp-frontend → Environment
4. Verify the backend URL is correct
5. Make sure it starts with `https://`

## Problem: Custom domain not working

**Solution:**
1. DNS takes up to 48 hours (usually 5-30 min)
2. Check cPanel CNAME record is correct
3. Use https://dnschecker.org to verify propagation
4. Make sure Render shows green checkmark for domain

---

# ✅ Deployment Complete!

Congratulations! Your ERP is now live at **https://erp.urbnsw.com**

**What you have:**
- ✅ Full ERP system running free
- ✅ MongoDB database (512MB free)
- ✅ Custom domain configured
- ✅ Automatic deployments from GitHub
- ✅ SSL/HTTPS included free

**Total Cost: $0/month**

---

*Guide Created: March 8, 2026*
*For: E1 ERP System - Urban Streetwear*
