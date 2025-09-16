#!/bin/bash

# Exit on error
set -e

echo "Setting up Nocturnal Archive development environment..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

# Check for Rust
if ! command -v cargo &> /dev/null; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
fi

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build Rust components
echo "Building Rust components..."
cargo build

# Create necessary directories
echo "Creating project directories..."
mkdir -p data/documents
mkdir -p data/vectors
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOL
MISTRAL_API_KEY=yoPu5xWfVjZT3ZVHQyQj313CiyrP8KSX
CEREBRAS_API_KEY=csk-34cp53294pcmrexym8h2r4x5cyy2npnrd344928yhf2hpctj
COHERE_API_KEY=Z3mJnh9hFLcvHt0UBpvYZkp8uVd3VbQXZ06pBA4o
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017/nocturnal_archive
LOG_LEVEL=debug
EOL
    echo "Please update .env.local with your API keys and configuration"
fi

# Fix any potential file permission issues
chmod +x scripts/*.sh

echo "Setup complete! Remember to:"
echo "1. Update .env with your API keys"
echo "2. Start your local MongoDB and Redis instances"
echo "3. Activate virtual environment with 'source .venv/bin/activate'"