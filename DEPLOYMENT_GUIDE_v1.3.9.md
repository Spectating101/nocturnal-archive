# Cite-Agent v1.3.9 – Deployment & Showcase Guide

> Purpose-built for academic research and financial analysis. Treat this as the playbook for validating, demoing, and extending the agent in production-like environments.

## 1. Environment Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Optional: keep the conversation archive inside the repo sandbox
export CITE_AGENT_ARCHIVE_DIR="$(pwd)/.tmp_archive"
```

### Smoke Tests

```bash
.venv/bin/python -m pytest tests/enhanced -q          # 25 focused autonomy/unit tests
.venv/bin/python scripts/autonomy_harness.py          # Deterministic showcase scenarios
```

The harness simulates three “Cursor/Claude-style” demos without contacting live services:

| Scenario    | Tools Exercised                        | Expectation                                 |
|-------------|----------------------------------------|---------------------------------------------|
| Finance     | `_plan_financial_request`, FinSight    | Two tickers fetched, citations preserved    |
| File Ops    | Shell planner, safe command gating     | Reads temp files, no hallucinated content   |
| Research    | Archive pipeline, citation collection  | Returns real-looking paper metadata only    |

## 2. Persistent Research Memory

- `cite_agent/conversation_archive.py` stores compact summaries per `(user_id, conversation_id)` in `~/.cite_agent/conversation_archive` (override via `CITE_AGENT_ARCHIVE_DIR`).
- `EnhancedNocturnalAgent` now pulls the last three summaries into the system prompt so returning users pick up where they left off.
- Archives stay local and contain summarised responses plus cited sources—no raw transcripts.

To reset per-session memory:

```bash
rm -rf ~/.cite_agent/conversation_archive  # or your custom archive dir
```

## 3. Capability Showcase Script

`scripts/autonomy_harness.py` prints the synthesized responses, tool usage ledger, and API calls hit in each scenario. Use it verbatim during demos to illustrate parity with Claude Code / Cursor without network dependencies.

```bash
# Text transcript for all scenarios
.venv/bin/python scripts/autonomy_harness.py

# JSON metrics for selected cases
.venv/bin/python scripts/autonomy_harness.py --only finance research --json artifacts/autonomy.json --no-transcript
```

The harness now captures elapsed time, tool usage, backend prompts, and—if you include the archive scenario—proof that persistent context is loaded across sessions. Use it to generate reproducible transcripts and charts that benchmark the agent against Claude/Cursor workflows.

## 4. Manual Demo Flow

1. **Repo walk-through** – ask the agent (CLI or API) to describe `cite_agent/enhanced_ai_agent.py`; verify it surfaces planner, archive, and workflow components.
2. **Financial query** – “Compare revenue and net income for Apple and Microsoft this quarter.” Confirm SEC-sourced metrics and citations, no hallucinations.
3. **Data inspection** – drop a CSV in the workspace, request summary stats; agent should call Python/R safely (or explain limitations if offline).
4. **Research synthesis** – “Summarize recent transformer research trends.” Ensure returned papers include DOIs and the archive records a summary.

## 5. Deployment Notes

- **Backend endpoints**: `https://cite-agent-api-720dfadd602c.herokuapp.com` (Archive/FinSight/query). Keep API tokens server-side; the client never ships secrets.
- **Packaging**: `dist/cite_agent-1.3.9.tar.gz` and the wheel are ready for `twine upload`; Windows installer work is paused until UX stabilises.
- **Branch status**: `production-backend-only` with conversation archive + autonomy harness merged; run `git status` before shipping.

## 6. Outstanding Enhancements

- Re-introduce the end-to-end integration tests once the stub harness graduates into a fixture (currently the harness is manual-only).
- Expand the archive to store cross-session TODOs / follow-ups so the planner can proactively remind users.
- Optional: finish the Windows installer once the feature surface is locked and telemetry confirms stability.

## 7. Support Checklist Before Each Release

- [ ] `pytest` suite green, harness output reviewed
- [ ] `DEPLOYMENT_GUIDE_v1.3.9.md` updated with any new workflow steps
- [ ] `CHANGELOG.md` and `README.md` reflect new capabilities
- [ ] Archive directory verified/cleared if demoing on a fresh machine

Deliver these steps and you’ll have a smooth showcase that demonstrates why Cite-Agent is a trusted research partner—not just a “good enough” coding bot.
