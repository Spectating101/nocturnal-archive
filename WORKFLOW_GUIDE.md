# Workflow Integration Guide
## Making Cite-Agent Your Daily Research Companion

Cite-Agent now includes powerful workflow features that **eliminate context switching** and integrate directly into your research workflow. Think of it as "Cursor for scholars" - always available, always helpful.

---

## 🎯 Key Features

### 1. **Local Paper Library** 📚
Keep a personal database of papers without switching to Zotero or Mendeley.

### 2. **BibTeX Export** 📄
Export directly to `.bib` files for LaTeX papers.

### 3. **Clipboard Integration** 📋
Copy citations directly to clipboard - paste into your document instantly.

### 4. **Session History** 🕒
Never lose a query - automatic tracking of all your searches.

### 5. **Markdown Export** 📝
Export to Obsidian, Notion, or any markdown-based system.

---

## 🚀 Quick Start Examples

### Basic Workflow: Research → Save → Export

```bash
# 1. Search for papers
cite-agent "Find papers on transformer architecture"

# 2. Search and save to library
cite-agent "Find papers on BERT" --save

# 3. Search and copy citation to clipboard
cite-agent "Cite BERT paper in APA" --format apa --copy

# 4. Export everything to BibTeX for your LaTeX paper
cite-agent --export-bibtex

# 5. Check what you've searched recently
cite-agent --history
```

---

## 📖 Complete Command Reference

### Library Management

#### View Your Library
```bash
# List all papers
cite-agent --library

# Filter by tag
cite-agent --library --tag "machine-learning"
```

#### Search Your Library
```bash
# Find papers by keyword
cite-agent --search-library "transformer"

# This searches titles, authors, and abstracts
```

### Citation Formats

#### Get Citations in Different Formats
```bash
# APA format
cite-agent "Cite the Attention Is All You Need paper" --format apa

# BibTeX format
cite-agent "Cite the BERT paper" --format bibtex

# Copy to clipboard automatically
cite-agent "Cite Transformer-XL" --format apa --copy
```

### Export Features

#### Export to BibTeX
```bash
# Export entire library
cite-agent --export-bibtex

# Output: ~/.cite_agent/exports/references.bib
# Import this file into Zotero, Mendeley, or use in LaTeX
```

#### Export to Markdown
```bash
# Export for Obsidian/Notion
cite-agent --export-markdown

# Output: ~/.cite_agent/exports/papers_YYYYMMDD_HHMMSS.md
```

### History & Tracking

#### View Query History
```bash
# See recent queries
cite-agent --history

# Shows:
# - Timestamp
# - Your question
# - Tools used (archive_api, finsight_api, etc.)
```

---

## 🎨 Real-World Workflows

### Workflow 1: **Writing a Literature Review**

```bash
# Day 1: Collect papers
cite-agent "Find papers on attention mechanisms in NLP" --save
cite-agent "Find papers on BERT and its variants" --save
cite-agent "Find papers on GPT architecture" --save

# Day 2: Export for writing
cite-agent --export-bibtex
# → Import references.bib into Overleaf

# Day 3: Need a specific citation?
cite-agent "Cite Attention Is All You Need in APA" --copy
# → Paste directly into Google Docs
```

### Workflow 2: **Statistical Analysis**

```bash
# Check if your results are significant
cite-agent "My sample size is 30, p=0.048, Cohen's d=0.3. Is this meaningful?"

# Get proper citation for statistical test
cite-agent "Cite Cohen 1992 power primer" --format apa --copy

# Check history later
cite-agent --history
```

### Workflow 3: **Financial Research**

```bash
# Get company data
cite-agent "What is Apple's revenue for 2024?" --copy

# Export for your report
cite-agent --export-markdown

# All queries auto-saved to history
cite-agent --history
```

### Workflow 4: **Daily Research Assistant**

```bash
# Morning: Quick fact-check
cite-agent "Is water's boiling point 100°C?" --copy

# Afternoon: Paper search
cite-agent "Latest papers on large language models" --save

# Evening: Export everything
cite-agent --export-bibtex
```

---

## 🔧 Advanced Features

### Custom Tags (Coming Soon)
```bash
# Tag papers for organization
cite-agent --tag "paper_id" "methodology,baseline"
```

### Notes on Papers (Coming Soon)
```bash
# Add notes to saved papers
cite-agent --add-note "paper_id" "Important for related work section"
```

### Integration with Writing Tools (Coming Soon)
```bash
# Direct Zotero sync
cite-agent --sync-zotero

# Obsidian plugin
cite-agent --export-obsidian
```

---

## 📁 File Locations

All your data is stored locally in `~/.cite_agent/`:

```
~/.cite_agent/
├── library/              # Your paper database (JSON files)
│   ├── paper_abc123.json
│   └── paper_def456.json
├── exports/              # Exported files
│   ├── references.bib    # BibTeX export
│   └── papers_*.md       # Markdown exports
└── history/              # Query history
    └── 20251013.jsonl    # Daily query logs
```

---

## 💡 Pro Tips

### 1. **Clipboard Workflow**
Always use `--copy` when you need to paste immediately:
```bash
cite-agent "Statistical significance of p=0.05" --copy
# → Cmd/Ctrl+V into your document
```

### 2. **History for Follow-ups**
Check history to remember what you searched:
```bash
cite-agent --history
# See what you searched yesterday
```

### 3. **BibTeX for LaTeX Papers**
Export once, reuse everywhere:
```bash
cite-agent --export-bibtex
# Add to your LaTeX project: \bibliography{~/.cite_agent/exports/references}
```

### 4. **Markdown for Note-Taking**
Perfect for Obsidian/Notion workflows:
```bash
cite-agent --export-markdown
# Import into Obsidian vault
```

### 5. **Combine Flags**
```bash
# Search + Save + Copy + Format
cite-agent "Find BERT paper" --save --format bibtex --copy
```

---

## 🆚 Comparison: Before vs. After

### Before (Without Workflow Integration):
1. Ask cite-agent for paper
2. Copy response to notepad
3. Open Google Scholar to verify
4. Copy citation manually
5. Open Zotero
6. Add paper manually
7. Export BibTeX from Zotero
8. Import to LaTeX

**Time: ~10 minutes per paper**

### After (With Workflow Integration):
```bash
cite-agent "Find BERT paper" --save --format bibtex --copy
cite-agent --export-bibtex
```
**Time: ~30 seconds**

---

## 🎓 Use Cases by Discipline

### Computer Science
```bash
# Find papers + export for conference
cite-agent "Papers on transformers 2023" --save
cite-agent --export-bibtex
```

### Economics / Business
```bash
# Get financial data + proper citations
cite-agent "Apple's Q3 2024 revenue" --copy
cite-agent "Cite SEC filing for AAPL" --format apa --copy
```

### Psychology / Social Sciences
```bash
# Statistical validation + citation
cite-agent "Is my t-test result significant?" --copy
cite-agent "Cite APA guidelines for t-tests" --format apa --copy
```

### Biology / Medicine
```bash
# PubMed search + save
cite-agent "Papers on CRISPR from Nature" --save
cite-agent --export-markdown
```

---

## 🔗 Integration Roadmap

Future integrations being developed:

- [ ] **Zotero Plugin** - Direct sync with your Zotero library
- [ ] **Overleaf Extension** - Insert citations directly in browser
- [ ] **VS Code Extension** - Cite while writing markdown
- [ ] **Obsidian Plugin** - Smart citation suggestions
- [ ] **Notion Integration** - Export with proper formatting
- [ ] **Google Docs Add-on** - One-click citation insertion

---

## ❓ FAQ

**Q: Where is my data stored?**  
A: Locally in `~/.cite_agent/`. Completely private, no cloud sync.

**Q: Can I use this offline?**  
A: History, library, and exports work offline. Queries need internet.

**Q: Does it work with my citation manager?**  
A: Yes! Export to BibTeX and import into Zotero, Mendeley, EndNote, etc.

**Q: Can I edit saved papers?**  
A: Yes! Papers are stored as JSON in `~/.cite_agent/library/`. Edit directly or use CLI (coming soon).

**Q: Is clipboard integration secure?**  
A: Yes. It only copies what you explicitly request with `--copy`.

---

## 🆘 Troubleshooting

### Clipboard not working?
Install clipboard utility:
```bash
# Linux
sudo apt-get install xclip  # or xsel, or wl-clipboard for Wayland

# macOS
# Built-in, should work automatically

# Windows
# Built-in, should work automatically
```

### Can't find exported files?
```bash
# Check the directory
ls ~/.cite_agent/exports/

# BibTeX file location
cat ~/.cite_agent/exports/references.bib
```

### History not showing?
Queries are only saved when using the new workflow features. Run a query first:
```bash
cite-agent "test query" --copy
cite-agent --history
```

---

## 🎯 Bottom Line

**Cite-Agent with workflow integration eliminates context switching:**

✅ No more switching to Google Scholar  
✅ No more manual copy-paste to Zotero  
✅ No more hunting for citations in old browser tabs  
✅ No more re-running queries you already did  

**Just:** `cite-agent "question" --save --copy --format bibtex`

**Result:** Paper found, saved to library, citation on clipboard, exported to BibTeX, all tracked in history.

**That's the "Cursor for scholars" experience.**

---

## 📞 Get Help

- **Docs**: Read `USER_GUIDE.md` for basics
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord for tips and tricks

---

*Happy researching! 🔬📚*



