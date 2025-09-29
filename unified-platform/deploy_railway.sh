#!/usr/bin/env bash
set -e

echo "🚀 Deploying R/SQL Assistant to Railway"
echo "======================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - R/SQL Assistant Server"
    echo "✅ Git repository initialized"
else
    echo "📦 Updating git repository..."
    git add .
    git commit -m "Update R/SQL Assistant Server" || echo "No changes to commit"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Push to GitHub:"
echo "   git remote add origin https://github.com/yourusername/r-sql-assistant.git"
echo "   git push -u origin main"
echo ""
echo "2. Deploy to Railway:"
echo "   - Go to https://railway.app"
echo "   - Sign in with GitHub"
echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
echo "   - Select your repository"
echo ""
echo "3. Add environment variables in Railway dashboard:"
echo "   - GROQ_API_KEY_1=your_first_key"
echo "   - GROQ_API_KEY_2=your_second_key"
echo "   - GROQ_API_KEY_3=your_third_key"
echo "   - GROQ_API_KEY_4=your_fourth_key"
echo "   - GROQ_API_KEY_5=your_fifth_key"
echo ""
echo "4. Get your server URL and update client scripts"
echo ""
echo "📚 See RAILWAY_DEPLOYMENT.md for detailed instructions"
echo ""
echo "🎉 Your server will be live at: https://your-app-name.railway.app"
