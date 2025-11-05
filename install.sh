#!/bin/bash
# Cite-Agent Installer - One-command installation
set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Installing Cite-Agent v1.4.0                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION detected"
echo ""

# Install pipx if not present (handles PATH automatically)
echo "Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ pipx installed"
else
    echo "✅ pipx already installed"
fi
echo ""

# Install cite-agent with pipx
echo "Installing cite-agent..."
pipx install cite-agent --force
echo "✅ cite-agent installed"
echo ""

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding to PATH..."
    
    # Detect shell
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    # Add PATH
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ Added to $SHELL_RC"
else
    echo "✅ PATH already configured"
fi
echo ""

# Verify installation
echo "Verifying installation..."
if command -v cite-agent &> /dev/null; then
    cite-agent --version
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║  Installation successful!                                 ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Run: cite-agent --setup  # First-time setup"
    echo "Then: cite-agent \"Find papers on AI\""
else
    echo "⚠️  Command not found in current shell. Try:"
    echo "   source $SHELL_RC"
    echo "   cite-agent --version"
fi
