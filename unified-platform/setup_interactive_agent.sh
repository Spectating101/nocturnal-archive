#!/bin/bash

# Setup Interactive Agent - Makes the system work like Claude
# This script sets up the interactive agent with conversation memory and tool integration

echo "🤖 Setting up Interactive Agent (Like Claude)"
echo "=" * 50

# Check if we're in the right directory
if [ ! -f "interactive_agent.py" ]; then
    echo "❌ Error: interactive_agent.py not found"
    echo "💡 Make sure you're in the unified-platform directory"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "server_venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv server_venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source server_venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn groq requests pydantic

# Check for API keys
echo "🔑 Checking for Groq API keys..."
if [ -z "$GROQ_API_KEY_1" ] && [ -z "$GROQ_API_KEY_2" ] && [ -z "$GROQ_API_KEY_3" ]; then
    echo "⚠️  No Groq API keys found in environment"
    echo "💡 You need to set at least one Groq API key:"
    echo "   export GROQ_API_KEY_1='your_groq_api_key_here'"
    echo "   export GROQ_API_KEY_2='your_second_groq_api_key_here' (optional)"
    echo "   export GROQ_API_KEY_3='your_third_groq_api_key_here' (optional)"
    echo ""
    echo "🔗 Get free API keys at: https://console.groq.com/keys"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
else
    echo "✅ Found Groq API keys"
fi

# Create environment file
echo "📝 Creating environment file..."
cat > .env << EOF
# Interactive Agent Environment
SERVER_HOST=0.0.0.0
SERVER_PORT=8001

# Groq API Keys (set these in your shell)
# GROQ_API_KEY_1=your_first_groq_api_key
# GROQ_API_KEY_2=your_second_groq_api_key
# GROQ_API_KEY_3=your_third_groq_api_key
EOF

# Make scripts executable
chmod +x interactive_client.py
chmod +x interactive_agent.py

# Test the setup
echo "🧪 Testing setup..."
python3 -c "
import sys
try:
    import fastapi
    import uvicorn
    import groq
    import requests
    import pydantic
    print('✅ All dependencies installed successfully')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "🚀 To start the Interactive Agent:"
    echo "   source server_venv/bin/activate"
    echo "   python3 interactive_agent.py"
    echo ""
    echo "💬 To use the Interactive Client:"
    echo "   source server_venv/bin/activate"
    echo "   python3 interactive_client.py"
    echo ""
    echo "🌐 The agent will be available at: http://localhost:8001"
    echo "📚 API docs will be at: http://localhost:8001/docs"
    echo ""
    echo "💡 Example usage:"
    echo "   'What files are in the current directory?'"
    echo "   'Read the file README.md and summarize it'"
    echo "   'Check if R is installed and what packages are available'"
    echo "   'Create a simple R script that calculates the mean of 1:10'"
    echo ""
    echo "🔧 The Interactive Agent can:"
    echo "   📁 Read and write files"
    echo "   🔍 Search directories"
    echo "   💻 Run commands (safely)"
    echo "   📊 Check R environment"
    echo "   🧠 Multi-step reasoning"
    echo "   💬 Remember conversations"
    echo ""
    echo "🎯 This makes your system work like me (Claude)!"
else
    echo "❌ Setup failed"
    exit 1
fi