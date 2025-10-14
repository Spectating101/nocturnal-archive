# 🔧 Installation Fix - "command not found"

## ✅ **Package Installed Successfully**

You see:
```
Successfully installed cite-agent-1.2.6
```

But get:
```bash
cite-agent
bash: cite-agent: command not found
```

---

## 🛠️ **Fix (Choose One):**

### **Option 1: Add to PATH (Permanent Fix)**
```bash
# Add ~/.local/bin to your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Now it works:
cite-agent --version
```

### **Option 2: Use Full Path (Quick Test)**
```bash
~/.local/bin/cite-agent --version
~/.local/bin/cite-agent "Find papers on AI"
```

### **Option 3: Python Module (Alternative)**
```bash
python3 -m cite_agent.cli --version
python3 -m cite_agent.cli "Find papers on AI"
```

---

## ✅ **Recommended: Option 1**

**Run this:**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
cite-agent --version
```

**Should show:**
```
Cite Agent v1.2.6
AI Research Assistant with real data integration
```

---

## 🚀 **Then Test:**

```bash
cite-agent "Find papers on quantum computing"
cite-agent "Apple latest revenue"
cite-agent "Bitcoin price today"
```

---

**This is a common Python pip install issue on Debian/Ubuntu.**  
**Nothing wrong with cite-agent - just PATH configuration.**

