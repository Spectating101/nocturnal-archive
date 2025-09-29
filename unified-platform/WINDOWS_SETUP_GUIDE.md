# Windows Setup Guide: OpenInterpreter + Groq for R/SQL AI Assistant

## Overview
This guide helps Windows users set up an interactive AI assistant that can help with R and SQL commands, with full file access and command execution capabilities.

## What You Get
- ✅ **Interactive AI Assistant** - Chat with AI about R/SQL commands
- ✅ **File Access** - AI can read your data files, scripts, and code
- ✅ **Command Execution** - AI can run R commands, SQL queries, etc.
- ✅ **Code Editing** - AI can modify your scripts and files
- ✅ **Free Tier** - 14,400 requests/day with Groq API

## Prerequisites
- **Windows 10/11** (or Windows 7/8 with Python 3.8+)
- **Python 3.8+** installed with pip
- **Internet connection** (for Groq API)
- **Administrator privileges** (for some installations)

## Quick Setup (Automated)

### Option 1: RStudio Terminal (Recommended for class)
1. **Open RStudio** → `Terminal` tab (not the Console)
2. **In Terminal**, run from this folder:
   ```cmd
   setup_rstudio_windows.bat
   ```
3. **Enter API key** when prompted (from https://console.groq.com/keys)
4. The assistant will auto-start in this Terminal
5. Next time, just run `start_assistant.bat`

### Option 2: Batch Script (outside RStudio)
1. **Download** `setup_windows.bat`
2. **Right-click** → "Run as administrator"
3. **Follow prompts**
4. **Run** `start_assistant.bat` to start using

### Option 2: PowerShell Script (For advanced users)
1. **Open PowerShell as Administrator**
2. **Run**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. **Download** `setup_windows.ps1`
4. **Run**: `.\setup_windows.ps1`
5. **Follow same steps** as Option 1

## Manual Setup (Step by Step)

### Step 1: Install Python
1. Go to https://www.python.org/downloads/
2. Download Python 3.8+ for Windows
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify: Open Command Prompt, type `python --version`

### Step 2: Create Virtual Environment
```cmd
# Open Command Prompt
python -m venv r_sql_assistant_env
r_sql_assistant_env\Scripts\activate.bat
```

### Step 3: Install OpenInterpreter
```cmd
# With virtual environment activated
pip install --upgrade pip
pip install open-interpreter
```

### Step 4: Get Groq API Key
1. Visit https://console.groq.com/keys
2. Sign up (free)
3. Create new API key
4. Copy the key (starts with `gsk_...`)

### Step 5: Set API Key
```cmd
# Option A: Set for current session
set GROQ_API_KEY=your-key-here

# Option B: Set permanently
setx GROQ_API_KEY "your-key-here"
```

### Step 6: Start Assistant
```cmd
# With virtual environment activated
interpreter --model groq/llama-3.1-70b-versatile
```

## Usage Examples

### Basic R Help
```
> How do I create a histogram in R?
> What's the syntax for ggplot2?
> How do I filter data in R?
```

### SQL Assistance
```
> What's the difference between INNER and LEFT JOIN?
> How do I write a subquery?
> Show me SQL syntax for GROUP BY
```

### File Analysis
```
> Read my data.csv file and tell me what's in it
> Analyze my R script and suggest improvements
> Help me debug this SQL query
```

### Code Generation
```
> Create an R script to load and visualize my data
> Write SQL to find duplicate records
> Generate R code for statistical analysis
```

## Available Models

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `groq/llama-3.1-70b-versatile` | Medium | High | **Recommended** |
| `groq/llama-3.1-8b-instant` | Fast | Good | Quick responses |
| `groq/mixtral-8x7b-32768` | Medium | High | Alternative option |

## Troubleshooting

### Common Issues

**"Python is not recognized"**
- Solution: Reinstall Python with "Add to PATH" checked
- Alternative: Add Python manually to system PATH

**"Permission denied"**
- Solution: Run Command Prompt as Administrator
- Alternative: Use PowerShell with proper execution policy

**"OpenInterpreter installation fails"**
- Solution: Try `pip install open-interpreter --no-deps`
- Alternative: Install dependencies manually

**"API key not working"**
- Solution: Verify key starts with `gsk_`
- Alternative: Regenerate key from Groq console

**"Virtual environment issues"**
- Solution: Delete `r_sql_assistant_env` folder and recreate
- Alternative: Use system-wide installation (not recommended)

### Performance Tips

**For Faster Responses:**
- Use `groq/llama-3.1-8b-instant` model
- Keep conversations focused
- Avoid very large file operations

**For Better Quality:**
- Use `groq/llama-3.1-70b-versatile` model
- Provide clear, specific questions
- Include context in your requests

## Alternative: Ollama (Offline)

If you prefer offline operation or have API limitations:

### Install Ollama
1. Download from https://ollama.ai/download
2. Install and restart terminal
3. Pull lightweight model: `ollama pull llama3.2:1b`
4. Run: `ollama run llama3.2:1b`

### Limitations of Ollama
- ❌ No file access (conversation only)
- ❌ No command execution
- ❌ Requires local hardware (4GB+ RAM)
- ✅ Works offline
- ✅ No API key needed

## Linux Note

If you're on Linux (including RStudio on Linux), there's a one‑click installer in this folder:
```bash
chmod +x ./setup_student_assistant.sh && ./setup_student_assistant.sh
```
Then launch "R/SQL Assistant" from your app menu, or run `./run_assistant.sh` from the project folder (works from RStudio Terminal as well).

## Files Created by Setup

After running setup scripts, you'll have:
- `r_sql_assistant_env/` - Virtual environment folder
- `start_assistant.bat` - Windows batch startup script
- `start_assistant.ps1` - PowerShell startup script
- `setup_api_key.bat` - API key configuration script

## Support

### For Students:
- Check this guide first
- Try troubleshooting section
- Contact professor or TA

### For Professors:
- Test setup on different Windows versions
- Prepare demo questions
- Have backup Ollama option ready

## Security Notes

- **API Keys**: Never share your Groq API key
- **File Access**: AI can read/modify files in your workspace
- **Internet**: Requires internet connection for Groq API
- **Privacy**: Groq may log conversations (check their privacy policy)

## Next Steps

1. **Test the setup** with sample R/SQL questions
2. **Prepare demo** for your professor
3. **Create backup plan** (Ollama for offline use)
4. **Document any issues** for future reference

---

**Ready to revolutionize your R/SQL learning experience!** 🚀