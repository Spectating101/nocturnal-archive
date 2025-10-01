# Capability-Aware Groq Model Routing

## Overview

Implemented intelligent model routing that automatically selects the appropriate Groq model based on task complexity and requirements. This ensures optimal performance and cost efficiency by matching model capabilities to task demands.

## Architecture

### Task Complexity Classification

- **LITE** (≤300 tokens): Lookup, grep, quote, simple Q&A
- **MEDIUM** (≤800 tokens): Code explain, short synthesis  
- **HEAVY** (≥800 tokens): Multi-doc synthesis, reasoning, safety-critical

### Available Models

| Model | Capability | Cost Tier | Latency | Recommended For |
|-------|------------|-----------|---------|-----------------|
| `llama-3.1-8b-instant` | Fast, cheap | 0.1x | Fast | LITE tasks |
| `gemma2-9b-it` | Balanced | 0.15x | Fast | LITE, MEDIUM tasks |
| `llama-3.3-70b-versatile` | Most capable | 1.0x | Slow | All tasks (HEAVY preferred) |

### Routing Logic

1. **Task Analysis**: Classifies complexity based on:
   - Output word count
   - Number of papers
   - Task type (lookup, synthesis, etc.)
   - Reasoning requirements

2. **Model Selection**: 
   - Prefers faster/cheaper models for simple tasks
   - Automatically upgrades to heavy models for complex tasks
   - Falls back gracefully if preferred model unavailable

3. **Strict Mode**: 
   - `/synthesize/strict` endpoint requires heavy model capability
   - Returns 503 if no suitable heavy model available
   - Provides fallback suggestions

## API Endpoints

### Regular Synthesis (Smart Routing)
```http
POST /api/synthesize
```
- Automatically selects optimal model
- Falls back to rule-based synthesis if no LLM available
- Returns routing metadata in response

### Strict Synthesis (Heavy Model Required)
```http
POST /api/synthesize/strict
```
- Requires 70B+ model capability
- Returns 503 if no heavy model available
- Provides fallback suggestions

## Response Format

Both endpoints return routing metadata:

```json
{
  "summary": "...",
  "key_findings": [...],
  "citations_used": {...},
  "word_count": 500,
  "metadata": {
    "routing_metadata": {
      "routing_decision": {
        "model": "llama-3.3-70b-versatile",
        "complexity": "heavy",
        "reasoning": "Selected llama-3.3-70b-versatile for heavy task (cost: 1.0)",
        "estimated_tokens": 8192
      },
      "usage": {
        "total_tokens": 1234,
        "prompt_tokens": 800,
        "completion_tokens": 434
      }
    }
  }
}
```

## Benefits

1. **Cost Optimization**: Uses cheaper models for simple tasks
2. **Performance**: Fast models for quick responses, heavy models for complex analysis
3. **Reliability**: Graceful fallbacks and error handling
4. **Transparency**: Full routing metadata in responses
5. **Flexibility**: Both automatic and strict modes available

## Future Enhancements

- API key rotation for network-wide optimization
- Multi-provider routing (OpenAI, Mistral, Cohere)
- Dynamic model availability checking
- Usage analytics and optimization recommendations


