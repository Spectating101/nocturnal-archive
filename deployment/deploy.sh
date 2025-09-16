#!/bin/bash

# Nocturnal Archive Deployment Script
# This script will deploy the entire system using GitHub Student Developer Pack

echo "🚀 Starting Nocturnal Archive Deployment..."

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create deployment directory if it doesn't exist
mkdir -p deployment

echo "📋 Step 1: Preparing deployment files..."

# Copy deployment configs
cp deployment/railway.toml ./
cp deployment/vercel.json ./chatbot-ui/

echo "✅ Deployment files prepared"

echo "📋 Step 2: Setting up environment variables..."

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production not found. Please create it from env.production.template"
    echo "   Fill in your actual values for:"
    echo "   - MONGODB_URI"
    echo "   - REDIS_URL" 
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - SENTRY_DSN"
    echo "   - API keys"
    exit 1
fi

echo "✅ Environment variables configured"

echo "📋 Step 3: Installing dependencies..."

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd chatbot-ui
npm install
cd ..

echo "✅ Dependencies installed"

echo "📋 Step 4: Building frontend..."

cd chatbot-ui
npm run build
cd ..

echo "✅ Frontend built"

echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Create accounts for required services (MongoDB Atlas, Redis Cloud, etc.)"
echo "2. Fill in .env.production with your actual credentials"
echo "3. Deploy backend to Railway"
echo "4. Deploy frontend to Vercel"
echo "5. Configure custom domain"
echo ""
echo "Run 'bash deployment/deploy.sh' again after setting up credentials"
