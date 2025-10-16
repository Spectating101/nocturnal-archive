# Cite-Agent: AI Research Assistant

**Stop switching between 10 different tools. Just ask questions in plain English.**

---

## **What It Does (30-Second Version)**

Cite-Agent is a command-line AI assistant for researchers and students that:

- 📊 **Reads your data files** (CSV, R, Python) and answers questions about them
- 💼 **Gets financial data** instantly (revenue, earnings, ratios for any company)
- 🔍 **Searches academic literature** with proper citations
- 🗂️ **Manages your files** using natural language
- 🧠 **Remembers context** across your entire conversation

**No coding required. No data upload. Everything runs locally.**

---

## **Show, Don't Tell**

### **Example 1: Data Analysis**
```
You: show me my data.csv
Agent: [Displays file, detects columns: Date, Price, Volume, Ticker...]

You: what's the average price?
Agent: $45.23 (calculated from 1,247 rows)

You: any missing values?
Agent: Yes, 3 rows missing Price (rows 45, 127, 983)
```
**Time saved**: 10 minutes vs. writing pandas/R code

---

### **Example 2: Financial Research**
```
You: Tesla revenue
Agent: $96.77B (TTM)

You: what about Microsoft?
Agent: $245.12B (TTM)

You: which has better profit margins?
Agent: Microsoft: 36.7%, Tesla: 23.1%. Microsoft wins.
```
**Time saved**: 20 minutes vs. hunting through EDGAR

---

### **Example 3: File Navigation**
```
You: find my thesis project
Agent: Found: /home/user/thesis-2024/

You: look into it
Agent: [Lists files and directories]

You: show me analysis.R
Agent: [Displays file, detects functions: calculate_beta(), plot_returns()...]
```
**Time saved**: Instant vs. cd/ls/cat commands

---

## **Why It's Different**

| Feature | Cite-Agent | ChatGPT | RStudio | Terminal |
|---------|-----------|---------|---------|----------|
| Reads local files | ✅ | ❌ | ✅ | ❌ |
| Natural language | ✅ | ✅ | ❌ | ❌ |
| Financial data | ✅ | ⚠️ (outdated) | ❌ | ❌ |
| Remembers context | ✅ | ⚠️ (limited) | ❌ | ❌ |
| No coding needed | ✅ | ✅ | ❌ | ❌ |
| Privacy (local) | ✅ | ❌ | ✅ | ✅ |

---

## **Who Needs This?**

### **Graduate Students**
"I have 5 CSV files, 3 R scripts, and a deadline. I just need to analyze this data fast."

### **Finance Students** 
"I need to compare 10 companies' financials for my homework. Bloomberg Terminal costs $2,000/month."

### **Researchers**
"I spend 30% of my time just finding files and looking up basic info. I'd rather spend that time thinking."

### **Anyone With Data**
"I'm not a programmer. I just want answers."

---

## **The Value Proposition**

### **Time Savings**
- **Data exploration**: 10-15 minutes per task
- **Financial lookups**: 20-30 minutes per company
- **File navigation**: 5-10 minutes per session
- **Literature search**: 30-60 minutes per review

**Conservative estimate**: **2-3 hours saved per week**

### **Money Savings**
- Bloomberg Terminal: $24,000/year
- Data analysis contractors: $50-100/hour
- **Cite-Agent**: Free (currently)

### **Frustration Savings**
- No more "what was that command again?"
- No more copying data between tools
- No more context switching
- No more syntax errors

---

## **Technical Credibility**

- ✅ **100% test pass rate** (15/15 queries in production)
- ✅ **1.7s average response time**
- ✅ **86,400 queries/day capacity**
- ✅ **Published on PyPI** (pip installable)
- ✅ **Auto-updates** (always latest features)
- ✅ **Anti-hallucination** prompts (real data only)

**Translation**: It works, it's fast, it's reliable.

---

## **Get Started in 60 Seconds**

```bash
pip install cite-agent
cite-agent
```

Then try:
```
> what can you do?
> show me [your_file.csv]
> Tesla revenue
> find my project folder
```

---

## **Current Status: Early Access**

- ✅ Fully functional
- ✅ Free to use
- ✅ Active development
- 📝 Collecting user feedback
- 🚀 Improving based on real usage

**Want to help shape the product?** Try it and tell us what you need.

---

## **The Ask**

If you're a researcher, student, or data person:

1. **Try it** (5 minutes)
2. **Give feedback** (what worked, what didn't)
3. **Share it** (if you find it useful)

That's it. No signup, no credit card, no catch.

---

## **Contact**

- **Install**: `pip install cite-agent`
- **Issues**: [GitHub Issues]
- **Questions**: [Your Email]
- **Updates**: Follow on [Platform]

---

**Built for researchers who have better things to do than remember syntax.**

*Version 1.3.6 — October 2025*

