# Research Kit: Financial Events Briefing

Produce a concise financial brief for leadership or investors using Nocturnal Archive's finance integrations.

## Goal
Summarize recent performance, key metrics, and news sentiment for one or more tickers.

## Inputs
- **Tickers**: e.g., `AAPL, MSFT`
- **Period**: e.g., `2024-Q2`
- **Metrics**: revenue growth, operating margin, EPS, guidance updates
- **News window**: past 14 days recommended

## Agent Prompt
```
You are a financial analyst.
Task: Create an executive briefing covering {TICKERS} for {PERIOD}.
Include:
- KPI table (Revenue, Operating Margin, EPS) for the last four quarters
- Recent news highlights with sentiment (past {NEWS_WINDOW})
- Analyst consensus or notable forecasts
- Risks & opportunities
- Recommended follow-up actions
```

## Recommended Workflow
1. Run the prompt via the Enhanced Nocturnal Agent.
2. Allow the agent to call FinSight endpoints and data-analysis tools.
3. Review generated charts saved under `~/.nocturnal_archive/outputs/`.
4. Export the briefing to PDF or presentation format.

## Quality Checklist
- [ ] KPI table includes actual values and quarter labels
- [ ] News items reference credible sources with links
- [ ] Sentiment analysis is supported by brief evidence
- [ ] Follow-up actions are specific and time-bound

## Extensions
- Ask for scenario analysis: "Model the impact of ±5% revenue change on EPS"
- Request a quote-ready summary: "Draft a 3-sentence executive email"
- Chain into research kit: "Compare these findings with top 3 competitors"
