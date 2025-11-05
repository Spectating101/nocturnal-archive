# Autonomous Mode - Optiplex Works Independently

## What is Autonomous Mode?

Autonomous mode allows Optiplex to work **independently** without human intervention. Instead of waiting for prompts, it:

1. **Reads tasks from a file** (`tasks.json`)
2. **Executes them sequentially**
3. **Self-reflects** to find more work when tasks are done
4. **Logs all actions** for transparency
5. **Saves results** back to the task file

This is how you make Optiplex work like an **employee**, not a chatbot.

---

## Usage

### 1. Autonomous Mode (Task-Based)

Create a `tasks.json` file in your project:

```json
{
  "tasks": [
    {
      "id": "task_1",
      "description": "Add type hints to all functions in src/utils.py",
      "status": "pending"
    },
    {
      "id": "task_2",
      "description": "Write unit tests for the UserManager class",
      "status": "pending"
    },
    {
      "id": "task_3",
      "description": "Refactor the database connection code to use connection pooling",
      "status": "pending"
    }
  ]
}
```

Then run:

```bash
optiplex --autonomous --max-iterations 100
```

**What happens:**
- Optiplex reads `tasks.json`
- Executes each pending task
- Updates task status (`completed`, `failed`)
- When done, it **self-reflects** on the codebase and suggests new tasks
- Creates new tasks automatically (e.g., "Fix linting errors", "Update tests")
- Continues until no work remains or max iterations reached

---

### 2. Watch Mode (Event-Driven)

Have Optiplex watch for file changes and auto-fix issues:

```bash
optiplex --watch
```

**What happens:**
- Monitors all `.py`, `.md`, `.json` files for changes
- When a file is modified, creates a task to analyze it
- Automatically fixes issues (linting, tests, docs)
- Runs continuously in the background

**Use case:** Save a file with a bug → Optiplex detects it → Analyzes → Fixes → Commits

---

## Self-Reflection

When tasks are done, Optiplex **self-reflects**:

```
1. Check git status for uncommitted changes
2. Look for TODO comments in the code
3. Check for linting errors or test failures
4. Suggest the most important task to work on next
```

If it finds work, it creates a new task and executes it. This makes Optiplex **proactive**.

---

## Examples

### Example 1: Weekend Maintenance

**Friday 5pm:**
```json
{
  "tasks": [
    {"id": "1", "description": "Refactor auth module for better performance", "status": "pending"},
    {"id": "2", "description": "Add comprehensive tests to payment module", "status": "pending"},
    {"id": "3", "description": "Update all dependencies to latest versions", "status": "pending"},
    {"id": "4", "description": "Generate API documentation", "status": "pending"}
  ]
}
```

```bash
nohup optiplex --autonomous --max-iterations 200 > weekend.log 2>&1 &
```

**Monday 9am:** Check `tasks.json` - all tasks completed, plus it found and fixed 3 TODO items.

---

### Example 2: Continuous CI/CD Agent

```bash
# In your deploy script
optiplex --watch --auto-apply &
```

Now Optiplex runs in the background:
- Someone pushes code → Optiplex detects changes
- Runs linting → Fixes issues → Commits fixes
- Updates tests → Verifies → Reports

---

### Example 3: Large Refactoring

```json
{
  "tasks": [
    {"id": "1", "description": "Analyze the entire codebase and create a refactoring plan for the authentication system", "status": "pending"},
    {"id": "2", "description": "Execute step 1 of the refactoring plan", "status": "pending"},
    {"id": "3", "description": "Execute step 2 of the refactoring plan", "status": "pending"}
  ]
}
```

Optiplex will:
1. Read all auth-related files
2. Create a detailed plan (10-20 steps)
3. Execute each step
4. Verify after each step
5. Self-correct if tests fail

---

## Comparison to Cursor

| Feature | Cursor | Optiplex Autonomous |
|---------|--------|---------------------|
| **Interaction** | Manual prompts | Reads tasks, works independently |
| **Scope** | Single file/task | Entire project, multi-step plans |
| **Duration** | Short sessions | Long-running (hours/days) |
| **Proactivity** | Zero | Self-reflects, finds new work |
| **Unattended** | No | **Yes** - run overnight/weekend |
| **Cost** | $20/month | **FREE** |

**This is the killer feature.** Cursor can't do this - it requires human interaction for every task.

---

## Configuration

### Task File Format

```json
{
  "tasks": [
    {
      "id": "unique_id",              // Required
      "description": "What to do",     // Required
      "status": "pending",             // pending|completed|failed
      "priority": 1,                   // Optional (not yet used)
      "dependencies": ["task_1"],      // Optional (not yet used)
      "created_at": "2025-01-01T12:00:00",
      "completed_at": "2025-01-01T14:30:00",  // Set automatically
      "result": "Success! Added type hints to 12 functions", // Set automatically
      "error": "Failed to parse file" // Set if task fails
    }
  ]
}
```

### Autonomous Log

All actions are logged to `autonomous.log`:

```
[2025-10-12 20:00:00] [INFO] 🚀 Starting autonomous mode
[2025-10-12 20:00:01] [INFO] Starting task task_1: Add type hints to src/utils.py
[2025-10-12 20:00:15] [SUCCESS] ✅ Task task_1 completed
[2025-10-12 20:00:15] [INFO] Result: Successfully added type hints to 12 functions...
[2025-10-12 20:00:16] [INFO] No pending tasks. Running self-reflection...
[2025-10-12 20:00:20] [INFO] Self-reflection suggests: Fix 3 linting errors in tests/
[2025-10-12 20:00:20] [INFO] Starting task auto_2: Fix 3 linting errors in tests/
```

---

## Best Practices

1. **Start small**: Test with 2-3 simple tasks first
2. **Use max-iterations**: Set `--max-iterations 20` to avoid runaway loops
3. **Monitor logs**: Check `autonomous.log` to see what it's doing
4. **Review changes**: Check git diff before deploying
5. **Incremental tasks**: Break large tasks into smaller steps

---

## Safety

- All file changes are backed up automatically
- Failed tasks are marked and skipped
- Max iterations prevents infinite loops
- Logs are detailed for debugging
- You can stop anytime with Ctrl+C

---

## Future Enhancements

- [ ] GitHub integration (read issues, create PRs)
- [ ] Slack notifications when tasks complete
- [ ] Priority-based task scheduling
- [ ] Dependency-aware task execution
- [ ] Rollback on test failures
- [ ] Cost tracking per task

---

## TL;DR

**Instead of this (Cursor):**
```
You: "Add type hints"
Cursor: [adds type hints]
You: "Now write tests"
Cursor: [writes tests]
You: "Now fix that bug"
...repeat 50 times...
```

**Do this (Optiplex Autonomous):**
```
Create tasks.json with 50 tasks
Run: optiplex --autonomous
Go to bed
Wake up: All done
```

**That's the difference.**


