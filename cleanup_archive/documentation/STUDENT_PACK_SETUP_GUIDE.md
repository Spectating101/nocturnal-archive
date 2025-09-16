# 🎓 Student Pack Setup Guide - Step by Step

## 🚀 **Ready to Deploy! Here's How We'll Do It**

I've prepared all the deployment files. Now let's get your accounts set up and deploy the Nocturnal Archive!

---

## 📋 **Step 1: Create Required Accounts (15 minutes)**

### **1. MongoDB Atlas (Database)**
1. Go to: https://www.mongodb.com/atlas
2. Click "Try Free" 
3. Sign up with your student email
4. Create a new cluster (choose the free M0 tier)
5. Create a database user
6. Get your connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)

### **2. Redis Cloud (Caching)**
1. Go to: https://redis.com/try-free/
2. Sign up with your student email
3. Create a new database (choose the free 30MB tier)
4. Get your connection string (looks like: `redis://username:password@host:port`)

### **3. Supabase (Authentication)**
1. Go to: https://supabase.com
2. Sign up with your student email
3. Create a new project
4. Go to Settings > API
5. Copy your Project URL and anon key

### **4. Sentry (Error Tracking)**
1. Go to: https://sentry.io
2. Sign up with your student email
3. Create a new project (choose Python)
4. Copy your DSN

### **5. Railway (Backend Hosting)**
1. Go to: https://railway.app
2. Sign up with your GitHub account
3. Connect your GitHub repository
4. You'll get a deployment URL

### **6. Vercel (Frontend Hosting)**
1. Go to: https://vercel.com
2. Sign up with your GitHub account
3. Import your repository
4. You'll get a deployment URL

---

## 🔧 **Step 2: Configure Environment Variables**

Once you have all the credentials, I'll help you create the `.env.production` file with your actual values.

**Just share the credentials with me in this format:**
```
MONGODB_URI: mongodb+srv://username:password@cluster.mongodb.net/nocturnal_archive
REDIS_URL: redis://username:password@host:port
SUPABASE_URL: https://your-project.supabase.co
SUPABASE_KEY: your-anon-key
SENTRY_DSN: https://your-sentry-dsn
```

---

## 🚀 **Step 3: Deploy Backend to Railway**

1. **Connect GitHub Repository:**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Nocturnal-Archive repository

2. **Configure Environment Variables:**
   - In Railway dashboard, go to your project
   - Click on "Variables" tab
   - Add all the environment variables from your `.env.production`

3. **Deploy:**
   - Railway will automatically deploy when you push to GitHub
   - You'll get a URL like: `https://your-app.railway.app`

---

## 🌐 **Step 4: Deploy Frontend to Vercel**

1. **Import Repository:**
   - Go to Vercel dashboard
   - Click "New Project"
   - Import your Nocturnal-Archive repository
   - Set root directory to `chatbot-ui`

2. **Configure Environment Variables:**
   - In Vercel dashboard, go to your project
   - Click on "Settings" > "Environment Variables"
   - Add all the `NEXT_PUBLIC_*` variables

3. **Deploy:**
   - Vercel will automatically deploy
   - You'll get a URL like: `https://your-app.vercel.app`

---

## 🎯 **Step 5: Test the Deployment**

1. **Test Backend:**
   - Visit your Railway URL + `/docs` (e.g., `https://your-app.railway.app/docs`)
   - You should see the FastAPI documentation

2. **Test Frontend:**
   - Visit your Vercel URL
   - You should see the Nocturnal Archive landing page
   - Try the chat interface

3. **Test Integration:**
   - Use the chat interface
   - Check if it connects to the backend
   - Test user authentication

---

## 🎉 **Step 6: Custom Domain (Optional)**

1. **Get Free Domain:**
   - Use your Namecheap student pack benefit
   - Get a free `.me` domain for 1 year

2. **Configure DNS:**
   - Point your domain to Vercel
   - Vercel will automatically handle SSL

---

## 🚨 **What I Need From You**

**Just share these credentials with me:**

1. **MongoDB Atlas connection string**
2. **Redis Cloud connection string** 
3. **Supabase URL and anon key**
4. **Sentry DSN**
5. **Railway deployment URL** (after you connect the repo)
6. **Vercel deployment URL** (after you import the repo)

**I'll handle all the technical configuration!**

---

## ⚡ **Quick Start Commands**

Once you have the credentials, I'll run these commands:

```bash
# 1. Set up environment variables
cp deployment/env.production.template .env.production
# (I'll fill in your actual values)

# 2. Prepare deployment
bash deployment/deploy.sh

# 3. Deploy backend
# (I'll guide you through Railway deployment)

# 4. Deploy frontend  
# (I'll guide you through Vercel deployment)

# 5. Test everything
# (I'll run comprehensive tests)
```

---

## 🎯 **Expected Timeline**

- **Account Creation**: 15 minutes
- **Environment Setup**: 10 minutes  
- **Backend Deployment**: 20 minutes
- **Frontend Deployment**: 15 minutes
- **Testing & Configuration**: 20 minutes
- **Total**: ~1.5 hours

---

## 🚀 **Ready to Start?**

**Just let me know when you've created the accounts and I'll guide you through the rest!**

The deployment will be:
- ✅ **100% Free** (using your student pack)
- ✅ **Professional grade** (production-ready)
- ✅ **Fully functional** (all features working)
- ✅ **Beta ready** (ready for testing)

**Let's get the Nocturnal Archive online!** 🎓✨
