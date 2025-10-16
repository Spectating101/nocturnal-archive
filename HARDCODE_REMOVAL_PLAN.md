# Hardcode Removal Plan - Use LLM Intelligence

**Goal**: Replace ALL hardcoded pattern matching with LLM-based intelligence  
**Model**: llama-3.1-8b-instant (~50-200ms, cheap)  
**Benefit**: Flexible, context-aware, no maintenance

---

## Current Hardcoded Patterns (43 instances)

### **Category 1: Workflow Commands** (KEEP THESE)
```python
if any(phrase in question_lower for phrase in ["show my library", "export bibtex"]):
```
**Reason to keep**: Exact command matching, instant response, no ambiguity  
**Status**: ✅ Keep hardcoded

---

### **Category 2: Request Analysis** (REPLACE)

**Lines 2577-2580**: Compare detection
```python
if any(word in question_lower for word in ['compare', 'versus', 'vs']):
```
**Problem**: Misses: "what's the difference between", "X or Y?", "which is better"  
**Replace with**: LLM classifier

**Lines 2655-2663**: Financial metric detection
```python
if any(word in question_lower for word in ['market cap', 'marketcap']):
    metric = "marketCap"
elif any(word in question_lower for word in ['stock price']):
    metric = "price"
```
**Problem**: Brittle, misses synonyms ("valuation", "share value", "trading price")  
**Replace with**: LLM metric extractor

---

### **Category 3: Shell Command Detection** (REPLACE)

**Line 2734**: Needs shell check
```python
needs_shell = any(word in question_lower for word in [
    'directory', 'folder', 'where', 'find', 'list'...
])
```
**Problem**: False positives ("I wonder where Apple's revenue comes from")  
**Replace with**: Already using LLM planner ✅

---

### **Category 4: Ticker Extraction** (REPLACE)

**Current**: Regex for stock symbols
```python
tickers = re.findall(r'\b([A-Z]{2,5})\b', request.question)
```
**Problem**: False positives (USA, CEO, AI), misses lowercase (tsla)  
**Replace with**: LLM ticker extractor

---

### **Category 5: Web Search Triggers** (REPLACE)

**Lines 2684-2691**: Hardcoded web search triggers
```python
needs_web_search = (
    ('market share' in question_lower) or
    ('market size' in question_lower) or
    ('bitcoin' in question_lower) or...
)
```
**Problem**: Misses: "What % of cloud market does Snowflake have?"  
**Replace with**: LLM search decision

---

## Implementation Plan

### **Phase 1: Create Intelligence Layer** (NEW FILE)
Create `cite_agent/intelligence_layer.py`:
```python
class IntelligenceLay(self):
    """LLM-based intelligence for request understanding (no hardcoded patterns)"""
    
    async def classify_request(self, query: str, history: List) -> Dict:
        """What type of request? (research, finance, code, general)"""
        
    async def extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from query"""
        
    async def detect_financial_metric(self, query: str) -> str:
        """revenue, marketCap, price, eps, etc."""
        
    async def should_use_web_search(self, query: str, api_results: Dict) -> bool:
        """Does this need web search?"""
```

**All use llama-3.1-8b-instant, ~100-200ms each**

---

### **Phase 2: Replace Hardcoded Patterns**

**Request Analysis** → Use `classify_request()`  
**Ticker Extraction** → Use `extract_tickers()`  
**Metric Detection** → Use `detect_financial_metric()`  
**Web Search Decision** → Use `should_use_web_search()`

---

### **Phase 3: Testing**

Test cases that currently FAIL with hardcoded patterns:

**Ticker extraction:**
- "tsla stock" → Currently misses (lowercase)
- "What's Apple worth?" → Currently misses (company name)

**Metric detection:**
- "How much is Tesla valued at?" → Should detect "market cap"
- "What's the share price?" → Should detect "price"

**Web search:**
- "What percentage of cloud does Snowflake have?" → Should trigger (currently might not)

---

## Expected Benefits

**Accuracy**: 60% → 95% (handles edge cases, synonyms, context)  
**Maintenance**: Weekly fixes → Zero (LLM adapts)  
**Flexibility**: English only → Works with any phrasing  
**Latency**: +200ms per intelligence call (acceptable)  

---

## Token Cost

**Per query with intelligence:**
- Request classification: ~50 tokens
- Ticker extraction: ~30 tokens
- Metric detection: ~40 tokens
- Web search decision: ~40 tokens
**Total overhead**: ~160 tokens (~$0.000008)

**vs Hardcoded bugs**: Priceless

---

**Recommendation**: Implement this in v1.3.1 or v1.4.0

**Current v1.3.0 status**: Shell planning uses LLM ✅, other areas still hardcoded

