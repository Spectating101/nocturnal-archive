#!/bin/bash
# Run the integrated Nocturnal Platform server

echo "🌙 Starting Nocturnal Platform..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy env_simple.txt to .env and add your Groq API key:"
    echo "   cp env_simple.txt .env"
    echo "   nano .env  # Add your GROQ_API_KEY_1"
    exit 1
fi

# Check if Groq key is set (supports sk- and gsk_ prefixes)
if ! grep -Eq "^GROQ_API_KEY_1=(sk-|gsk_)" .env && ! grep -Eq "^GROQ_API_KEY=(sk-|gsk_)" .env; then
    echo "❌ Groq API key not found in .env!"
    echo "📝 Please add your Groq API key to .env:"
    echo "   GROQ_API_KEY_1=sk-... or GROQ_API_KEY_1=gsk_..."
    echo "   (or set GROQ_API_KEY if you prefer)"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Load environment variables
echo "📋 Loading environment variables..."
export $(grep -v '^#' .env | xargs)

# If GROQ_API_KEY is set but GROQ_API_KEY_1 is not, map it
if [ -n "${GROQ_API_KEY}" ] && [ -z "${GROQ_API_KEY_1}" ]; then
  export GROQ_API_KEY_1="${GROQ_API_KEY}"
fi

# Unset generic PROXIES var from other projects to avoid client init conflicts
unset PROXIES

# Start the server
echo "🚀 Starting integrated server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python integrated_server.py
