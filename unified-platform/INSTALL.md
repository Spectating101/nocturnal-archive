# Vertikal - Installation Guide

## 🚀 One-Line Installation

```bash
# Download and install Vertikal
curl -sSL https://raw.githubusercontent.com/your-repo/vertikal.py | python3 -c "
import sys, urllib.request, os
code = urllib.request.urlopen('https://raw.githubusercontent.com/your-repo/vertikal.py').read().decode()
with open('vertikal.py', 'w') as f: f.write(code)
os.chmod('vertikal.py', 0o755)
print('✅ Vertikal installed!')
"
```

## 📦 Manual Installation

### Step 1: Download
```bash
# Download the single file
curl -O https://raw.githubusercontent.com/your-repo/vertikal.py
chmod +x vertikal.py
```

### Step 2: Install Dependencies
```bash
# Install Groq client
pip3 install groq
```

### Step 3: Get API Key
1. Go to: https://console.groq.com/
2. Sign up (free)
3. Get your API key
4. Set it: `export GROQ_API_KEY="your_key_here"`

## 🎯 Usage in RStudio

### Method 1: Direct Command
```bash
# In RStudio Terminal
cd /path/to/your/project
python3 /path/to/vertikal.py --project-root .
```

### Method 2: Launcher Script
```bash
# Create launcher (run once)
cat > vertikal_launcher.sh << 'EOF'
#!/bin/bash
export GROQ_API_KEY="your_key_here"
python3 /path/to/vertikal.py --project-root .
EOF
chmod +x vertikal_launcher.sh

# Use launcher
./vertikal_launcher.sh
```

### Method 3: Alias (Recommended)
```bash
# Add to your ~/.bashrc or ~/.zshrc
alias vertikal='python3 /path/to/vertikal.py --project-root .'

# Then just run:
vertikal
```

## 🔧 Environment Setup

### For RStudio Users
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export GROQ_API_KEY="your_key_here"
export VERTIKAL_PATH="/path/to/vertikal.py"

# Create alias
alias vertikal='python3 $VERTIKAL_PATH --project-root .'
```

### For Class/Workshop Setup
```bash
# Create a setup script for students
cat > setup_vertikal.sh << 'EOF'
#!/bin/bash
echo "Setting up Vertikal for class..."

# Download Vertikal
curl -O https://raw.githubusercontent.com/your-repo/vertikal.py
chmod +x vertikal.py

# Install dependencies
pip3 install groq

# Set up environment
echo 'export GROQ_API_KEY="your_class_key_here"' >> ~/.bashrc
echo 'alias vertikal="python3 $(pwd)/vertikal.py --project-root ."' >> ~/.bashrc

echo "✅ Setup complete! Restart your terminal or run: source ~/.bashrc"
EOF

chmod +x setup_vertikal.sh
```

## 📋 Quick Test

```bash
# Test installation
python3 vertikal.py --help

# Test with demo
python3 demo_vertikal.py
```

## 🎓 For Instructors

### Class Distribution
1. **Single file**: Just share `vertikal.py`
2. **With setup**: Include `install_vertikal_simple.sh`
3. **Pre-configured**: Include API key in setup script

### Student Instructions
```bash
# Students run this once:
curl -O https://raw.githubusercontent.com/your-repo/vertikal.py
chmod +x vertikal.py
pip3 install groq
export GROQ_API_KEY="class_key_here"

# Then use in any project:
cd /path/to/project
python3 /path/to/vertikal.py --project-root .
```

## 🔒 Security Notes

- **API Key**: Keep your Groq API key secure
- **Project Root**: Vertikal only accesses files within the specified directory
- **Safe Mode**: Enabled by default, prevents path traversal
- **Read-Only**: Cannot modify or delete files

## 📞 Support

- **Documentation**: See `QUICK_START.md`
- **Demo**: Run `python3 demo_vertikal.py`
- **Issues**: Check GitHub issues or contact instructor

Happy coding! 🤖
