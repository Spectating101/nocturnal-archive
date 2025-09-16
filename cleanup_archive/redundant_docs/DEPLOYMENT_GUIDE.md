# Nocturnal Archive - Deployment Guide

## 🚀 **Quick Deploy with GitHub Student Pack**

### **Option 1: Railway (Recommended - Easiest)**

#### **Step 1: Prepare Your Repository**
```bash
# Make sure all files are committed
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

#### **Step 2: Deploy to Railway**
1. **Go to [railway.app](https://railway.app)**
2. **Sign in with GitHub** (use your student account)
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your `Nocturnal-Archive` repository**
6. **Railway will auto-detect Python/FastAPI**

#### **Step 3: Add Environment Variables**
In Railway dashboard, go to your project → Variables tab:

```bash
# Required API Keys
MISTRAL_API_KEY=your_mistral_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
CEREBRAS_API_KEY=your_cerebras_api_key_here

# Database URLs (Railway will provide these)
MONGODB_URL=mongodb://localhost:27017/nocturnal_archive
REDIS_URL=redis://localhost:6379

# Optional
LOG_LEVEL=INFO
MAX_RESEARCH_TIME=300
MAX_PAPERS_PER_QUERY=20
CACHE_TTL=3600
```

#### **Step 4: Add Database Services**
1. **Click "New Service"** in Railway
2. **Add MongoDB** (Railway will provide connection URL)
3. **Add Redis** (Railway will provide connection URL)
4. **Update environment variables** with the new URLs

#### **Step 5: Deploy**
- Railway will automatically deploy when you push to GitHub
- Get your live URL: `https://your-app-name.railway.app`

---

### **Option 2: Render (Alternative)**

#### **Step 1: Deploy to Render**
1. **Go to [render.com](https://render.com)**
2. **Sign in with GitHub** (student account)
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repo**
5. **Configure:**
   - **Name**: `nocturnal-archive`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

#### **Step 2: Add Environment Variables**
Same as Railway above.

#### **Step 3: Deploy**
- Render will build and deploy automatically
- Get your live URL: `https://your-app-name.onrender.com`

---

### **Option 3: Vercel (For Web Interface)**

#### **Step 1: Deploy to Vercel**
1. **Go to [vercel.com](https://vercel.com)**
2. **Sign in with GitHub** (student account)
3. **Click "New Project"**
4. **Import your GitHub repo**
5. **Vercel will auto-detect Python/FastAPI**

#### **Step 2: Configure**
- **Framework Preset**: Other
- **Build Command**: `pip install -r requirements.txt`
- **Output Directory**: `src`
- **Install Command**: `pip install -r requirements.txt`

#### **Step 3: Add Environment Variables**
Same as above.

#### **Step 4: Deploy**
- Vercel will deploy automatically
- Get your live URL: `https://your-app-name.vercel.app`

---

## 🗄️ **Database Setup**

### **MongoDB Atlas (Free Tier)**
1. **Go to [mongodb.com/atlas](https://mongodb.com/atlas)**
2. **Sign up with GitHub** (student account)
3. **Create free cluster** (M0 tier)
4. **Get connection string**
5. **Add to environment variables**

### **Redis Cloud (Free Tier)**
1. **Go to [redis.com/try-free](https://redis.com/try-free)**
2. **Sign up with GitHub** (student account)
3. **Create free database** (30MB)
4. **Get connection string**
5. **Add to environment variables**

---

## 🔑 **API Keys Setup**

### **Mistral AI**
1. **Go to [mistral.ai](https://mistral.ai)**
2. **Sign up for free account**
3. **Get API key from dashboard**
4. **Add to environment variables**

### **Cohere**
1. **Go to [cohere.ai](https://cohere.ai)**
2. **Sign up for free account**
3. **Get API key from dashboard**
4. **Add to environment variables**

### **Cerebras**
1. **Go to [cerebras.net](https://cerebras.net)**
2. **Sign up for free account**
3. **Get API key from dashboard**
4. **Add to environment variables**

---

## 🌐 **Custom Domain Setup**

### **Step 1: Buy Domain**
- **Namecheap**: $10-15/year
- **GoDaddy**: $10-15/year
- **Google Domains**: $12/year

### **Step 2: Point to Railway/Render/Vercel**
1. **Get your deployment URL**
2. **Go to domain registrar DNS settings**
3. **Add CNAME record:**
   - **Name**: `@` or `www`
   - **Value**: `your-app-name.railway.app`
4. **Wait 24-48 hours for propagation**

### **Step 3: Configure in Platform**
- **Railway**: Add custom domain in settings
- **Render**: Add custom domain in settings
- **Vercel**: Add custom domain in settings

---

## 🔒 **Security Checklist**

### **Environment Variables**
- ✅ **Never commit API keys** to GitHub
- ✅ **Use platform environment variables**
- ✅ **Rotate keys regularly**

### **CORS Configuration**
- ✅ **Configure allowed origins** for production
- ✅ **Limit to your domain**

### **Rate Limiting**
- ✅ **Platform handles basic rate limiting**
- ✅ **Consider additional rate limiting**

---

## 📊 **Monitoring & Analytics**

### **Railway**
- ✅ **Built-in monitoring**
- ✅ **Logs and metrics**
- ✅ **Performance insights**

### **Render**
- ✅ **Built-in monitoring**
- ✅ **Logs and metrics**
- ✅ **Uptime monitoring**

### **Vercel**
- ✅ **Built-in analytics**
- ✅ **Performance monitoring**
- ✅ **Error tracking**

---

## 🚀 **Deployment Commands**

### **Local Testing**
```bash
# Test locally before deploying
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Test with environment variables
export MISTRAL_API_KEY=your_key
export COHERE_API_KEY=your_key
export CEREBRAS_API_KEY=your_key
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### **GitHub Actions (Optional)**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: railway/deploy@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

---

## 🎯 **Post-Deployment Checklist**

### **Testing**
- ✅ **Health check**: `https://your-app.com/health`
- ✅ **API docs**: `https://your-app.com/docs`
- ✅ **Demo endpoint**: `https://your-app.com/api/demo`
- ✅ **Research endpoint**: `https://your-app.com/api/research`

### **Performance**
- ✅ **Response times** under 5 seconds
- ✅ **Database connections** working
- ✅ **API key authentication** working
- ✅ **Error handling** graceful

### **Security**
- ✅ **HTTPS** enabled
- ✅ **Environment variables** secure
- ✅ **CORS** configured
- ✅ **Rate limiting** active

---

## 💰 **Cost Breakdown (GitHub Student Pack)**

### **Free Tier Limits**
- **Railway**: $5/month credit (FREE with student pack)
- **Render**: Free tier available
- **Vercel**: Free tier available
- **MongoDB Atlas**: 512MB free
- **Redis Cloud**: 30MB free

### **Total Cost: $0/month** 🎉

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Build Failures**
```bash
# Check requirements.txt
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.11+
```

#### **Database Connection Issues**
```bash
# Test MongoDB connection
mongosh "your_mongodb_url"

# Test Redis connection
redis-cli -u "your_redis_url"
```

#### **API Key Issues**
```bash
# Test API keys locally
python -c "import os; print('Mistral:', bool(os.getenv('MISTRAL_API_KEY')))"
```

### **Support Resources**
- **Railway**: [docs.railway.app](https://docs.railway.app)
- **Render**: [render.com/docs](https://render.com/docs)
- **Vercel**: [vercel.com/docs](https://vercel.com/docs)

---

## 🎉 **You're Live!**

Once deployed, your Nocturnal Archive will be available at:
- **Main URL**: `https://your-app-name.railway.app`
- **API Docs**: `https://your-app-name.railway.app/docs`
- **Health Check**: `https://your-app-name.railway.app/health`

**Congratulations! Your research automation platform is now live and ready to revolutionize research workflows!** 🚀
