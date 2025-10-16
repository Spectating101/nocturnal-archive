# Research Kit: Rapid Literature Review

Use this template to spin up a structured literature review in minutes.

## Goal
Summarize the latest findings for a specific research question, capture citation-ready metadata, and surface open questions.

## Inputs
- **Topic**: e.g., "CRISPR base editing efficiency"
- **Time horizon**: e.g., "last 24 months"
- **Target sources**: Any combination of OpenAlex, PubMed, arXiv
- **Desired output length**: 400–600 words recommended

## Agent Prompt
```
You are an academic research assistant.
Task: Produce a structured literature review on "{TOPIC}".
Constraints:
- Focus on publications from {TIME_HORIZON}
- Retrieve papers from {SOURCES}
- Include at least 6 distinct papers
- Provide inline citations using the form [Author Year]
- Finish with a "Key Open Questions" section listing 3 follow-up research questions
```

## Recommended Workflow
1. Run the prompt through the **Enhanced Nocturnal Agent** (CLI or web UI).
2. If the agent flags the job as long-running, note the estimated completion time and continue once notified.
3. Review the output for coverage and accuracy.
4. Export the final report as Markdown or PDF.

## Quality Checklist
- [ ] Contains 6+ unique, credible papers
- [ ] Citations map to verifiable sources in the output metadata
- [ ] Includes a short "Methodology" summary of how the research was gathered
- [ ] Lists 3+ open questions or future directions

## Extensions
- Ask the agent to generate comparative tables (e.g., sample sizes, key metrics)
- Request chart-ready data for quick visualization (the CLI will save generated charts under `~/.nocturnal_archive/outputs/`)
- Chain into a follow-up task: "Draft a 1-page executive summary for non-technical stakeholders"
