# Vertikal - Terminal File-Aware Assistant

A minimal ChatGPT-like assistant that lives in your terminal and can see your project files. Perfect for RStudio's Terminal pane.

## What it does

- **File Navigation**: List directories, read files, search content
- **R/SQL Help**: Ask programming questions with context from your files
- **Safe & Secure**: Sandboxed to your project directory only
- **Fast**: Uses Groq's lightning-fast LLM
- **Terminal Native**: Works in any terminal, including RStudio

## Quick Start

### 1. Get Groq API Key
```bash
# Visit: https://console.groq.com/
# Sign up and get your free API key
export GROQ_API_KEY="your_key_here"
```

### 2. Run Vertikal
```bash
python3 vertikal.py
```

### 3. Use it
```
vertikal:.> list
vertikal:.> read README.md
vertikal:.> search "function"
vertikal:.> How do I create a histogram in R?
```

## Commands

- `list` - List files in current directory
- `read <filename>` - Read file content
- `search <query>` - Search for text in files
- `<any question>` - Ask about your project or code

## Examples

```bash
# List files
vertikal:project> list

# Read a file
vertikal:project> read analysis.R

# Search for functions
vertikal:project> search "ggplot"

# Ask R questions
vertikal:project> How do I create a scatter plot in R?

# Ask SQL questions  
vertikal:project> Write a SQL query to find top customers
```

## Security Features

- ✅ **Path Traversal Protection**: Blocks `../` and absolute paths
- ✅ **Project Sandbox**: Only access files within project directory
- ✅ **Read-Only**: Cannot modify or delete files
- ✅ **Safe Mode**: Enabled by default

## RStudio Integration

1. Open RStudio
2. Go to Terminal pane (Tools → Terminal → New Terminal)
3. Navigate to your project: `cd /path/to/your/project`
4. Run: `python3 vertikal.py`
5. Start chatting!

## Demo

```bash
# Test without API key
python3 demo_vertikal.py
```

## Installation

### Option 1: Direct Download
```bash
# Download vertikal.py
curl -O https://raw.githubusercontent.com/your-repo/vertikal.py
chmod +x vertikal.py
```

### Option 2: pip install (coming soon)
```bash
pip install vertikal
```

## Requirements

- Python 3.8+
- Groq API key (free at console.groq.com)
- Internet connection

## Why Vertikal?

- **Faster than web ChatGPT**: No window switching
- **Context-aware**: Sees your actual project files
- **Terminal native**: Works in RStudio, VS Code, any terminal
- **Safe**: Sandboxed to your project only
- **Free**: Uses Groq's free tier

## Comparison

| Feature | ChatGPT Web | Vertikal |
|---------|-------------|----------|
| Speed | Slow (web) | Fast (terminal) |
| File Access | Manual copy/paste | Automatic |
| Context | Limited | Full project |
| Cost | Paid | Free (Groq) |
| RStudio | No | Yes |

## Troubleshooting

### "GROQ_API_KEY not set"
```bash
export GROQ_API_KEY="your_key_here"
```

### "Access denied" errors
- Vertikal only accesses files within your project directory
- This is a security feature, not a bug

### Slow responses
- Check your internet connection
- Groq is usually very fast (< 1 second)

## License

MIT License - Use freely for personal and educational projects.
