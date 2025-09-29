#!/usr/bin/env bash
set -e

# Complete Railway deployment script for R/SQL Assistant Server
# Handles git setup, Railway deployment, and configuration

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME="r-sql-assistant-server"

echo "🚀 Deploying R/SQL Assistant to Railway"
echo "======================================"

# Check if git is available
if ! command -v git >/dev/null 2>&1; then
    echo "❌ Git is required. Please install git and re-run."
    exit 1
fi

# Check if Railway CLI is available (optional)
if command -v railway >/dev/null 2>&1; then
    echo "✅ Railway CLI detected"
    USE_RAILWAY_CLI=true
else
    echo "⚠️  Railway CLI not found. Will use web deployment."
    USE_RAILWAY_CLI=false
fi

# Initialize git repository if needed
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - R/SQL Assistant Server with API key rotation"
    echo "✅ Git repository initialized"
else
    echo "📦 Updating git repository..."
    git add .
    git commit -m "Update R/SQL Assistant Server" || echo "No changes to commit"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Environment files
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv/
server_venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Test files
test_*.py
*_test.py
EOF
    echo "✅ .gitignore created"
fi

# Create deployment instructions
cat > DEPLOYMENT_INSTRUCTIONS.md << 'EOF'
# Railway Deployment Instructions

## Quick Deploy

1. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/yourusername/r-sql-assistant-server.git
   git push -u origin main
   ```

2. **Deploy to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python and deploy

3. **Configure Environment Variables:**
   In Railway dashboard, add these variables:
   ```
   GROQ_API_KEY_1=your_first_groq_api_key
   GROQ_API_KEY_2=your_second_groq_api_key
   GROQ_API_KEY_3=your_third_groq_api_key
   GROQ_API_KEY_4=your_fourth_groq_api_key
   GROQ_API_KEY_5=your_fifth_groq_api_key
   ```

4. **Get Your Server URL:**
   Railway will provide a URL like: `https://your-app-name.railway.app`

5. **Update Client Scripts:**
   Update the server URL in client configuration files.

## Alternative: Railway CLI

If you have Railway CLI installed:
```bash
railway login
railway init
railway up
railway variables set GROQ_API_KEY_1=your_key_here
railway variables set GROQ_API_KEY_2=your_key_here
# ... add all keys
```

## Testing

After deployment, test your server:
```bash
curl https://your-app-name.railway.app/
curl https://your-app-name.railway.app/status
```

## Client Setup

Update client scripts with your Railway URL:
```bash
export ASSISTANT_SERVER_URL=https://your-app-name.railway.app
./run_rstudio_assistant.sh
```
EOF

echo ""
echo "🎯 Next steps:"
echo ""
echo "1. 📤 Push to GitHub:"
echo "   git remote add origin https://github.com/yourusername/$REPO_NAME.git"
echo "   git push -u origin main"
echo ""
echo "2. 🚀 Deploy to Railway:"
echo "   - Go to https://railway.app"
echo "   - Sign in with GitHub"
echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
echo "   - Select your repository"
echo ""
echo "3. 🔑 Add API Keys in Railway Dashboard:"
echo "   - GROQ_API_KEY_1=your_first_key"
echo "   - GROQ_API_KEY_2=your_second_key"
echo "   - GROQ_API_KEY_3=your_third_key"
echo "   - GROQ_API_KEY_4=your_fourth_key"
echo "   - GROQ_API_KEY_5=your_fifth_key"
echo ""
echo "4. 🌐 Get your server URL and update client scripts"
echo ""
echo "📚 See DEPLOYMENT_INSTRUCTIONS.md for detailed steps"
echo ""
echo "🎉 Your server will be live at: https://your-app-name.railway.app"

# If Railway CLI is available, offer to deploy directly
if [ "$USE_RAILWAY_CLI" = true ]; then
    echo ""
    read -p "🚀 Deploy directly with Railway CLI? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Deploying with Railway CLI..."
        railway login
        railway init
        railway up
        echo "✅ Deployment initiated!"
        echo "💡 Don't forget to set your API keys:"
        echo "   railway variables set GROQ_API_KEY_1=your_key_here"
    fi
fi

echo ""
echo "🎯 Ready for beta testing with 75 users!"
echo "💰 Cost: $0 (free with GitHub Student Pack)"
echo "🔧 API Keys: 3-5 Groq free tier keys"
echo "📊 Capacity: 1,000+ users (15x more than needed)"
