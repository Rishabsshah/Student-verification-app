# 🚀 Student Verification System - Render Deployment Guide

## 📋 Quick Deployment Steps

### 1. **Prepare Your Repository**

```bash
# Make sure all files are committed
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. **Create Web Service on Render**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `student-verification` (or your choice)
- **Region**: Choose closest to your location
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn CampusSafety.wsgi:application`

**Instance Type:**
- For hackathon: **Free** tier is fine
- For production: **Starter** or higher

### 3. **Environment Variables**

Click **"Advanced"** → **"Add Environment Variable"**

**Required Variables:**

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.13.1` | Python version |
| `SECRET_KEY` | `<generate-random-key>` | Django secret key |
| `DEBUG` | `False` | Set to False for production |

**To generate a secure SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. **Deploy!**

Click **"Create Web Service"** - Render will:
- ✅ Clone your repository
- ✅ Install dependencies
- ✅ Run `build.sh` (migrations + collectstatic)
- ✅ Start gunicorn server

**Build time:** ~10-15 minutes (first time - DeepFace model downloads)

---

## 📡 **After Deployment**

### Your App URLs:
- **Main App**: `https://your-app-name.onrender.com/`
- **ID Verification**: `https://your-app-name.onrender.com/id-verification/`
- **Admin Panel**: `https://your-app-name.onrender.com/admin/`

### Create Superuser (Optional):

Via Render Shell:
1. Go to your service → **"Shell"** tab
2. Run:
```bash
python manage.py createsuperuser
```

---

## 🔧 **Troubleshooting**

### Build Fails:

**Check logs:**
- Render Dashboard → Your Service → **"Logs"** tab

**Common issues:**
1. **Missing dependencies**: Check `requirements.txt`
2. **Build timeout**: Increase instance tier
3. **Static files 404**: Run `python manage.py collectstatic`

### App Crashes After Deploy:

```bash
# Check runtime logs in Render dashboard
# Common fixes:
- Set ALLOWED_HOSTS correctly
- Set DEBUG=False in production
- Check DATABASE_URL if using PostgreSQL
```

### DeepFace Model Download:

**First startup is slow (~10-15 min)** because:
- VGG-Face model downloads (~580MB)
- After first run, it's cached

---

## 🎯 **Hackathon Tips**

### Free Tier Limitations:
- ✅ Perfect for demo/hackathon
- ⚠️ Spins down after 15 min inactivity
- ⏱️ First request after spin-down: ~1 min cold start

### Keep It Awake:
Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your app every 14 minutes

### Demo Day:
- Wake up your app **5 minutes before** presenting
- Have backup screenshots/video ready
- Test complete flow beforehand

---

## 📊 **Features Deployed**

✅ ID Card OCR (OCR.space API)
✅ Face Recognition (DeepFace VGG-Face)
✅ Liveness Detection (MediaPipe)
✅ ResQ Server Sync
✅ Admin Dashboard
✅ User Authentication

---

## 🆘 **Need Help?**

**Render Docs**: https://render.com/docs
**Django Deployment**: https://docs.djangoproject.com/en/5.1/howto/deployment/

---

## ✨ **Post-Hackathon**

For production deployment:
1. Upgrade to **Starter** tier ($7/month)
2. Add **PostgreSQL** database
3. Set up **custom domain**
4. Enable **HTTPS** (automatic on Render)
5. Add **monitoring** and **logging**

---

**Good luck with your hackathon! 🚀**
