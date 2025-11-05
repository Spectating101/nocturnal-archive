#!/bin/bash
# Script to create all Optiplex Agent files

echo "Creating Optiplex Agent project files..."

# requirements.txt
cat > requirements.txt << 'EOF'
requests>=2.31.0
EOF

# .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.so
.Python
build/
dist/
*.egg-info/
venv/
.venv
.vscode/
.idea/
.DS_Store
.optiplex/
*.bak
EOF

echo "✅ Created requirements.txt and .gitignore"
