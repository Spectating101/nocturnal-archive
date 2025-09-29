# Railway Deployment Guide

## Quick Deploy to Railway (Free with GitHub Student Pack)

### 1. Prepare Your Repository

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - R/SQL Assistant Server"

# Push to GitHub
git remote add origin https://github.com/yourusername/r-sql-assistant.git
git push -u origin main
```

### 2. Deploy to Railway

1. **Go to [Railway.app](https://railway.app)**
2. **Sign in with GitHub** (use your student account)
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository**
6. **Railway will auto-detect Python and deploy**

### 3. Configure Environment Variables

In Railway dashboard:

1. **Go to your project**
2. **Click "Variables" tab**
3. **Add these variables:**

```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=$PORT

# API Keys (add 3-5 keys)
GROQ_API_KEY_1=your_first_groq_api_key_here
GROQ_API_KEY_2=your_second_groq_api_key_here
GROQ_API_KEY_3=your_third_groq_api_key_here
GROQ_API_KEY_4=your_fourth_groq_api_key_here
GROQ_API_KEY_5=your_fifth_groq_api_key_here
```

### 4. Get Your Server URL

Railway will give you a URL like:
```
https://your-app-name.railway.app
```

### 5. Update Client Configuration

Update your client setup to use the Railway URL:

```bash
# In client .env file
ASSISTANT_SERVER_URL=https://your-app-name.railway.app
```

## Alternative: Render Deployment

### 1. Go to [Render.com](https://render.com)
2. **Sign in with GitHub**
3. **Click "New +" → "Web Service"**
4. **Connect your repository**
5. **Configure:**
   - **Build Command:** `pip install -r server_requirements.txt`
   - **Start Command:** `python server.py`
   - **Environment:** Python 3

### 2. Add Environment Variables in Render Dashboard

Same variables as Railway above.

## Alternative: Fly.io Deployment

### 1. Install Fly CLI
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Create fly.toml
```toml
app = "your-app-name"
primary_region = "iad"

[build]

[env]
  SERVER_HOST = "0.0.0.0"
  SERVER_PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### 3. Deploy
```bash
fly auth login
fly launch
fly secrets set GROQ_API_KEY_1=your_key_here
fly secrets set GROQ_API_KEY_2=your_key_here
# ... add all keys
fly deploy
```

## Cost Comparison

| Platform | Free Tier | Best For |
|----------|-----------|----------|
| **Railway** | $5 credit/month | Easiest setup |
| **Render** | 750 hours/month | Reliable |
| **Fly.io** | 3 shared VMs | Performance |
| **Heroku** | Check your credits | Familiar |

## Recommended: Railway

**Why Railway:**
- ✅ **Easiest setup** (5 minutes)
- ✅ **Auto-deploy** from GitHub
- ✅ **Free tier** with GitHub Student Pack
- ✅ **Perfect for FastAPI** apps
- ✅ **Built-in monitoring**

## Next Steps

1. **Choose Railway** (recommended)
2. **Deploy your server**
3. **Get the server URL**
4. **Update client scripts** with the URL
5. **Start beta testing!**

Your server will be live at a URL like:
`https://r-sql-assistant-production.railway.app`

Then your beta users just need to:
```bash
# Set server URL in their client
export ASSISTANT_SERVER_URL=https://your-server.railway.app
./run_assistant.sh
```

No API keys needed for users - everything goes through your server!
