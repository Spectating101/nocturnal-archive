#!/bin/bash
# Nocturnal Archive - Environment Setup Script
# This script helps you set Railway environment variables quickly

set -e

echo "=============================================="
echo "🌙 Nocturnal Archive - Railway Setup"
echo "=============================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo "  OR"
    echo "  brew install railway"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Not logged in to Railway. Logging in..."
    railway login
fi

echo "✅ Logged in to Railway"
echo ""

# Generate JWT secret
echo "🔑 Generating JWT secret..."
JWT_SECRET=$(openssl rand -hex 32)
railway variables set JWT_SECRET_KEY="$JWT_SECRET"
echo "✅ JWT_SECRET_KEY set"

# Set environment
railway variables set ENV="production"
echo "✅ ENV set to production"

echo ""
echo "=============================================="
echo "📝 Now, let's set your API keys"
echo "=============================================="
echo ""

# Groq keys
echo "Enter your Groq API keys (press Enter to skip):"
read -p "GROQ_API_KEY_1: " groq1
if [ ! -z "$groq1" ]; then
    railway variables set GROQ_API_KEY_1="$groq1"
    echo "✅ GROQ_API_KEY_1 set"
fi

read -p "GROQ_API_KEY_2: " groq2
if [ ! -z "$groq2" ]; then
    railway variables set GROQ_API_KEY_2="$groq2"
    echo "✅ GROQ_API_KEY_2 set"
fi

read -p "GROQ_API_KEY_3: " groq3
if [ ! -z "$groq3" ]; then
    railway variables set GROQ_API_KEY_3="$groq3"
    echo "✅ GROQ_API_KEY_3 set"
fi

read -p "GROQ_API_KEY_4 (optional): " groq4
if [ ! -z "$groq4" ]; then
    railway variables set GROQ_API_KEY_4="$groq4"
    echo "✅ GROQ_API_KEY_4 set"
fi

echo ""

# Cerebras keys
echo "Enter your Cerebras API keys (press Enter to skip):"
read -p "CEREBRAS_API_KEY_1: " cerebras1
if [ ! -z "$cerebras1" ]; then
    railway variables set CEREBRAS_API_KEY_1="$cerebras1"
    echo "✅ CEREBRAS_API_KEY_1 set"
fi

read -p "CEREBRAS_API_KEY_2: " cerebras2
if [ ! -z "$cerebras2" ]; then
    railway variables set CEREBRAS_API_KEY_2="$cerebras2"
    echo "✅ CEREBRAS_API_KEY_2 set"
fi

read -p "CEREBRAS_API_KEY_3: " cerebras3
if [ ! -z "$cerebras3" ]; then
    railway variables set CEREBRAS_API_KEY_3="$cerebras3"
    echo "✅ CEREBRAS_API_KEY_3 set"
fi

echo ""

# Download tracking
read -p "Enter your GitHub username (for download tracking): " github_user
if [ ! -z "$github_user" ]; then
    railway variables set GITHUB_RELEASE_BASE="https://github.com/$github_user/nocturnal-archive/releases/download"
    railway variables set VERSION="v0.9.0-beta"
    echo "✅ Download tracking configured"
fi

echo ""
echo "=============================================="
echo "✅ Environment setup complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Add PostgreSQL plugin: railway add --plugin postgresql"
echo "2. Deploy: railway up"
echo "3. Run migrations: railway run python run_migrations.py"
echo ""
echo "To view all variables: railway variables"
echo "To add more later: railway variables set KEY=value"
echo ""

