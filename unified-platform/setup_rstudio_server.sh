#!/usr/bin/env bash
set -e

# RStudio Server Integration Setup
# Sets up R/SQL Assistant to work seamlessly with RStudio

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
LAUNCHER="$PROJECT_DIR/run_rstudio_assistant.sh"
DESKTOP_FILE="$HOME/.local/share/applications/R_SQL_Assistant_RStudio.desktop"

echo "🚀 Setting up R/SQL Assistant for RStudio"
echo "=========================================="

# Check if Python 3 is available
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 is required. Please install Python 3.8+ and re-run." >&2
  exit 1
fi

# Check if R is available
if ! command -v R >/dev/null 2>&1; then
  echo "⚠️  R is not found. The assistant will work but R-specific features will be limited."
  echo "💡 Install R from: https://cran.r-project.org/"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install requests

# Get server URL
echo ""
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

# Check if running in RStudio
if [ -n "$RSTUDIO" ] || [ -n "$RSTUDIO_PANDOC" ]; then
    echo "🎯 RStudio detected - using enhanced integration"
    exec python3 "$SCRIPT_DIR/rstudio_integration.py"
else
    echo "💻 Terminal mode - using standard client"
    exec python3 "$SCRIPT_DIR/r_sql_assistant_client.py"
fi
LAUNCH
chmod +x "$LAUNCHER"

# Create desktop entry
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=R/SQL Assistant (RStudio)
Comment=AI assistant for R and SQL with RStudio integration
Exec=$LAUNCHER
Terminal=true
Categories=Development;Education;Science;
Icon=applications-science
EOF

update_desktop_db >/dev/null 2>&1 || true

# Create RStudio add-in (optional)
R_ADDIN_DIR="$HOME/.local/share/R/rstudio/addins"
if [ -d "$R_ADDIN_DIR" ] || mkdir -p "$R_ADDIN_DIR" 2>/dev/null; then
    cat > "$R_ADDIN_DIR/r_sql_assistant_addin.R" <<'EOF'
# R/SQL Assistant RStudio Add-in
# Provides quick access to AI assistant from RStudio

library(shiny)
library(miniUI)

r_sql_assistant_addin <- function() {
  ui <- miniPage(
    gadgetTitleBar("R/SQL Assistant"),
    miniContentPanel(
      textInput("question", "Ask a question about R or SQL:", 
                placeholder = "e.g., How do I create a histogram?",
                width = "100%"),
      actionButton("ask", "Ask Assistant", class = "btn-primary"),
      br(), br(),
      verbatimTextOutput("response")
    )
  )
  
  server <- function(input, output, session) {
    observeEvent(input$ask, {
      if (nchar(input$question) > 0) {
        # Call the Python assistant
        cmd <- paste0("python3 '", getwd(), "/rstudio_integration.py' --question '", 
                     input$question, "'")
        result <- system(cmd, intern = TRUE)
        output$response <- renderText(paste(result, collapse = "\n"))
      }
    })
  }
  
  runGadget(ui, server)
}

# Register the add-in
if (interactive()) {
  r_sql_assistant_addin()
}
EOF
    echo "✅ RStudio add-in created"
fi

echo ""
echo "🎉 RStudio integration setup complete!"
echo ""
echo "✅ You can now:"
echo "- Run from RStudio Terminal: $LAUNCHER"
echo "- Run from system terminal: $LAUNCHER"
echo "- Find 'R/SQL Assistant (RStudio)' in your application launcher"
echo ""
echo "🔧 Configuration:"
echo "- Server URL: $SERVER_URL"
echo "- User ID: ${USER_ID:-'anonymous'}"
echo "- Config file: $PROJECT_DIR/.env"
echo ""
echo "💡 Features:"
echo "- Automatic RStudio detection"
echo "- R environment context"
echo "- Enhanced R/SQL assistance"
echo "- No API keys needed (handled by server)"
echo ""
echo "🚀 Ready to use! Start asking questions about R and SQL!"

exit 0
