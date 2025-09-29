#!/bin/bash

# Vertikal Installation Script
# Installs the minimal terminal file-aware assistant

set -e

echo "🚀 Installing Vertikal - Terminal File-Aware Assistant"
echo "======================================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Check if Groq is installed
if ! python3 -c "import groq" 2>/dev/null; then
    echo "📦 Installing Groq Python client..."
    pip3 install groq
else
    echo "✅ Groq client already installed"
fi

# Make vertikal.py executable
chmod +x vertikal.py
echo "✅ Made vertikal.py executable"

# Test installation
echo "🧪 Testing installation..."
python3 demo_vertikal.py

echo
echo "🎉 Installation complete!"
echo
echo "Next steps:"
echo "1. Get your free Groq API key: https://console.groq.com/"
echo "2. Set environment variable: export GROQ_API_KEY='your_key'"
echo "3. Run: python3 vertikal.py"
echo
echo "For RStudio:"
echo "1. Open RStudio Terminal pane"
echo "2. Navigate to your project: cd /path/to/project"
echo "3. Run: python3 vertikal.py"
echo
echo "Happy coding! 🤖"
