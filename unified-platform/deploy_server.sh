#!/usr/bin/env bash
set -e

# Server deployment script for R/SQL Assistant
# Sets up server with API key rotation

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/server_venv"
LOG_DIR="$PROJECT_DIR/logs"

echo "🚀 Deploying R/SQL Assistant Server"
echo "=================================="

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "📥 Installing server dependencies..."
pip install --upgrade pip
pip install -r "$PROJECT_DIR/server_requirements.txt"

# Create logs directory
mkdir -p "$LOG_DIR"

# Check for environment file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Please copy env_example.txt to .env and configure your API keys:"
    echo "   cp env_example.txt .env"
    echo "   nano .env"
    echo ""
    echo "🔑 You need at least 3-5 Groq API keys for the beta test"
    echo "💡 Get them from: https://console.groq.com/keys"
    exit 1
fi

# Load environment variables
echo "🔧 Loading environment variables..."
set -a
source "$PROJECT_DIR/.env"
set +a

# Validate API keys
key_count=0
for i in {1..10}; do
    if [ -n "${!GROQ_API_KEY_$i}" ]; then
        key_count=$((key_count + 1))
    fi
done

if [ $key_count -eq 0 ]; then
    echo "❌ No API keys found in .env file!"
    echo "🔧 Please add GROQ_API_KEY_1, GROQ_API_KEY_2, etc. to your .env file"
    exit 1
fi

echo "✅ Found $key_count API keys"

# Create systemd service file
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/r-sql-assistant.service > /dev/null <<EOF
[Unit]
Description=R/SQL Assistant Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/server.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/server.log
StandardError=append:$LOG_DIR/server_error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "🔄 Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable r-sql-assistant
sudo systemctl start r-sql-assistant

# Wait a moment and check status
sleep 3
if sudo systemctl is-active --quiet r-sql-assistant; then
    echo "✅ Server started successfully!"
    echo "🌐 Server running on: http://localhost:${SERVER_PORT:-8000}"
    echo "📊 Check status: sudo systemctl status r-sql-assistant"
    echo "📝 View logs: sudo journalctl -u r-sql-assistant -f"
    echo "🛑 Stop server: sudo systemctl stop r-sql-assistant"
else
    echo "❌ Failed to start server!"
    echo "📝 Check logs: sudo journalctl -u r-sql-assistant"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "📋 Next steps:"
echo "1. Test the server: curl http://localhost:${SERVER_PORT:-8000}/"
echo "2. Update client scripts to use server URL"
echo "3. Monitor usage: curl http://localhost:${SERVER_PORT:-8000}/stats"
