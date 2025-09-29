# Vertikal

Terminal file-aware ChatGPT assistant for RStudio and data analysis.

[![PyPI version](https://badge.fury.io/py/vertikal.svg)](https://badge.fury.io/py/vertikal)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

### 1. Install
```bash
pip install vertikal
```

### 2. Get API Key (Free)
- Visit [Groq Console](https://console.groq.com/)
- Sign up for free account
- Create API key

### 3. Set Environment Variable
```bash
export GROQ_API_KEY="your_key_here"
```

### 4. Use in RStudio Terminal
```bash
cd /path/to/your/project
vertikal --project-root .
```

## 💡 Usage Examples

```bash
vertikal:project> list
vertikal:project> read data.csv
vertikal:project> How do I create a histogram in R?
vertikal:project> search "regression"
vertikal:project> What's in the README file?
vertikal:project> quit
```

## 🎯 Perfect For

- **Finance/Econometrics courses** - Analyze real datasets
- **R/SQL programming help** - Get instant code assistance
- **Data analysis projects** - Navigate and understand your files
- **Research workflows** - Quick file exploration and analysis

## 🔧 Features

### File Operations
- **List files**: `list` - See directory contents
- **Read files**: `read filename.csv` - Preview file contents
- **Search files**: `search "keyword"` - Find files by content

### AI Assistant
- **R/SQL help**: Ask programming questions with context
- **File analysis**: Get insights about your data files
- **Code generation**: Generate R/SQL code snippets
- **Explanations**: Understand complex datasets and code

### Security & Safety
- **Sandboxed access**: Only reads files in your project directory
- **File size limits**: Prevents reading huge files (5MB max)
- **Path validation**: Blocks directory traversal attacks
- **Safe mode**: Additional security restrictions

## 🛠️ Command Line Options

```bash
vertikal [OPTIONS]

Options:
  --project-root PATH    Project directory (default: current)
  --safe-mode           Enable additional security restrictions
  --verbose             Show debug information
  --version             Show version information
  --help                Show help message
```

## 📁 RStudio Integration

### Method 1: Terminal Pane (Recommended)
1. Open RStudio
2. Go to **Tools → Terminal → New Terminal**
3. Navigate to your project: `cd /path/to/project`
4. Run: `vertikal --project-root .`
5. Start chatting with your files!

### Method 2: R Console
```r
# Install vertikal in R
system("pip install vertikal")

# Set API key
Sys.setenv(GROQ_API_KEY = "your_key_here")

# Open terminal
system("vertikal --project-root .")
```

## 🔒 Security Features

- **Project isolation**: Only accesses files within specified directory
- **Path validation**: Prevents `../` and absolute path attacks
- **File size limits**: 5MB maximum file size
- **Read-only access**: Cannot modify or delete files
- **Safe mode**: Additional restrictions for sensitive environments

## 🐛 Troubleshooting

### "Command not found: vertikal"
```bash
# Make sure vertikal is installed
pip install vertikal

# Check if it's in your PATH
which vertikal
```

### "GROQ_API_KEY not set"
```bash
# Set the environment variable
export GROQ_API_KEY="your_key_here"

# Or add to your shell profile
echo 'export GROQ_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### "File not found" errors
```bash
# Make sure you're in the right directory
pwd
ls -la

# Use absolute path if needed
vertikal --project-root /full/path/to/project
```

### Python version issues
```bash
# Check Python version (need 3.9+)
python --version

# Use python3 if needed
python3 -m pip install vertikal
```

## 📚 Examples

### Finance Course Example
```bash
vertikal:project> list
📁 Project files:
├── data/
│   ├── stock_prices.csv
│   └── economic_indicators.csv
├── scripts/
│   ├── analysis.R
│   └── visualization.R
└── README.md

vertikal:project> read data/stock_prices.csv
📄 File: data/stock_prices.csv
Content:
Date,Apple,Google,Microsoft
2024-01-01,150.25,2800.50,420.75
...

vertikal:project> How do I calculate daily returns in R?
🤖 To calculate daily returns in R, you can use:

# Method 1: Simple percentage returns
returns <- diff(prices) / prices[-length(prices)] * 100

# Method 2: Log returns (more common in finance)
log_returns <- diff(log(prices))

# Method 3: Using quantmod package
library(quantmod)
returns <- dailyReturn(prices)
```

### Data Analysis Example
```bash
vertikal:project> search "regression"
🔍 Found 3 files containing "regression":
- analysis.R (line 45): lm_model <- lm(y ~ x, data = df)
- report.md (line 12): Multiple regression analysis shows...
- notes.txt (line 8): TODO: Add regression diagnostics

vertikal:project> What does the regression analysis in analysis.R show?
🤖 Looking at your regression analysis in analysis.R:

The code performs a simple linear regression using lm():
- Dependent variable: y
- Independent variable: x
- Data source: df dataframe

Key points:
1. Uses standard R lm() function
2. Formula: y ~ x (linear relationship)
3. Results stored in lm_model object

You might want to add:
- summary(lm_model) to see coefficients
- plot() for diagnostic plots
- predict() for predictions
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/vertikal/issues)
- **Documentation**: [GitHub Wiki](https://github.com/yourusername/vertikal/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/vertikal/discussions)

## 🙏 Acknowledgments

- Built with [Groq](https://groq.com/) for lightning-fast AI responses
- Designed for RStudio and data science workflows
- Inspired by the need for file-aware terminal assistants

---

**Made with ❤️ for data scientists and R users**