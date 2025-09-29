#!/usr/bin/env bash
set -e

# Client setup script for R/SQL Assistant
# Sets up client to connect to server (no API keys needed)

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
LAUNCHER="$PROJECT_DIR/run_assistant.sh"
DESKTOP_FILE="$HOME/.local/share/applications/R_SQL_Assistant_Client.desktop"

echo "==> Setting up R/SQL Assistant Client"
echo "====================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required. Please install Python 3.8+ and re-run." >&2
  exit 1
fi

# Create virtual environment
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

# Install client dependencies
pip install requests

# Get server URL
echo
read -r -p "Enter server URL (default: http://localhost:8000): " SERVER_URL
SERVER_URL=${SERVER_URL:-"http://localhost:8000"}

# Get user ID
read -r -p "Enter your user ID (optional): " USER_ID

# Create environment file
cat > "$PROJECT_DIR/.env" <<EOF
ASSISTANT_SERVER_URL=$SERVER_URL
USER_ID=$USER_ID
EOF

# Create launcher script
cat > "$LAUNCHER" << 'LAUNCH'
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

exec python3 "$SCRIPT_DIR/r_sql_assistant_client.py"
LAUNCH
chmod +x "$LAUNCHER"

# Create desktop entry
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=R/SQL Assistant Client
Comment=Client for R/SQL AI assistant server
Exec=$LAUNCHER
Terminal=true
Categories=Development;Education;
EOF

update_desktop_db >/dev/null 2>&1 || true

echo "==> Client setup complete!"
echo ""
echo "✅ You can now:"
echo "- Run from terminal: $LAUNCHER"
echo "- Or find 'R/SQL Assistant Client' in your application launcher"
echo ""
echo "🔧 Configuration:"
echo "- Server URL: $SERVER_URL"
echo "- User ID: ${USER_ID:-'anonymous'}"
echo "- Config file: $PROJECT_DIR/.env"
echo ""
echo "💡 No API keys needed - the server handles everything!"

exit 0
