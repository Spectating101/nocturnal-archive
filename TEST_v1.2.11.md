# Test Guide - v1.2.11

**When you're ready to test, follow this guide.**

---

## Installation

```bash
# Uninstall old version
pipx uninstall cite-agent

# Install v1.2.11
pipx install ~/Downloads/llm_automation/project_portfolio/Cite-Agent/dist/cite_agent-1.2.11-py3-none-any.whl

# Verify version
cite-agent --version
# Should show: Cite Agent v1.2.11
```

---

## Test 1: Conversation Memory (CRITICAL FIX)

```bash
cite-agent
```

**Conversation:**
```
You: where am i?
Agent: [Shows directory: /home/phyrexian/...]

You: what files are here?
Agent: [Lists files]

You: show me the third file
Agent: [Should remember which file was third from previous message]
```

**Expected**: Agent remembers context ✅  
**Before**: Agent forgot (said "what third file?") ❌

---

## Test 2: Directory Search (NEW FEATURE)

**Conversation:**
```
You: i'm looking for a directory called cm522 or something, it's in downloads
Agent: [Executes: find ~/Downloads -iname '*cm522*']
       "Found: /home/phyrexian/Downloads/cm522-main"

You: can you look into it?
Agent: [Executes: ls -lah /home/phyrexian/Downloads/cm522-main]
       [Shows directory contents]
```

**Expected**: Proactive search + pronoun resolution ✅  
**Before**: "You could use find command..." (useless) ❌

---

## Test 3: Long Conversation (SUMMARIZATION)

**Have a 60+ message conversation about anything.**

After ~30K tokens (roughly 60 messages):
- Backend should auto-summarize early messages
- You should NOT notice (transparent)
- Context should remain coherent

**Check logs for:** "Summarized conversation" message (means it triggered)

---

## Test 4: Authentication Recovery

**Simulate session loss:**
```bash
rm ~/.nocturnal_archive/session.json
cite-agent
```

**Expected**: 
- Auto-creates session.json from config.env
- You're logged in immediately
- NO "Not authenticated" errors ✅

---

## Test 5: Real Queries

```
You: Find papers on transformers
Agent: [Should show 3 papers with DOIs]

You: Tesla revenue
Agent: [$X billion from SEC filing]

You: Bitcoin price
Agent: [$X,XXX from CoinMarketCap]
```

**Expected**: All data sources working ✅

---

## What to Watch For

### ✅ **Should Work:**
- Conversation memory across messages
- Directory/file search with fuzzy names
- Pronoun resolution ("look into it")
- Long conversations (60+ messages)
- Authentication never fails

### ❌ **Should NOT Happen:**
- "Not authenticated" after successful login
- "You could use find command..." (should execute instead)
- Forgetting context from previous messages
- Web searching for "Downloads folder" (should use shell)

---

## If Something Breaks

**Check:**
1. Version: `cite-agent --version` (should be 1.2.11)
2. Session: `ls ~/.nocturnal_archive/session.json` (should exist)
3. Debug mode: `NOCTURNAL_DEBUG=1 cite-agent` (shows what's happening)

**Common fixes:**
```bash
# Reset everything
rm -rf ~/.nocturnal_archive/
pipx reinstall cite-agent

# Then login again
cite-agent --setup
```

---

## Current Status

**Backend**: ✅ v52 deployed (2 min ago)  
**CLI**: ✅ v1.2.11 built (ready to install)  
**Features**: ✅ All critical fixes deployed  

**Ready for testing when you are.** 🚀

