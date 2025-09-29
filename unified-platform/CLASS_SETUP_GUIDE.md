# R/SQL AI Assistant Setup Guide for Class

## Overview
This guide helps you set up an interactive AI assistant for R and SQL commands that works directly in terminal/R Studio.

## What You Get
- ✅ Interactive AI assistance for R/SQL commands
- ✅ Works in terminal, R Studio, or any environment
- ✅ Free tier available (14,400 requests/day with Groq)
- ✅ No high-end hardware requirements
- ✅ Easy setup for students

## Option 1: Groq API (Recommended - Free Tier)

### For Students (Linux): One‑click install
1. **Get free API key**: visit https://console.groq.com/keys
2. **Run installer** from this folder:
   ```bash
   chmod +x ./setup_student_assistant.sh && ./setup_student_assistant.sh
   ```
3. **Start the assistant**:
   - From your application launcher: "R/SQL Assistant"
   - Or from terminal/RStudio Terminal:
     ```bash
     ./run_assistant.sh
     ```
   - If the key was not set during install, run:
     ```bash
     export GROQ_API_KEY='your-key-here' && ./run_assistant.sh
     ```

### For Professor:
- **Demo**: Show students how to ask questions like:
  - "How do I create a histogram in R?"
  - "What's the SQL syntax for JOIN?"
  - "How do I filter data in R?"

## Option 2: Ollama (Offline - No Internet Required)

### Setup:
```bash
# Download Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull lightweight model
ollama pull llama3.2:1b  # ~1GB, works on most laptops
# OR
ollama pull phi3:mini     # ~2GB, Microsoft's model
```

### Usage:
```bash
# Start interactive session
ollama run llama3.2:1b

# Ask questions
> How do I create a scatter plot in R?
> What's the SQL syntax for GROUP BY?
```

## Option 3: What's Currently Working (Mystery Integration)

**Current Status**: You have an AI assistant working directly in R Studio terminal
- ✅ Already functional
- ✅ Can see workspace files
- ✅ Can run R commands
- ❓ Unknown how it's integrated
- ❓ May not be replicable for students

## Comparison Table

| Option | Cost | Internet | Setup | Hardware | Reliability |
|--------|------|----------|-------|----------|-------------|
| Groq API | Free tier | Required | Easy | Any | High |
| Ollama | Free | Not needed | Medium | 4GB+ RAM | High |
| Current Setup | Unknown | Unknown | Unknown | Unknown | Unknown |

## Recommended Approach for Class

### Primary: Groq API Setup
1. **Professor**: Set up Groq account, get API key
2. **Students**: Follow setup script, get individual API keys
3. **Backup**: Provide Ollama instructions for offline use

### Demo Script for Professor:
```bash
# Show basic usage
python3 r_sql_assistant.py

# Example questions to demonstrate:
# "How do I load a CSV file in R?"
# "What's the difference between INNER and LEFT JOIN?"
# "How do I create a bar chart with ggplot2?"
```

## Files Created:
- `r_sql_assistant.py` - Main assistant script
- `setup_student_assistant.sh` - Student setup script
- `CLASS_SETUP_GUIDE.md` - This guide

## Next Steps:
1. Test Groq API setup
2. Create student accounts
3. Prepare demo questions
4. Set up backup Ollama option
5. Document the mystery integration (if replicable)

## Support:
- Groq Documentation: https://console.groq.com/docs
- Ollama Documentation: https://ollama.ai/docs
- Issues: Contact professor or TA