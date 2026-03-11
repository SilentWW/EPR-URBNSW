# E1 ERP System - Render.com Deployment Guide

## Prerequisites
1. A Render.com account
2. A MongoDB Atlas database (free tier available)
3. This codebase pushed to GitHub

---

## Option 1: Blueprint Deployment (Recommended)

1. **Push code to GitHub**
   - Use the "Save to Github" button in Emergent

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables**
   - In Render Dashboard, set `MONGO_URL` for the backend service
   - Example: `mongodb+srv://user:pass@cluster.mongodb.net/erp_system`

4. **Deploy!**

---

## Option 2: Manual Deployment

### Backend (Web Service)

1. **Create New Web Service**
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Root Directory: `backend`

2. **Environment Variables**
   ```
   MONGO_URL=mongodb+srv://your-connection-string
   DB_NAME=erp_system
   JWT_SECRET=your-secret-key-here
   CORS_ORIGINS=*
   ```

### Frontend (Static Site)

1. **Create New Static Site**
   - Build Command: `yarn install && yarn build`
   - Publish Directory: `build`
   - Root Directory: `frontend`

2. **Environment Variables**
   ```
   REACT_APP_BACKEND_URL=https://your-backend-service.onrender.com
   ```

3. **Add Rewrite Rule**
   - Source: `/*`
   - Destination: `/index.html`
   - Action: Rewrite

---

## MongoDB Atlas Setup

1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create a free cluster
3. Create a database user
4. Whitelist IP: `0.0.0.0/0` (allow all for Render)
5. Get connection string and add to Render's `MONGO_URL`

---

## Post-Deployment Checklist

- [ ] Backend health check: `https://your-backend.onrender.com/api/health`
- [ ] Frontend loads correctly
- [ ] User registration works
- [ ] Login/logout works
- [ ] All modules accessible

---

## Troubleshooting

### CORS Issues
If you get CORS errors, update `CORS_ORIGINS` in backend environment:
```
CORS_ORIGINS=https://your-frontend.onrender.com
```

### Database Connection Issues
- Verify MongoDB Atlas IP whitelist includes `0.0.0.0/0`
- Check connection string format
- Ensure database user has read/write permissions

### Build Failures
- Check Render logs for specific errors
- Ensure all dependencies are in requirements.txt / package.json

---

## File Structure for Render

```
/
├── render.yaml          # Render blueprint config
├── backend/
│   ├── server.py        # FastAPI application
│   ├── requirements.txt # Python dependencies
│   ├── routes/          # API routes
│   └── .env             # (local only, not deployed)
└── frontend/
    ├── package.json     # Node dependencies
    ├── src/             # React source
    └── public/          # Static assets
```

---

## Support

For issues with:
- **Render**: [render.com/docs](https://render.com/docs)
- **MongoDB Atlas**: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
