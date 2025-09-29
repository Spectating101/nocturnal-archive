#!/usr/bin/env bash
set -e

# Simple one-click installer for R/SQL AI Assistant (Linux)
# - Creates venv
# - Installs dependencies
# - Prompts for and saves GROQ_API_KEY
# - Creates launcher script and desktop entry

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="R_SQL_Assistant"
VENV_DIR="$PROJECT_DIR/.venv"
LAUNCHER="$PROJECT_DIR/run_assistant.sh"
DESKTOP_FILE="$HOME/.local/share/applications/${APP_NAME}.desktop"

echo "==> Setting up $APP_NAME"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required. Please install Python 3.8+ and re-run." >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [ -f "$PROJECT_DIR/requirements.txt" ]; then
  pip install -r "$PROJECT_DIR/requirements.txt"
else
  pip install groq
fi

echo
if [ -z "$GROQ_API_KEY" ]; then
  read -r -p "Enter your GROQ_API_KEY (from console.groq.com/keys): " KEY
else
  KEY="$GROQ_API_KEY"
fi

if [ -z "$KEY" ]; then
  echo "GROQ_API_KEY not provided. You can set it later in ~/.profile" >&2
else
  if ! grep -q "^export GROQ_API_KEY=" "$HOME/.profile" 2>/dev/null; then
    echo "export GROQ_API_KEY=\"$KEY\"" >> "$HOME/.profile"
  else
    sed -i "s/^export GROQ_API_KEY=.*/export GROQ_API_KEY=\"$KEY\"/" "$HOME/.profile"
  fi
  export GROQ_API_KEY="$KEY"
fi

cat > "$LAUNCHER" << 'LAUNCH'
#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
exec python3 "$SCRIPT_DIR/r_sql_assistant.py"
LAUNCH
chmod +x "$LAUNCHER"

mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=R/SQL Assistant
Comment=Interactive R/SQL AI assistant (Groq)
Exec=$LAUNCHER
Terminal=true
Categories=Development;Education;
EOF

update_desktop_db >/dev/null 2>&1 || true

echo "==> Installed. You can:"
echo "- Run from terminal: $LAUNCHER"
echo "- Or find 'R/SQL Assistant' in your application launcher"
echo "- Log out/in or 'source ~/.profile' to apply GROQ_API_KEY"

exit 0


