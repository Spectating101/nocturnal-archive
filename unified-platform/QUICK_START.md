# Vertikal - Quick Start Guide

## 🚀 For RStudio Users

### Step 1: Download Vertikal
```bash
# Download the single file
curl -O https://raw.githubusercontent.com/your-repo/vertikal.py
chmod +x vertikal.py
```

### Step 2: Get Groq API Key (Free)
1. Go to: https://console.groq.com/
2. Sign up (free)
3. Get your API key
4. Set it: `export GROQ_API_KEY="your_key_here"`

### Step 3: Use in RStudio
1. **Open RStudio**
2. **Terminal pane**: Tools → Terminal → New Terminal
3. **Navigate to your project**: `cd /path/to/your/project`
4. **Run Vertikal**: `python3 /path/to/vertikal.py --project-root .`

### Step 4: Start Chatting!
```
vertikal:your-project> list
vertikal:your-project> read data.csv
vertikal:your-project> How do I create a histogram in R?
```

## 📋 Complete Example Session

```bash
# 1. Open RStudio Terminal
# 2. Navigate to your project
$ cd /home/user/my-finance-project

# 3. Run Vertikal
$ python3 /home/user/vertikal.py --project-root .

📁 Project root: /home/user/my-finance-project
🔒 Safe mode: ON

🤖 Vertikal - Terminal Assistant
========================================
Commands: list, read <file>, search <query>, or just ask questions
Type 'quit' to exit, 'help' for more info

vertikal:my-finance-project> list
📂 .
📁 data/
📄 analysis.R
📄 data.csv
📄 README.md

vertikal:my-finance-project> read data.csv
📄 data.csv

Date,Stock,Return
2023-01-01,AAPL,0.05
2023-01-02,AAPL,-0.02
...

vertikal:my-finance-project> How do I calculate portfolio returns in R?
🤔 Thinking...

To calculate portfolio returns in R, you can use the following approach:

```r
# Load required libraries
library(dplyr)
library(PerformanceAnalytics)

# Read your data
data <- read.csv("data.csv")

# Calculate portfolio returns (equal-weighted)
portfolio_returns <- data %>%
  group_by(Date) %>%
  summarise(portfolio_return = mean(Return, na.rm = TRUE))

# Or weighted by market cap
portfolio_returns_weighted <- data %>%
  group_by(Date) %>%
  summarise(portfolio_return = weighted.mean(Return, MarketCap, na.rm = TRUE))
```

vertikal:my-finance-project> search "portfolio"
🔍 Search results for 'portfolio':

📄 analysis.R
  15: portfolio_returns <- mean(returns)
  23: portfolio_risk <- sd(returns)

vertikal:my-finance-project> quit
👋 Goodbye!
```

## 🎯 What You Can Do

### File Operations
- `list` - See all files in your project
- `read filename` - Read any file (R, CSV, text, etc.)
- `search "keyword"` - Find text across all files

### Programming Help
- "How do I create a scatter plot in R?"
- "Write a SQL query to find top customers"
- "What's wrong with this ggplot code?"
- "How do I handle missing data?"

### Data Analysis
- "Explain this dataset"
- "What statistical test should I use?"
- "How do I create a correlation matrix?"

## 🔧 Troubleshooting

### "python3 not found"
```bash
# Try python instead
python /path/to/vertikal.py --project-root .
```

### "GROQ_API_KEY not set"
```bash
# Set your API key
export GROQ_API_KEY="your_key_here"
```

### "Permission denied"
```bash
# Make sure vertikal.py is executable
chmod +x vertikal.py
```

## 💡 Pro Tips

1. **Keep Vertikal running** - Don't close the terminal
2. **Use specific questions** - "How do I create a histogram?" vs "Help with R"
3. **Search first** - `search "function_name"` to find existing code
4. **Copy code blocks** - Vertikal provides copy-pasteable R code
5. **One question at a time** - For best results

## 🎓 Perfect For

- **Finance/Econometrics courses**
- **Data analysis projects**
- **R/SQL programming help**
- **Research with real datasets**
- **Learning with actual data**

Happy coding! 🤖
