#!/bin/bash
# Developer Setup Script for Cite-Agent
# THIS IS FOR DEVELOPERS ONLY - DO NOT SHARE WITH USERS
# This allows testing locally without backend auth for faster development

echo "🔧 Setting up Cite-Agent for LOCAL DEVELOPMENT"
echo "========================================"
echo ""
echo "⚠️  WARNING: This bypasses backend authentication"
echo "⚠️  Use ONLY for development/testing"
echo "⚠️  Production users MUST use backend mode"
echo ""

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "❌ .env.local not found"
    echo ""
    echo "Create .env.local with your API keys:"
    echo ""
    echo "CEREBRAS_API_KEY=csk-your-key-here"
    echo "GROQ_API_KEY=gsk-your-key-here"
    echo "USE_LOCAL_KEYS=true"
    echo ""
    exit 1
fi

# Install in development mode
echo "📦 Installing in development mode..."
pip install -e . --quiet

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi

echo "✅ Installed successfully"
echo ""

# Export dev mode flag
export USE_LOCAL_KEYS=true
export CITE_AGENT_DEV_MODE=true

echo "✅ Development environment ready!"
echo ""
echo "Usage:"
echo "  export USE_LOCAL_KEYS=true"
echo "  cite-agent \"your query here\""
echo ""
echo "Or run:"
echo "  USE_LOCAL_KEYS=true cite-agent \"your query\""
echo ""



