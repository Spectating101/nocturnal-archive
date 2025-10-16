# Personal Code Agent

**Your unlimited AI coding assistant powered by Cerebras (free tier)**

Stop running out of Cursor/Copilot/Claude tokens. Use this instead.

---

## Why?

- ✅ **Unlimited tokens** - Cerebras gives you 14.4k requests/day × 3 keys = 43.2k/day
- ✅ **Fast responses** - Cerebras is 10x faster than Cursor's backend
- ✅ **Free** - $0 cost on free tier
- ✅ **No rate limits** - Use 100-300 requests/day easily
- ✅ **CLI-first** - Faster than switching to a GUI

## Quick Start

### 1. Install
```bash
cd code-agent
pip install requests

# Make it executable
chmod +x code_agent.py

# Optional: Add to PATH
ln -s $(pwd)/code_agent.py ~/.local/bin/code-agent
```

### 2. Use

```bash
# Basic usage (includes project context)
code-agent "fix the bug in main.py"

# Fast mode (no context)
code-agent --no-context "what's wrong with this function?"

# Check git status
code-agent --status

# Example prompts
code-agent "add error handling to api.py"
code-agent "optimize the database query"
code-agent "refactor this function to be more readable"
code-agent "write unit tests for the auth module"
```

### 3. Examples

```bash
# Fix a bug
$ code-agent "the login function is failing, fix it"
🤖 Code Agent: Processing your request...
📂 Gathering project context...
✅ Loaded 8 files for context
💭 Thinking...
============================================================
I found the issue in auth.py, line 45. You're not handling
the case where the user doesn't exist.

# In file: auth.py, line 45
- user = db.query(User).filter(User.email == email).first()
+ user = db.query(User).filter(User.email == email).first()
+ if not user:
+     raise HTTPException(status_code=404, detail="User not found")
============================================================

# Add a feature
$ code-agent "add caching to the API endpoint"
[... suggests Redis caching implementation ...]

# Optimize code
$ code-agent "make this function faster"
[... suggests algorithmic improvements ...]
```

---

## How It Works

1. **Gathers context** - Reads your project files (Python, JS, etc.)
2. **Sends to Cerebras** - Uses Llama 3.3 70B model (free tier)
3. **Gets response** - AI analyzes and suggests changes
4. **Shows diff** - You apply changes manually (or auto in v2)

**Context management:**
- Only reads recently modified files
- Prioritizes small files (<10KB)
- Max 50KB total context
- Skips `.git`, `node_modules`, `venv`, etc.

---

## Configuration

### API Keys

By default, uses the 3 Cerebras keys from cite-agent. To use your own:

```bash
export CEREBRAS_API_KEY_1="your-key-1"
export CEREBRAS_API_KEY_2="your-key-2"
export CEREBRAS_API_KEY_3="your-key-3"
```

### Project Root

By default, uses current directory. To specify:

```python
from code_agent import CodeAgent

agent = CodeAgent(project_root="/path/to/project")
agent.chat("your prompt")
```

---

## Advanced Usage

### Python API

```python
from code_agent import CodeAgent

# Initialize
agent = CodeAgent()

# Chat with context
response = agent.chat("fix the bug")

# Chat without context (faster)
response = agent.chat("explain this", with_context=False)

# Get git status
status = agent.git_status()
diff = agent.git_diff()
```

### Custom Prompts

```bash
# Architecture questions
code-agent "explain the architecture of this project"

# Best practices
code-agent "review this code for security issues"

# Documentation
code-agent "write docstrings for all functions"

# Testing
code-agent "write pytest tests for the API"
```

---

## Comparison to Cursor/Copilot

| Feature | Code Agent | Cursor | Copilot | Claude Code |
|---------|-----------|--------|---------|-------------|
| **Cost** | $0 | $20/month | $10/month | $0 (beta) |
| **Token limit** | 43,200/day | ~500/day | ~300/day | ~1000/day |
| **Speed** | 2-3 sec | 5-10 sec | 3-5 sec | 5-10 sec |
| **Model** | Llama 3.3 70B | Claude 3.5 | GPT-4 | Sonnet 4 |
| **Context** | 50KB | 200KB | 100KB | Unlimited |
| **IDE integration** | CLI only | Native | Native | VS Code |
| **Best for** | Power users | Everyone | Autocomplete | Research |

**When to use Code Agent:**
- ✅ You hit token limits on other tools
- ✅ You prefer CLI over GUI
- ✅ You want unlimited usage
- ✅ You need fast responses

**When to use Cursor/Copilot:**
- ❌ You need deep IDE integration
- ❌ You want autocomplete (not just chat)
- ❌ You prefer GUI over CLI

---

## Roadmap

### v1.0 (Current) ✅
- [x] Basic chat with context
- [x] Multi-file context gathering
- [x] Cerebras API integration
- [x] Git status/diff
- [x] CLI interface

### v1.1 (Next Week)
- [ ] Automatic diff application
- [ ] Streaming responses (see changes in real-time)
- [ ] Better context selection (AST-based)
- [ ] Support more languages (JS, Go, Rust)

### v1.2 (Future)
- [ ] Git integration (auto-commit)
- [ ] VS Code extension
- [ ] Multi-turn conversations
- [ ] Code review mode

---

## Tips & Tricks

### 1. Use specific prompts
```bash
# Bad
code-agent "fix this"

# Good
code-agent "fix the authentication bug in auth.py line 45"
```

### 2. Include file names
```bash
code-agent "add error handling to api/routes.py"
```

### 3. Use --no-context for quick questions
```bash
code-agent --no-context "what does this error mean?"
```

### 4. Check status before asking
```bash
code-agent --status
code-agent "fix the changes shown in git diff"
```

### 5. Chain prompts
```bash
code-agent "add a new feature X"
# Apply changes manually
code-agent "now add tests for feature X"
# Apply tests
code-agent "optimize the performance"
```

---

## Troubleshooting

### "All API keys exhausted"
**Cause:** Hit rate limits on all 3 keys

**Solution:** Wait 1 minute (Cerebras resets every 60 seconds)

### "Failed to get response from API"
**Cause:** Network issue or invalid API key

**Solution:**
1. Check internet connection
2. Verify API keys: `echo $CEREBRAS_API_KEY_1`
3. Try again

### Context is too large
**Cause:** Too many files in project

**Solution:** Use `--no-context` or reduce max_files in code

### Response is not helpful
**Cause:** Not enough context or vague prompt

**Solution:**
1. Be more specific in prompt
2. Include file names and line numbers
3. Use `code-agent --status` to show what changed

---

## FAQ

**Q: Is this free forever?**
A: Cerebras free tier is currently 14.4k RPD. If they change it, you may need to pay (~$0.001 per request).

**Q: Can I use this for work projects?**
A: Yes, but check your company's AI policy first.

**Q: Does it work offline?**
A: No, requires internet to call Cerebras API.

**Q: Can I use GPT-4 or Claude instead?**
A: Yes, modify `call_cerebras()` to use OpenAI/Anthropic API. But you'll pay per token.

**Q: How is this different from Claude Code?**
A: Claude Code is VS Code extension, this is CLI. Claude Code has unlimited context, this has 50KB limit. But this is free with 43k requests/day.

---

## Contributing

This is a personal tool, but feel free to fork and customize!

**Ideas for improvements:**
- Add support for more languages
- Better context selection (use AST parsing)
- Automatic diff application (use git apply)
- VS Code extension
- Web UI (for non-CLI users)

---

## License

MIT - Do whatever you want

---

**Built by:** You, for you
**Powered by:** Cerebras Llama 3.3 70B
**Cost:** $0/month (free tier)
**Token limit:** 43,200 requests/day (vs Cursor's 500/day)

**Stop running out of tokens. Start coding unlimited.** 🚀
