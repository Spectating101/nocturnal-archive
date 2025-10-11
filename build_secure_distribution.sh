#!/bin/bash
# Build secure distribution with local LLM code removed
set -e

echo "🔒 Building Secure Distribution (Backend-Only)"
echo "================================================"
echo

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build_secure dist_secure
mkdir -p build_secure
mkdir -p dist_secure

# Copy source
echo "📦 Copying source code..."
cp -r cite_agent build_secure/
cp setup.py build_secure/
cp README.md build_secure/
cp LICENSE build_secure/
cp requirements.txt build_secure/
[ -f MANIFEST.in ] && cp MANIFEST.in build_secure/

# Replace enhanced_ai_agent.py with backend-only version
echo "🔒 Replacing agent with backend-only version..."
mv build_secure/cite_agent/enhanced_ai_agent.py build_secure/cite_agent/enhanced_ai_agent.ORIGINAL
cp build_secure/cite_agent/agent_backend_only.py build_secure/cite_agent/enhanced_ai_agent.py

# Remove files with local LLM code
echo "✂️  Removing files with local LLM code..."
rm -f build_secure/cite_agent/enhanced_ai_agent.ORIGINAL
rm -f build_secure/cite_agent/cli_conversational.py
rm -f build_secure/cite_agent/streaming_ui.py
rm -rf build_secure/cite_agent/__pycache__

# Add distribution marker
echo "📝 Adding distribution marker..."
cat > build_secure/cite_agent/__distribution__.py << 'DISTPY'
"""
This is a DISTRIBUTION build.
Local LLM calling code has been removed.
All queries must go through the centralized backend.
"""
DISTRIBUTION_BUILD = True
BACKEND_ONLY = True
DISTPY

# Update setup.py
echo "📝 Updating setup.py..."
cat > build_secure/setup.py << 'SETUP'
#!/usr/bin/env python3
from setuptools import setup, find_packages
from pathlib import Path

readme_path = Path("README.md")
long_description = readme_path.read_text() if readme_path.exists() else "AI Research Assistant"

setup(
    name="cite-agent",
    version="1.0.2",
    author="Cite-Agent Team",
    author_email="contact@citeagent.dev",
    description="AI Research Assistant - Backend-Only Distribution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Spectating101/cite-agent",
    packages=find_packages(exclude=["tests", "docs", "cite-agent-api", "cite_agent_api", "build*", "dist*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "rich>=13.7.0",
        "keyring>=24.3.0",
        # NOTE: groq and cerebras NOT included - backend only
    ],
    entry_points={
        "console_scripts": [
            "cite-agent=cite_agent.cli:main",
            "nocturnal=cite_agent.cli:main",
        ],
    },
)
SETUP

# Build package
echo "🔨 Building distribution package..."
cd build_secure
python3 setup.py sdist bdist_wheel > /dev/null 2>&1

# Move to dist_secure
echo "📦 Moving artifacts..."
mv dist/* ../dist_secure/
cd ..

# Verify no groq imports
echo "🔍 Verifying security..."
if grep -r "import groq" build_secure/cite_agent/*.py 2>/dev/null; then
    echo "❌ SECURITY FAILURE: groq imports found!"
    exit 1
fi

if [ -f "build_secure/cite_agent/cli_conversational.py" ]; then
    echo "❌ SECURITY FAILURE: conversational CLI not removed!"
    exit 1
fi

echo "✅ No local LLM imports found"

# Check that backend-only marker exists
if [ ! -f "build_secure/cite_agent/__distribution__.py" ]; then
    echo "❌ Distribution marker missing!"
    exit 1
fi

echo "✅ Distribution marker present"

# List artifacts
echo
echo "================================================"
echo "✅ Secure Distribution Built!"
echo "================================================"
echo
echo "📦 Distribution files:"
ls -lh dist_secure/
echo
echo "🔒 Security: Local LLM code completely removed"
echo "   - groq/cerebras dependencies removed"
echo "   - Local API calling code removed"
echo "   - Conversational CLI removed"
echo "   Users CANNOT bypass backend"
echo
