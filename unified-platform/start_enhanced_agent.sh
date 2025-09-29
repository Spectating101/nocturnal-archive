#!/bin/bash
# Start Enhanced Interactive Agent

echo "🚀 Starting Enhanced Interactive Agent..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your Groq API keys before running again."
    exit 1
fi

# Check R availability
echo "🔍 Checking R availability..."
if command -v R &> /dev/null; then
    R --version | head -1
    echo "✅ R is available"
else
    echo "⚠️  R not found. Some features may not work."
fi

# Start the enhanced agent
echo "🌟 Starting Enhanced Interactive Agent on port 8002..."
echo "📊 Monitor URL: http://localhost:8002/enhanced/health"
echo "💬 Chat URL: http://localhost:8002/enhanced/chat"
echo "📚 Docs URL: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 enhanced_interactive_agent.py