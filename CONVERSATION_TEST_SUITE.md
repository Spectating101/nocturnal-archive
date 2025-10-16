# Cite Agent v1.3.1 - Conversational Intelligence Test Suite

**Goal**: Test multi-turn conversations with context retention, pronoun resolution, and edge cases

**Not Testing**: Individual queries in isolation  
**Testing**: Full conversation flows with complex context dependencies

---

## Test Scenarios

### 🧪 SCENARIO 1: Shell Conversation Chain
**Goal**: Test context retention across shell operations

**Conversation**:
```
1. "find cm522 in downloads"
   Expected: Finds directory, stores path in conversation
   
2. "look into it"
   Expected: Resolves "it" → path from #1, lists contents
   
3. "what's in the data folder?"
   Expected: Resolves "data folder" → {path from #1}/data, lists contents
   
4. "go back to the main folder"
   Expected: Returns to path from #1
```

**Edge Cases**:
- Pronoun resolution across 3+ turns
- Nested directory references
- "Go back" without explicit path

---

### 🧪 SCENARIO 2: Finance Conversation with Comparison
**Goal**: Test finance context + follow-up queries

**Conversation**:
```
1. "Tesla revenue"
   Expected: TSLA revenue from FinSight
   
2. "what about Apple?"
   Expected: Infers "revenue" from #1, gets AAPL revenue
   
3. "which is higher?"
   Expected: Compares TSLA vs AAPL revenue from #1 and #2
   
4. "show me their market cap instead"
   Expected: Switches metric, gets both marketCap
```

**Edge Cases**:
- Implicit metric inheritance ("what about Apple?" assumes revenue)
- Comparison across previous results
- Metric switching mid-conversation

---

### 🧪 SCENARIO 3: Mixed Shell + Finance
**Goal**: Test context switching between different API types

**Conversation**:
```
1. "find any finance projects in downloads"
   Expected: Shell find for finance-related directories
   
2. "look into it"
   Expected: Lists directory found in #1
   
3. "what's Tesla's stock doing?"
   Expected: Switches to FinSight, gets TSLA data
   
4. "any papers on that company?"
   Expected: Switches to Archive, searches papers on Tesla
```

**Edge Cases**:
- Context switch (shell → finance → archive)
- "That company" resolves to Tesla from #3
- System remembers shell context while handling finance/archive

---

### 🧪 SCENARIO 4: Pronoun Chain (Deep Context)
**Goal**: Test pronoun resolution across multiple references

**Conversation**:
```
1. "find cm522"
   Expected: Finds /path/to/cm522-main
   
2. "what's in it?"
   Expected: "it" → cm522-main directory
   
3. "check the data folder in there"
   Expected: "there" → cm522-main from #1
   
4. "go back and show me the README"
   Expected: "back" → cm522-main, "README" → file in that dir
   
5. "summarize it"
   Expected: "it" → README.md content from #4
```

**Edge Cases**:
- Nested pronoun references (it → there → back → it)
- Each pronoun resolves to different entity
- 5-turn context retention

---

### 🧪 SCENARIO 5: Ambiguous Query Resolution
**Goal**: Test how system handles unclear intent

**Conversation**:
```
1. "look into it"
   Expected: "No previous context - what should I look into?"
   
2. "find something interesting"
   Expected: Clarifies "what should I look for?"
   
3. "financial reports"
   Expected: Now has context, searches for financial reports
   
4. "open the first one"
   Expected: References result from #3
```

**Edge Cases**:
- Pronoun without context (should ask for clarification)
- Vague query handling
- Building context incrementally

---

### 🧪 SCENARIO 6: Error Recovery
**Goal**: Test graceful handling of failures mid-conversation

**Conversation**:
```
1. "Tesla revenue"
   Expected: Works, gets data
   
2. "what about INVALID_TICKER_XYZ?"
   Expected: FinSight fails, graceful message
   
3. "okay, what about Apple then?"
   Expected: Recovers, still remembers "revenue" from #1
   
4. "compare Tesla and Apple"
   Expected: Uses results from #1 and #3, ignores failed #2
```

**Edge Cases**:
- API failure doesn't break conversation
- Context preserved across errors
- Comparison skips failed queries

---

### 🧪 SCENARIO 7: Long Conversation (Memory Test)
**Goal**: Test if conversation history stays coherent beyond 10 turns

**Conversation** (15+ turns):
```
1. "find cm522"
2. "look into it"
3. "what's the README say?"
4. "find any R scripts"
5. "show me calculate_annual_betas.R"
6. "what does it calculate?"
7. "Tesla revenue"
8. "what about Apple?"
9. "compare them"
10. "papers on portfolio theory"
11. "summarize the first paper"
12. "how does that relate to my R script?" (refers to #5)
13. "go back to cm522" (refers to #1)
14. "show files again" (refers to #2)
15. "what was Tesla's revenue again?" (refers to #7)
```

**Edge Cases**:
- References to turn #1 from turn #13 (long-range memory)
- Context switches (shell → finance → archive → back to shell)
- Conversation summarization at >10K tokens

---

### 🧪 SCENARIO 8: Interleaved Context
**Goal**: Test handling multiple parallel contexts

**Conversation**:
```
1. "find cm522"
   Context A: Shell, cm522 directory
   
2. "Tesla revenue"
   Context B: Finance, TSLA
   
3. "look into it" (ambiguous - refers to A or B?)
   Expected: Asks for clarification OR defaults to most recent (Tesla data)
   
4. "no, the directory"
   Expected: Clarifies, uses Context A (cm522)
   
5. "now show me Microsoft revenue"
   Context C: Finance, MSFT
   
6. "compare it with Tesla"
   Expected: MSFT from #5 vs TSLA from #2
```

**Edge Cases**:
- Multiple active contexts
- Ambiguous pronoun (could refer to 2 entities)
- System asks for clarification OR makes smart choice

---

### 🧪 SCENARIO 9: Rapid Context Switching
**Goal**: Test system handles fast topic changes

**Conversation**:
```
1. "Tesla revenue"
2. "find cm522"
3. "Apple market cap"
4. "papers on machine learning"
5. "what files are here?"
6. "Microsoft profit"
```

**Expected**:
- Each query independent (no cross-contamination)
- No "follow-up" assumptions when topics change
- Clean slate for each unrelated query

**Edge Cases**:
- No pronoun resolution when context is broken
- Each query gets fresh analysis

---

### 🧪 SCENARIO 10: Correction & Override
**Goal**: Test user corrections mid-conversation

**Conversation**:
```
1. "find cm5"
   Expected: Finds results for "cm5"
   
2. "no, I meant cm522"
   Expected: Overrides #1, searches for cm522
   
3. "look into it"
   Expected: Uses corrected result from #2, not #1
   
4. "Tesla revenue"
   Expected: Gets TSLA revenue
   
5. "actually, I meant Tesla market cap"
   Expected: Overrides metric, gets marketCap instead
```

**Edge Cases**:
- Correction invalidates previous result
- Subsequent queries use corrected context
- "Actually" and "no" trigger override logic

---

## Success Criteria

For each scenario, the agent must:
1. ✅ Maintain context across all turns
2. ✅ Resolve pronouns correctly
3. ✅ Handle ambiguity gracefully (ask for clarification)
4. ✅ Recover from errors without losing context
5. ✅ Switch contexts cleanly when topics change
6. ✅ Never hallucinate paths/data
7. ✅ Performance < 2s per turn

---

## Execution Plan

**Phase 1**: Run Scenarios 1-3 (basic flows)  
**Phase 2**: Run Scenarios 4-6 (complex/edge cases)  
**Phase 3**: Run Scenarios 7-10 (stress tests)  
**Phase 4**: Document failures, fix, retest

---

**Next**: Execute all scenarios with full conversation capture


