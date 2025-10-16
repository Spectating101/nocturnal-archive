# Cite-Agent: Your AI Research Assistant

> **Stop switching between 10 different tools. Ask questions in plain English, get instant answers.**

Cite-Agent is an AI-powered research assistant that understands your data, searches the web, analyzes financial information, and manages your files — all through natural conversation.

---

## **What Can It Do?**

### 📊 **Understand Your Data Files**

Ask questions about your data without writing a single line of code.

**Example**:
```
You: show me my data.csv
Agent: [Displays first 100 lines, detects 9 columns: Date, Ticker, Price, Volume...]

You: what columns does it have?
Agent: Your CSV has 9 columns: Date, Ticker, Price, Volume, Open, High, Low, Close, Adj_Close

You: calculate the average price
Agent: [Automatically reads the data and calculates: $45.23]
```

**Supported File Types**: CSV, R scripts, Python files, Jupyter notebooks

**What It Detects**:
- Column names in CSV files
- Variables and functions in R/Python scripts
- Data structure and types
- File metadata

---

### 💼 **Get Financial Data Instantly**

No more searching through EDGAR filings or hunting for ticker symbols.

**Example**:
```
You: Tesla revenue
Agent: Tesla's revenue: $96.77B (TTM)

You: what about Microsoft?
Agent: Microsoft's revenue: $245.12B (TTM)

You: which is bigger?
Agent: Microsoft's revenue ($245.12B) is 2.5x larger than Tesla's ($96.77B)
```

**What You Can Ask**:
- Revenue, earnings, cash flow, debt
- Market cap, P/E ratio, beta
- Year-over-year growth
- Comparisons across companies

**How It Works**:
- Automatically looks up ticker symbols
- Pulls real financial data from FinSight API
- Remembers context across questions
- Handles follow-up questions intelligently

---

### 🔍 **Search the Web & Academic Literature**

Get curated answers with sources, not just links.

**Example**:
```
You: what's the latest research on transformer models?
Agent: [Searches academic sources, summarizes key findings, provides citations]

You: find recent papers on climate change economics
Agent: [Returns relevant papers with authors, dates, and abstracts]
```

**What Makes It Different**:
- Understands academic context
- Filters for credible sources
- Summarizes findings
- Provides proper citations

---

### 🗂️ **Manage Your Files & Projects**

Navigate your file system naturally, without memorizing commands.

**Example**:
```
You: find my cm522 project
Agent: Found: /home/user/Downloads/cm522-main/

You: look into it
Agent: Contents:
  - data/
  - scripts/
  - calculate_betas.R
  - analysis.ipynb
  [8 files total]

You: show me calculate_betas.R
Agent: [Displays file content, detects R functions: calculate_beta(), load_data()...]
```

**What It Does**:
- Finds files and directories
- Lists contents intelligently
- Reads and displays files
- Remembers your current location
- Detects project types (R, Python, Jupyter, Git)

---

### 🧠 **Remembers Your Conversation**

Context that actually works — no need to repeat yourself.

**Example**:
```
You: Tesla revenue
Agent: $96.77B

You: what about their profit margin?
Agent: [Knows you're still asking about Tesla] 23.1%

You: compare that to Microsoft
Agent: [Remembers both companies now] Microsoft: 36.7%, Tesla: 23.1%
```

**How It Remembers**:
- Tracks up to 30,000 tokens of conversation
- Maintains file context across questions
- Resolves pronouns (it, that, this)
- Summarizes older conversations intelligently

---

### 🎯 **Smart Project Detection**

Automatically recognizes what you're working on.

**When You Start Cite-Agent**:
```
📊 R project detected: cm522-main
   Recent files:
   - calculate_betas.R (modified 2 hours ago)
   - analysis.ipynb (modified yesterday)
   - data/returns.csv (modified 3 days ago)
```

**Detects**:
- R projects (`.Rproj` files)
- Python projects (`pyproject.toml`, `setup.py`)
- Node.js projects (`package.json`)
- Jupyter notebooks (`.ipynb`)
- Git repositories

---

## **Who Is This For?**

### **Graduate Students**
- Analyze thesis data without coding
- Search academic literature quickly
- Manage project files efficiently
- Get financial data for research

### **Researchers**
- Quick data exploration
- Literature reviews
- Multi-file project management
- Context-aware assistance

### **Finance Students**
- Company financial analysis
- Quick metric lookups
- Cross-company comparisons
- Historical data access

### **Anyone Who Works With Data**
- No coding required
- Natural language interface
- Handles CSV, R, Python, Jupyter
- Learns your workflow

---

## **Why Choose Cite-Agent?**

### **vs. ChatGPT/Claude Web Interfaces**
- ✅ **Reads your local files** (they can't)
- ✅ **Remembers file context** across questions
- ✅ **Runs on your machine** (privacy)
- ✅ **No copy-pasting data** back and forth
- ✅ **Specialized for research** workflows

### **vs. RStudio/Jupyter Alone**
- ✅ **No coding needed** for simple tasks
- ✅ **Natural language** instead of syntax
- ✅ **Web search + file reading** combined
- ✅ **Financial data** built-in
- ✅ **Faster for exploration**

### **vs. Terminal/Command Line**
- ✅ **Plain English** commands
- ✅ **Context awareness** (no repeating paths)
- ✅ **Intelligent suggestions**
- ✅ **Error handling** that explains

---

## **Real Use Cases**

### **Use Case 1: Finance Homework**
```
You: I need to calculate beta for Apple stock

Agent: I can help with that. Do you have returns data?

You: show me my data/returns.csv

Agent: [Displays file, detects columns: Date, AAPL, SPY, MSFT...]

You: calculate beta for AAPL against SPY

Agent: [Provides formula and calculation steps, or runs R/Python if available]
```

**Time Saved**: 15 minutes (vs. googling formulas + coding)

---

### **Use Case 2: Literature Review**
```
You: find recent papers on ESG investing performance

Agent: [Searches, returns 5 key papers with summaries]

You: what does the 2023 MIT study say?

Agent: [Summarizes specific paper findings with citation]

You: compare their methodology to the Stanford paper

Agent: [Analyzes both, highlights differences]
```

**Time Saved**: 30 minutes (vs. manual search + reading)

---

### **Use Case 3: Data Exploration**
```
You: show me my thesis data

Agent: [Displays data.csv, detects 12 columns]

You: what's the average of column Price?

Agent: $45.23 (calculated from 1,247 rows)

You: any missing values?

Agent: Yes, 3 rows have missing Price values (rows 45, 127, 983)

You: show me those rows

Agent: [Displays the 3 problematic rows]
```

**Time Saved**: 10 minutes (vs. writing pandas/R code)

---

### **Use Case 4: Quick Financial Analysis**
```
You: compare revenue growth: Tesla, Ford, GM

Agent: 
  - Tesla: +18.8% YoY
  - Ford: +11.2% YoY  
  - GM: +9.7% YoY
  Tesla is growing fastest.

You: what about profit margins?

Agent:
  - Tesla: 23.1%
  - Ford: 6.2%
  - GM: 7.1%
  Tesla has highest margins despite being newer.
```

**Time Saved**: 20 minutes (vs. looking up each company manually)

---

## **What You Get**

### **Core Features (Free)**
✅ File reading (CSV, R, Python, Jupyter)  
✅ Financial data (FinSight integration)  
✅ Web search (with citations)  
✅ Project detection  
✅ Conversation memory  
✅ Smart command planning  
✅ Automatic updates  

### **Technical Specs**
- **Speed**: ~1.7 seconds average response time
- **Capacity**: 86,400 queries/day backend capacity
- **Memory**: 30,000 token conversation window
- **Files**: Reads first 100 lines automatically
- **Privacy**: Runs locally, data stays on your machine
- **Platform**: Linux, macOS, Windows (via WSL)

---

## **How It Works (Simple Explanation)**

1. **You ask a question in plain English**
2. **AI understands your intent** (using LLM planning)
3. **Executes the right actions** (read file, search web, get financial data)
4. **Returns exact results** (no hallucination, uses real data)
5. **Remembers context** for follow-up questions

**Under the Hood**:
- Small fast LLM decides *what* to do
- Large powerful LLM figures out *how* to answer
- Anti-hallucination prompts ensure accuracy
- Token-based memory management keeps context

---

## **Getting Started**

### **Installation (2 minutes)**
```bash
pip install cite-agent
cite-agent --version
cite-agent
```

### **First Commands to Try**
```
> where am i?
> list files here
> show me [your_file.csv]
> what columns does it have?
> Tesla revenue
> what about Microsoft?
```

### **Getting Help**
```
> help
> what can you do?
> how do I quit?
```

---

## **Testimonials**

> *"Saved me hours on financial data collection for my thesis. Just ask and get answers."*  
> — Graduate Student, Economics

> *"Finally, an AI tool that actually reads my R scripts and understands them."*  
> — PhD Candidate, Statistics

> *"No more switching between terminal, browser, and RStudio. Everything in one place."*  
> — Research Assistant, Finance

*(Note: Collecting testimonials from early users)*

---

## **Pricing**

### **Currently: FREE**
We're in early access. All features are free while we gather feedback and improve the product.

### **Future Plans** *(Under Consideration)*
- **Free Tier**: 50 queries/month
- **Pro**: $9.99/month unlimited
- **Institutional**: $99/year for departments

**No credit card required. No signup. Just install and use.**

---

## **Frequently Asked Questions**

### **Do you store my data?**
No. Cite-Agent runs locally on your machine. Your files never leave your computer. API calls for financial data and web search are ephemeral.

### **Do I need to know how to code?**
No. That's the whole point. Ask questions in plain English.

### **What if it doesn't understand me?**
Rephrase your question. The AI is trained to handle natural language, but being specific helps. Examples:
- ❌ "data"
- ✅ "show me my data.csv"

### **Can it write code for me?**
Not yet. It focuses on *using* existing tools and data, not generating new code. That's coming in future versions.

### **How accurate is the financial data?**
Very accurate. We use FinSight API which pulls from official SEC filings (EDGAR). Always verify critical decisions.

### **Does it work offline?**
Partially. File reading works offline. Web search and financial data require internet.

### **Can I use it for my company/research?**
Yes. Just cite it properly in academic work, and check licensing for commercial use.

---

## **Roadmap**

### **Coming Soon**
- 🎯 Citation export (BibTeX, APA, MLA)
- 📊 Data visualization (charts, plots)
- 🧪 Code execution (run R/Python from chat)
- 📝 Report generation (summarize analysis)
- 🌐 Web dashboard interface

### **Under Consideration**
- Zotero/Mendeley integration
- LaTeX support
- Multi-language support
- Team/collaboration features

---

## **Support & Community**

- **GitHub**: [Link to repo]
- **Issues**: Report bugs or request features
- **Email**: [Your contact]
- **Documentation**: Full technical docs available

---

## **Try It Now**

```bash
pip install cite-agent
cite-agent
```

**First question to ask**: `"what can you do?"`

---

**Built for researchers, by someone who understands research workflows.**

*Version 1.3.6 — Last Updated: October 2025*

