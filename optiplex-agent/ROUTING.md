# Smart Model Routing

Optiplex Agent automatically switches between Cerebras models based on task complexity, maximizing efficiency while staying within the 1M daily token limit.

## How It Works

The agent analyzes your request and routes to the optimal model:

| Complexity | Model | Size | Use Case |
|------------|-------|------|----------|
| **Simple** | llama-4-scout-17b | 17B | Quick questions, git status, file reads |
| **General** | llama-3.3-70b | 70B | Standard coding, explanations, reviews |
| **Coding** | qwen-3-32b | 32B | Writing functions, implementing features |
| **Heavy** | qwen-3-coder-480b | 480B | Refactoring, architecture, complex debugging |

## Detection Logic

### Simple Tasks
- Keywords: "explain", "what is", "how does", "show me", "list", "status"
- Short messages (< 10 words)
- Examples:
  - "what's the git status?"
  - "explain this function"
  - "list all files"

### General Tasks
- Default for most queries
- Medium-length messages
- Examples:
  - "review this code for improvements"
  - "help me understand the architecture"

### Coding Tasks
- Keywords: "implement", "write function", "create class", "build feature"
- Examples:
  - "implement a binary search function"
  - "write a REST API endpoint"
  - "create a user authentication system"

### Heavy Tasks
- Keywords: "refactor", "architect", "design", "optimize", "analyze"
- Large context (5+ files)
- Long conversations (20+ messages)
- Examples:
  - "refactor the entire authentication system"
  - "architect a microservices solution"
  - "optimize this codebase for performance"

## Usage

### Auto-Routing (Default)
```bash
# Automatically switches models
optiplex

You> what's the git status?
# Uses: llama-4-scout-17b (simple)

You> implement a user registration function
🔄 Switching to qwen-3-32b (Coding task)
# Uses: qwen-3-32b (coding)

You> refactor the entire API architecture with proper separation of concerns
🔄 Switching to qwen-3-coder-480b (Complex task detected)
# Uses: qwen-3-coder-480b (heavy)
```

### Manual Mode
```bash
# Disable auto-routing, stick to one model
optiplex --no-auto-route -m qwen-3-coder-480b
```

### Check Statistics
```
You> stats
📊 Routing Statistics:
Total requests: 15

Model usage:
  llama-4-scout-17b: 5
  llama-3.3-70b: 7
  qwen-3-32b: 2
  qwen-3-coder-480b: 1

Complexity distribution:
  simple: 5
  general: 7
  coding: 2
  heavy: 1
```

## Token Efficiency

With 1M daily tokens from Cerebras:

| Model | Avg Tokens/Request | Requests/Day |
|-------|-------------------|--------------|
| llama-4-scout-17b | 500 | 2000 |
| llama-3.3-70b | 2000 | 500 |
| qwen-3-32b | 3000 | 333 |
| qwen-3-coder-480b | 8000 | 125 |

**Smart routing allows ~600-800 mixed requests per day** vs ~125 if you always used the 480B model.

## Configuration

Customize routing behavior in Python:

```python
from optiplex import OptiplexAgent
from optiplex.router import AdaptiveAgent

agent = OptiplexAgent(".", model_name="llama-3.3-70b")
adaptive = AdaptiveAgent(agent, enable_routing=True)

# Customize tier models
adaptive.router.set_tier_model("heavy", "claude-3-5-sonnet")
adaptive.router.set_tier_model("coding", "qwen-3-coder-480b")

# Disable routing temporarily
adaptive.disable_auto_routing()

# Re-enable
adaptive.enable_auto_routing()

# View stats
stats = adaptive.get_routing_stats()
print(stats)
```

## Best Practices

1. **Let it auto-route** - The system is designed to optimize your token usage
2. **Monitor stats** - Use `stats` command to see routing patterns
3. **Override when needed** - Use `--no-auto-route` for consistent behavior testing
4. **Trust the 480B** - Heavy tasks benefit significantly from the large model

## Why This Matters

- **Cost Optimization**: Use expensive models only when necessary
- **Speed**: Smaller models respond faster for simple tasks
- **Token Conservation**: Maximize your 1M daily token budget
- **Quality**: Complex tasks get the power they need

Without routing: **125 complex sessions/day**
With routing: **600-800 mixed sessions/day**

🚀 3-6x more productivity within the same token budget!
