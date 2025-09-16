#!/bin/bash

# Nocturnal Archive - Deployment Script
# This script helps you deploy to Railway, Render, or Vercel

echo "🚀 Nocturnal Archive Deployment Script"
echo "======================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if all files are committed
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes. Please commit them first:"
    echo "   git add ."
    echo "   git commit -m 'Ready for deployment'"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  .env.local not found. Creating template..."
    cp env.example .env.local
    echo "📝 Please edit .env.local with your API keys before deploying"
    echo ""
fi

echo "📋 Deployment Options:"
echo "1. Railway (Recommended - Easiest)"
echo "2. Render (Alternative)"
echo "3. Vercel (Web Interface)"
echo "4. Local Testing"
echo ""

read -p "Choose deployment option (1-4): " choice

case $choice in
    1)
        echo "🚂 Deploying to Railway..."
        echo ""
        echo "📝 Steps:"
        echo "1. Go to https://railway.app"
        echo "2. Sign in with GitHub (student account)"
        echo "3. Click 'New Project'"
        echo "4. Select 'Deploy from GitHub repo'"
        echo "5. Choose your Nocturnal-Archive repository"
        echo "6. Add environment variables in Railway dashboard"
        echo "7. Add MongoDB and Redis services"
        echo ""
        echo "🔗 Your app will be available at: https://your-app-name.railway.app"
        ;;
    2)
        echo "🎨 Deploying to Render..."
        echo ""
        echo "📝 Steps:"
        echo "1. Go to https://render.com"
        echo "2. Sign in with GitHub (student account)"
        echo "3. Click 'New +' → 'Web Service'"
        echo "4. Connect your GitHub repo"
        echo "5. Configure build and start commands"
        echo "6. Add environment variables"
        echo ""
        echo "🔗 Your app will be available at: https://your-app-name.onrender.com"
        ;;
    3)
        echo "⚡ Deploying to Vercel..."
        echo ""
        echo "📝 Steps:"
        echo "1. Go to https://vercel.com"
        echo "2. Sign in with GitHub (student account)"
        echo "3. Click 'New Project'"
        echo "4. Import your GitHub repo"
        echo "5. Configure build settings"
        echo "6. Add environment variables"
        echo ""
        echo "🔗 Your app will be available at: https://your-app-name.vercel.app"
        ;;
    4)
        echo "🧪 Testing locally..."
        echo ""
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            echo "📦 Creating virtual environment..."
            python3 -m venv venv
        fi
        
        echo "🔧 Activating virtual environment..."
        source venv/bin/activate
        
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
        
        echo "🚀 Starting local server..."
        echo "📝 Make sure you have API keys in .env.local"
        echo ""
        echo "🔗 Your app will be available at: http://localhost:8000"
        echo "📚 API docs: http://localhost:8000/docs"
        echo "❤️  Health check: http://localhost:8000/health"
        echo ""
        echo "Press Ctrl+C to stop the server"
        echo ""
        
        python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo "❌ Invalid option. Please choose 1-4."
        exit 1
        ;;
esac

echo ""
echo "📚 For detailed instructions, see DEPLOYMENT_GUIDE.md"
echo "🎉 Good luck with your deployment!"
