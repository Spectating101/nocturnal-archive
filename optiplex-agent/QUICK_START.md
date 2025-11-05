# Optiplex Agent: Quick Start Guide

## 30-Second Install

```bash
# Clone and install
cd optiplex-agent
pip install -e .

# Run
optiplex

# That's it!
```

---

## Your First Session

```bash
$ optiplex

🤖 Optiplex Agent (llama-3.3-70b)
📁 Working directory: /home/user/myproject
🔀 Auto-routing: ENABLED

You> help
```

---

## Common Tasks (Copy-Paste Ready)

### 1. Index Your Codebase (Do This First!)
```
You> index
```
**Result**: Fast search, context-aware suggestions

### 2. Fix All Imports
```
You> add missing imports to src/main.py
```
**Result**: Auto-detects and adds stdlib + project imports

### 3. Search Your Code
```
You> search for authentication functions
You> find all files importing flask
You> where is UserModel called?
```
**Result**: Instant indexed search results

### 4. Refactor Across Files
```
You> rename function get_user to fetch_user everywhere
```
**Result**: Multi-file edit with diff preview

### 5. Get Code Summary
```
You> summary
```
**Result**: Files, classes, functions count

### 6. Check Git Status
```
You> what's the git status?
```
**Result**: Shows changes, suggests commits

### 7. Commit Changes
```
You> commit these changes with message "fix auth bug"
```
**Result**: Stages and commits automatically

### 8. Deploy to Production
```
You> ssh to production and check logs
You> deploy latest changes to heroku
```
**Result**: Full DevOps automation

---

## CLI Flags (Advanced)

### Auto-Apply Mode (No Confirmations)
```bash
optiplex --auto-apply
```
**Use when**: You trust the agent completely

### Disable Interactive Diffs
```bash
optiplex --no-interactive
```
**Use when**: In CI/CD pipelines

### Disable Model Routing (Stick to One Model)
```bash
optiplex --no-auto-route -m qwen-3-coder-480b
```
**Use when**: You want consistent model behavior

### Single Command Mode
```bash
optiplex -c "fix all type errors"
```
**Use when**: Scripting or automation

---

## Special Commands

| Command | What It Does |
|---------|-------------|
| `index` | Index codebase (do this first!) |
| `summary` | Show codebase stats |
| `stats` | Show model usage stats |
| `reset` | Clear conversation history |
| `help` | Show all commands |
| `exit` | Quit |

---

## Advanced Features

### Tree-sitter (Optional, Better Parsing)
```bash
# Install tree-sitter
pip install tree-sitter

# Build languages (one-time, 2-5 minutes)
python scripts/build_tree_sitter.py

# Set path
export TREE_SITTER_LIB_PATH=./tree-sitter-libs

# Run
optiplex
```
**Benefit**: 95% parsing accuracy vs 70%

### Context Files (@-syntax)
```
You> @src/config.py explain this file
```
**Benefit**: Include specific files in context

---

## Cost Optimization

### Free Tier (Cerebras)
- **Default model**: llama-3.3-70b
- **Free quota**: 1M tokens/day
- **Cost**: $0

### Auto-Routing (Saves Tokens)
| Task Type | Model Used | Tokens Saved |
|-----------|------------|--------------|
| Simple | llama-4-scout-17b | 3x vs 70B |
| General | llama-3.3-70b | Baseline |
| Coding | qwen-3-32b | 2x faster |
| Heavy | qwen-3-coder-480b | Best quality |

**To disable**: `optiplex --no-auto-route`

---

## Troubleshooting

### "No module named optiplex"
```bash
pip install -e .
```

### "API key not found"
```bash
export CEREBRAS_API_KEY=your_key_here
```

### "Tree-sitter not available"
```bash
# Optional - works without it
pip install tree-sitter
python scripts/build_tree_sitter.py
```

### "Diff confirmation is annoying"
```bash
optiplex --auto-apply
```

---

## Performance Tips

1. **Always index first**: `You> index`
2. **Use specific queries**: "search for auth" > "search code"
3. **Include context files**: `@file.py` for better results
4. **Check stats**: `You> stats` to see model usage
5. **Reset when stuck**: `You> reset` clears history

---

## Example Workflows

### Workflow 1: Fix Bug
```
You> index
You> search for error handling in api
You> read src/api/errors.py
You> fix the authentication error in this file
You> git diff
You> commit with message "fix auth error handling"
```

### Workflow 2: Add Feature
```
You> create a new endpoint for user settings
You> add tests for the settings endpoint
You> add missing imports
You> run tests
You> commit if tests pass
```

### Workflow 3: Refactor
```
You> search for all uses of old_function
You> rename old_function to new_function everywhere
You> add missing imports
You> run tests
You> git diff
```

---

## What Makes Optiplex Different

| Feature | Optiplex | Cursor | Claude Code | Aider |
|---------|----------|--------|-------------|-------|
| **Cost** | $0/month | $20/month | ~$130/month | ~$130/month |
| **Shell access** | ✅ Full | ❌ | ❌ | ⚠️ Limited |
| **Codebase indexing** | ✅ Fast | ✅ | ✅ | ❌ |
| **Auto-import** | ✅ Python | ✅ All | ❌ | ❌ |
| **Multi-language AST** | ✅ Tree-sitter | ✅ LSP | ✅ LSP | ❌ |
| **Model flexibility** | ✅ 9 providers | ❌ | ❌ | ✅ |
| **IDE integration** | ❌ CLI only | ✅ | ❌ | ❌ |

---

## Quick Reference Card

```
# Setup
optiplex                    # Start agent
You> index                  # Index codebase
You> help                   # Show commands

# Code Operations
You> search for [query]     # Search code
You> read [file]            # Read file
You> edit [file]            # Edit file
You> add imports to [file]  # Fix imports

# Git Operations
You> git status             # Check status
You> git diff               # Show changes
You> commit [message]       # Commit changes

# Advanced
You> summary                # Codebase stats
You> stats                  # Model usage
You> @file.py [question]    # Include context

# Exit
You> exit                   # Quit
```

---

## Next Steps

1. **Read**: [COMPLETE.md](COMPLETE.md) - Full feature list
2. **Compare**: [BENCHMARK.md](BENCHMARK.md) - vs competitors
3. **Deep dive**: [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Tree-sitter + Auto-import
4. **Understand**: [ROUTING.md](ROUTING.md) - How model routing works

---

## TL;DR

**Install**: `pip install -e .`
**Run**: `optiplex`
**Index**: `You> index`
**Use**: Ask anything
**Cost**: $0 with Cerebras

🚀 **That's it. Start coding.**
