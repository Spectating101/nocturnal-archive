#!/bin/bash

# Vertikal - Simple Installation Script
# One-click setup for RStudio users

set -e

echo "🚀 Installing Vertikal - Terminal File-Aware Assistant"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "vertikal.py" ]; then
    echo "❌ vertikal.py not found in current directory"
    echo "Please run this script from the directory containing vertikal.py"
    exit 1
fi

# Make vertikal.py executable
chmod +x vertikal.py
echo "✅ Made vertikal.py executable"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found"

# Check if Groq is installed
if ! python3 -c "import groq" 2>/dev/null; then
    echo "📦 Installing Groq Python client..."
    pip3 install groq
else
    echo "✅ Groq client already installed"
fi

# Create a simple launcher script
cat > vertikal_launcher.sh << 'EOF'
#!/bin/bash
# Vertikal Launcher Script

# Check if GROQ_API_KEY is set
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY not set!"
    echo "Get your free API key from: https://console.groq.com/"
    echo "Then set it with: export GROQ_API_KEY='your_key_here'"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERTIKAL_PATH="$SCRIPT_DIR/vertikal.py"

# Check if vertikal.py exists
if [ ! -f "$VERTIKAL_PATH" ]; then
    echo "❌ vertikal.py not found at $VERTIKAL_PATH"
    exit 1
fi

# Run Vertikal with current directory as project root
python3 "$VERTIKAL_PATH" --project-root .
EOF

chmod +x vertikal_launcher.sh
echo "✅ Created vertikal_launcher.sh"

# Test installation
echo "🧪 Testing installation..."
python3 demo_vertikal.py

echo
echo "🎉 Installation complete!"
echo
echo "📋 Next steps:"
echo "1. Get your free Groq API key: https://console.groq.com/"
echo "2. Set it: export GROQ_API_KEY='your_key_here'"
echo "3. In RStudio Terminal:"
echo "   - Navigate to your project: cd /path/to/your/project"
echo "   - Run: /path/to/vertikal.py --project-root ."
echo "   - Or use the launcher: /path/to/vertikal_launcher.sh"
echo
echo "📖 See QUICK_START.md for detailed usage instructions"
echo
echo "Happy coding! 🤖"
