# 🚀 Getting Started with Cite-Agent

**Cite-Agent** is your AI research assistant - like ChatGPT but with real academic papers, financial data, and web search built in.

---

## 💬 What It Does

**Have a conversation** and get real data:

```
You: Find papers on transformers
Agent: [Shows 3 papers with real DOIs]

You: What is Tesla's revenue?
Agent: $22.5 billion from SEC filing (with link)

You: Bitcoin price today
Agent: $111,762 from CoinMarketCap

You: Snowflake market share
Agent: 18.33% in cloud data warehouses

You: quit
```

**No more copy-pasting between ChatGPT, Google Scholar, Yahoo Finance, and your terminal.**

---

## 📥 Installation

### **Linux (Ubuntu/Debian/Fedora):**
```bash
pip install cite-agent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
cite-agent
```

### **macOS:**
```bash
pip3 install cite-agent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
cite-agent
```

### **Windows:**
```bash
pip install cite-agent
python -m cite_agent
```

### **If "command not found":**
```bash
# Just use this instead:
python3 -m cite_agent
```

---

## 🎯 First Time Setup

**When you run it first time:**

```bash
cite-agent

# It will ask for:
Email: your-email@university.edu
Password: [create one]

# Then you're in!
```

---

## 💡 What You Can Ask

### **Academic Research:**
```
Find papers on neural networks
What papers cite GPT-3?
Search for quantum computing research from 2023
```

### **Financial Data:**
```
Apple latest revenue
Tesla vs Ford comparison
Microsoft market cap
```

### **Market Intelligence:**
```
Snowflake market share
AI chip industry size
OpenAI revenue
```

### **Current Data:**
```
Bitcoin price
Ethereum price today
Dollar to Euro exchange rate
```

### **Data Analysis (Advanced):**
```
Load my_data.csv and calculate mean
Run regression on beta values
Analyze interview themes
```

---

## 🎓 For Researchers

### **Citation Management:**
```
You: Find papers on reinforcement learning
Agent: [Shows 3 papers]

You: Save these to my library
Agent: ✅ Saved 3 papers

You: Export to BibTeX
Agent: [Provides BibTeX format]

You: Copy to clipboard
Agent: ✅ Copied
```

### **Data Analysis:**
```
You: I have stock return data in returns.csv
Agent: I can help analyze it. What would you like to know?

You: Calculate Fama-French 3-factor model
Agent: [Executes R code, shows results]
```

---

## 🔧 Common Issues

### **"Command not found"**
**Solution**: Use `python3 -m cite_agent` instead of `cite-agent`

### **"Not authenticated"**
**Solution**: Run `cite-agent --setup` first

### **Slow responses**
**Normal**: First query takes ~5-10 seconds (loading models)

---

## 💰 Pricing

**Beta**: Free with 25,000 tokens/day (~20 queries)  
**After Beta**: TBD

---

## 📧 Support

**Issues?** Report bugs or request features at your repo

**Questions?** Check the docs or ask the agent itself:
```
You: How do I save papers?
Agent: [Explains the workflow]
```

---

## 🎯 Pro Tips

1. **Be specific**: "Find papers on BERT transformers" > "Find papers on AI"
2. **It remembers**: Continues conversation context
3. **Use commands**: `save`, `export`, `library` for workflow features
4. **Dev mode**: Set `CITE_AGENT_DEV_MODE=true` for R/Python execution

---

**That's it! Start chatting and it'll figure out what you need.** 🚀

