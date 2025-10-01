#!/bin/bash
# Production Deployment Script

echo "🚀 NOCTURNAL PLATFORM - PRODUCTION DEPLOYMENT"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "integrated_server.py" ]; then
    echo "❌ Not in the right directory. Please run from unified-platform/"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ Production environment file not found!"
    echo "📝 Please create .env.production with your settings"
    exit 1
fi

# Copy production environment
echo "📋 Setting up production environment..."
cp .env.production .env

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set production environment variables
echo "🌙 Setting production environment variables..."
export FINSIGHT_STRICT=true
export ARCHIVE_STRICT=true
export NO_MOCK_DATA=true
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export DEBUG=false

# Run production tests
echo "🧪 Running production tests..."
python3 production_test.py

if [ $? -eq 0 ]; then
    echo "✅ Production tests passed!"
else
    echo "❌ Production tests failed!"
    echo "⚠️ Please check the issues above before deploying"
    exit 1
fi

# Start production server
echo "🚀 Starting production server..."
echo "📍 Server will be available at: http://0.0.0.0:8000"
echo "📚 API docs: http://0.0.0.0:8000/docs"
echo "🔍 Health check: http://0.0.0.0:8000/health"
echo ""
echo "🎯 PRODUCTION MODE ENABLED:"
echo "   • Real SEC EDGAR data only"
echo "   • Real academic papers only"
echo "   • No mock data allowed"
echo "   • Strict error handling"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 start_production.py