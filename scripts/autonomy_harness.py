#!/usr/bin/env python3
"""Advanced autonomy harness to evaluate Cite-Agent offline."""

import argparse
import asyncio
import json
from collections import Counter
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("CITE_AGENT_ARCHIVE_DIR", str(ROOT / ".tmp_archive"))

from cite_agent.conversation_archive import ConversationArchive
from cite_agent.enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest, ChatResponse

ResponseFactory = Callable[[str, Any, Any], str]


def _default_backend_response(query: str) -> str:
    """Fallback response for planner/decision prompts."""
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "Local harness run – web search unnecessary"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "none",
                "command": "",
                "reason": "Harness default: no shell needed",
                "updates_context": False,
            }
        )
    return "Synthetic backend summary"


def _snippets_present(text: str, snippets: List[str]) -> bool:
    return all(snippet in text for snippet in snippets)


def _normalise_topic(text: str) -> str:
    stripped = text.strip().strip('"').strip()
    stripped = stripped.rstrip("?.!\n")
    lowered = stripped.lower()
    prefixes = [
        "summarize",
        "summarise",
        "analyze",
        "analyse",
        "investigate",
        "review",
        "explore",
        "continue",
        "compare",
        "assess",
        "outline",
        "update",
    ]
    trim_chars = " ,:;-\n"
    for prefix in prefixes:
        if lowered.startswith(prefix):
            stripped = stripped[len(prefix):].lstrip(trim_chars)
            break
    return stripped or text.strip()


class _StubShell:
    """Minimal stub so shell planning paths stay active."""

    def poll(self) -> Optional[int]:
        return None


class FakeBackend:
    """Intercepts backend calls to keep scenarios deterministic."""

    def __init__(self, ledger: List[Dict[str, Any]], response_factory: Optional[ResponseFactory] = None):
        self.ledger = ledger
        self.response_factory = response_factory

    async def __call__(
        self,
        query: str,
        conversation_history: Any = None,
        api_results: Any = None,
        tools_used: Any = None,
    ) -> ChatResponse:
        entry = {
            "query": query.strip(),
            "history": conversation_history or [],
            "api_results": api_results or {},
        }
        self.ledger.append(entry)

        try:
            response_text = (
                self.response_factory(query, conversation_history, api_results)
                if self.response_factory
                else _default_backend_response(query)
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            response_text = f"Synthetic backend summary (factory error: {exc})"

        return ChatResponse(response=response_text, tools_used=tools_used or [], api_results=api_results or {})


def _finance_response_factory(query: str, _history: Any, api_results: Any) -> str:
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "FinSight covers these tickers"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "none",
                "command": "",
                "reason": "Financial comparison handled via FinSight API",
                "updates_context": False,
            }
        )

    financial = api_results.get("financial", {})

    def _fmt(metric: Optional[Dict[str, Any]]) -> str:
        value = metric.get("value") if isinstance(metric, dict) else None
        if value is None:
            return "n/a"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return str(value)
        if abs(value) >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        return f"${value:,.0f}"

    lines = []
    for ticker in ("AAPL", "MSFT"):
        payload = financial.get(ticker, {})
        revenue = _fmt(payload.get("revenue"))
        net_income = _fmt(payload.get("netIncome"))
        source = payload.get("revenue", {}).get("source") or payload.get("netIncome", {}).get("source") or "FinSight API"
        lines.append(f"- {ticker}: revenue {revenue}, net income {net_income} (source: {source})")

    if not lines:
        return "FinSight comparison complete but no data was returned."
    return "FinSight comparison complete:\n" + "\n".join(lines)


def _file_ops_response_factory(query: str, _history: Any, api_results: Any) -> str:
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "Notes file is already local"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "execute",
                "command": "head -n 20 notes.txt",
                "reason": "Read notes.txt before summarizing it",
                "updates_context": False,
            }
        )

    shell_info = api_results.get("shell_info", {})
    output = shell_info.get("output", "")
    lines: List[str] = []
    for line in str(output).splitlines():
        if "→" in line:
            lines.append(line.split("→", 1)[1])
        else:
            lines.append(line)
    snippet = " ".join(lines[:3]).strip()
    summary = snippet if snippet else "No readable content found."
    return f"I read notes.txt and found: {summary}"


def _repo_overview_response_factory(summary: str, services: Dict[str, Any]) -> ResponseFactory:
    def _factory(query: str, history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "Repository contents are local"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "execute",
                    "command": "ls -lah",
                    "reason": "Inspect repository roots before summarizing",
                    "updates_context": False,
                }
            )

        top_dirs = services["top_dirs"]
        top_files = services["top_files"]
        tests_count = services["tests_count"]
        docs = services["docs"]

        bullets = [
            f"Top-level packages: {', '.join(top_dirs)}",
            f"Key modules: {', '.join(top_files)}",
            f"Automated tests detected: {tests_count}",
        ]
        if docs:
            bullets.append(f"Documentation: {', '.join(docs)}")

        bullet_text = "\n".join(f"- {item}" for item in bullets)

        follow_up = ""
        if history:
            follow_up = "\n\nI can drill into any package or run targeted searches if you need more detail."

        return f"{summary}\n\n{bullet_text}{follow_up}"

    return _factory


def _build_research_summary(results: List[Dict[str, Any]], topic: Optional[str] = None) -> str:
    if not results:
        if topic:
            return f"I checked the academic index but couldn't find recent papers on {topic}."
        return "I checked the academic index but couldn't find relevant papers."

    def _fmt_paper(paper: Dict[str, Any]) -> str:
        title = paper.get("title", "Untitled work")
        year = paper.get("year", "n.d.")
        authors = paper.get("authors") or []
        byline = ", ".join(authors[:2])
        if len(authors) > 2:
            byline += " et al."
        doi = paper.get("doi")
        doi_part = f" (doi: {doi})" if doi else ""
        return f"{title} ({year}) — {byline}{doi_part}"

    highlights = [_fmt_paper(paper) for paper in results[:3]]
    bullet_list = "\n".join(f"- {item}" for item in highlights)
    topic_clean = topic.strip().strip('"') if topic else ""
    intro_topic = f" on \u201c{topic_clean}\u201d" if topic_clean else ""
    summary = (
        f"I pulled {len(results)} recent papers{intro_topic}:\n"
        f"{bullet_list}"
    )
    closing = "\n\nThese sources provide peer-reviewed grounding; let me know if you want deeper synthesis or specific metrics."
    return summary + closing


def _research_response_factory(query: str, history: Any, api_results: Any) -> str:
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "Archive API already returned peer-reviewed sources"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "none",
                "command": "",
                "reason": "Research queries rely on Archive API results, not shell access",
                "updates_context": False,
            }
        )

    research_payload = api_results.get("research", {})
    results = research_payload.get("results") or []
    sources = research_payload.get("sources_tried") or []
    topic = _normalise_topic(query)
    base_summary = _build_research_summary(results, topic=topic)
    if sources:
        base_summary += f"\nSources queried: {', '.join(sources)}."
    if history:
        base_summary += "\n\nBuilding on our earlier discussion, I'll focus the narrative around data efficiency and architectural innovations."
    return base_summary


def make_archive_resume_factory(initial_summary: str) -> ResponseFactory:
    def _factory(query: str, history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "Archive already provides the needed context"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "none",
                    "command": "",
                    "reason": "Archive context available; no filesystem action required",
                    "updates_context": False,
                }
            )

        research_payload = api_results.get("research", {})
        results = research_payload.get("results") or []
        topic = _normalise_topic(query)
        continuation = _build_research_summary(results, topic=topic)
        continuation += "\n\nPulling forward from the archived summary:\n"
        continuation += f"“{initial_summary.strip()}”\n"
        continuation += "I'll integrate the new findings to extend that discussion and highlight any shifts in Tesla's sustainability metrics."
        return continuation

    return _factory


def _ambiguous_response_factory(query: str, _history: Any, api_results: Any) -> str:
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "Need clarification before searching or fetching data"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "none",
                "command": "",
                "reason": "The prompt lacks context—ask a clarifying question instead of running shell commands",
                "updates_context": False,
            }
        )

    analysis = api_results.get("query_analysis", {})
    reason = analysis.get("reason") or "The request is ambiguous."
    reason = reason.rstrip()
    if reason and not reason.endswith(('.', '!', '?')):
        reason += '.'
    return (
        f"I don't want to guess and risk a wrong answer. {reason} "
        "Could you clarify whether you want economic data, research highlights, or something else about 2008, 2015, and 2019?"
    )


def _data_pipeline_response_factory(summary: str) -> ResponseFactory:
    def _factory(query: str, _history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "Data is local CSV files"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "execute",
                    "command": "python - <<'PY'\nimport pandas as pd\nimport json\ndf = pd.read_csv('sales_data.csv')\nresult = df.groupby(['region', 'product']).agg({'revenue': 'sum'}).reset_index()\nprint(result.to_json(orient='records'))\nPY",
                    "reason": "Aggregate sales by region and product",
                    "updates_context": False,
                }
            )

        shell_info = api_results.get("shell_info", {})
        output = shell_info.get("output")
        insights = summary
        if output:
            try:
                import json as _json

                records = _json.loads(output)
                top = max(records, key=lambda item: item.get("revenue", 0.0))
                insights += (
                    f"\nTop performer: {top.get('product')} in {top.get('region')} "
                    f"with revenue ${top.get('revenue'):,}"
                )
            except Exception:
                pass

        return insights

    return _factory


def _multi_hop_response_factory(research_payload: Dict[str, Any], finance_payload: Dict[str, Any]) -> ResponseFactory:
    def _factory(query: str, history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "Archive and FinSight APIs already cover this query"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "none",
                    "command": "",
                    "reason": "Analysis relies on API data rather than shell commands",
                    "updates_context": False,
                }
            )

        papers = research_payload.get("results", [])
        finance = finance_payload.get("financial", {})
        ticker = next(iter(finance.keys()), "NVDA")
        metrics = finance.get(ticker, {})
        revenue = metrics.get("revenue", {}).get("value")
        net_income = metrics.get("netIncome", {}).get("value")

        paper_lines = "\n".join(
            f"- {item.get('title')} ({item.get('year')}) — {', '.join(item.get('authors', [])[:2])}"
            for item in papers[:3]
        )

        return (
            "Research + market synthesis:\n"
            f"{paper_lines}\n\n"
            f"{ticker} latest revenue ${revenue:,.0f} and net income ${net_income:,.0f} suggest "
            "commercial demand aligns with the academic push toward efficient transformer inference. "
            "Consider highlighting energy-aware architectures when briefing stakeholders."
        )

    return _factory


def _repo_refactor_response_factory(insights: Dict[str, Any]) -> ResponseFactory:
    def _factory(query: str, history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "All code files are available locally"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "execute",
                    "command": "head -n 120 module.py",
                    "reason": "Review existing implementation before suggesting refactor",
                    "updates_context": False,
                }
            )

        smells = insights["smells"]
        plan = insights["plan"]
        lines = [
            "Refactor summary:",
            f"- Detected issues: {', '.join(smells)}",
            f"- Proposed plan: {plan}",
            "- Suggested follow-up: add unit test for edge cases and update documentation.",
        ]
        return "\n".join(lines)

    return _factory


def _data_analysis_response(query: str, _history: Any, api_results: Any) -> str:
    command = (
        "python - <<'PY'\n"
        "import csv, statistics, json\n"
        "import pathlib\n"
        "path = pathlib.Path('sample_data.csv')\n"
        "values = [float(row['value']) for row in csv.DictReader(path.open())]\n"
        "result = { 'count': len(values), 'mean': statistics.mean(values), 'stdev': round(statistics.pstdev(values), 4)}\n"
        "print(json.dumps(result))\n"
        "PY"
    )
    lower = query.lower()
    if '"use_web_search"' in query or "use_web_search" in lower:
        return json.dumps({"use_web_search": False, "reason": "CSV is local, shell execution suffices"})
    if "shell command planner" in lower:
        return json.dumps(
            {
                "action": "execute",
                "command": command,
                "reason": "Run Python locally to compute statistics",
                "updates_context": False,
            }
        )

    shell_info = api_results.get("shell_info", {})
    output = shell_info.get("output")
    try:
        stats = json.loads(output) if output else {}
    except json.JSONDecodeError:
        stats = {}
    if stats:
        summary = (
            "CSV analysis complete.\n"
            f"- rows analysed: {stats.get('count')}\n"
            f"- mean value: {stats.get('mean')}\n"
            f"- population stdev: {stats.get('stdev')}\n"
        )
    else:
        summary = "CSV analysis complete but statistics were unavailable."
    return (
        "I will inspect the CSV and compute summary statistics.\n\n"
        f"```shell\n{command}\n```\n"
        f"{summary}"
    )


async def run_finance_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []
    agent.call_backend_query = FakeBackend(ledger, response_factory=_finance_response_factory)  # type: ignore[assignment]

    async def fake_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "financial",
            "apis": ["finsight"],
            "confidence": 0.9,
            "analysis_mode": "quantitative",
        }

    agent._analyze_request_type = fake_analysis  # type: ignore[assignment]
    agent._plan_financial_request = lambda q, session_key=None: (["AAPL", "MSFT"], ["revenue", "netIncome"])  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    captured_calls: List[Tuple[str, Tuple[str, ...]]] = []

    async def fake_get_financial_metrics(ticker: str, metrics: List[str]):
        captured_calls.append((ticker, tuple(metrics)))
        return {metric: {"value": 123456789, "source": "SEC 10-K"} for metric in metrics}

    agent.get_financial_metrics = fake_get_financial_metrics  # type: ignore[assignment]

    response = await agent.process_request(
        ChatRequest(question="Compare revenue and net income for Apple and Microsoft this quarter")
    )
    await agent.close()
    return {
        "response": response,
        "finance_calls": captured_calls,
        "ledger": ledger,
    }


async def run_local_file_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []
    agent.call_backend_query = FakeBackend(ledger, response_factory=_file_ops_response_factory)  # type: ignore[assignment]

    async def fake_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "system",
            "apis": ["shell"],
            "confidence": 0.8,
            "analysis_mode": "quantitative",
        }

    agent._analyze_request_type = fake_analysis  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "notes.txt"
        target.write_text("first line\nsecond line\nthird line\n", encoding="utf-8")
        agent.file_context["current_cwd"] = str(tmp_path)

        original_read_file = agent.read_file

        def local_read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
            resolved = Path(path)
            if not resolved.is_absolute():
                resolved = tmp_path / path
            return original_read_file(str(resolved), offset, limit)

        agent.read_file = local_read_file  # type: ignore[assignment]

        def fake_execute(cmd: str) -> str:
            cleaned = cmd.strip()
            if cleaned == "pwd":
                return str(tmp_path)
            if "notes.txt" in cleaned:
                return target.read_text(encoding="utf-8")
            return ""

        agent.execute_command = fake_execute  # type: ignore[assignment]

        response = await agent.process_request(
            ChatRequest(question="Read the contents of notes.txt and summarize it")
        )
    await agent.close()
    return {
        "response": response,
        "ledger": ledger,
    }


async def run_research_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []
    agent.call_backend_query = FakeBackend(ledger, response_factory=_research_response_factory)  # type: ignore[assignment]

    async def fake_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "research",
            "apis": ["archive"],
            "confidence": 0.85,
            "analysis_mode": "mixed",
        }

    agent._analyze_request_type = fake_analysis  # type: ignore[assignment]

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    async def fake_search(query: str, limit: int = 5) -> Dict[str, Any]:
        return {
            "results": [
                {
                    "title": "Foundations of Transformer Models",
                    "year": 2023,
                    "authors": ["Doe", "Smith"],
                    "doi": "10.1234/example",
                }
            ],
            "sources_tried": ["semantic_scholar"],
        }

    agent.search_academic_papers = fake_search  # type: ignore[assignment]

    response = await agent.process_request(
        ChatRequest(question="Summarize recent transformer research trends")
    )
    await agent.close()
    return {
        "response": response,
        "ledger": ledger,
    }


async def run_archive_resume_showcase() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["CITE_AGENT_ARCHIVE_DIR"] = tmp

        ledger_first: List[Dict[str, Any]] = []
        agent_first = EnhancedNocturnalAgent()
        agent_first.archive = ConversationArchive(root=tmp)
        agent_first.workflow.save_query_result = lambda *args, **kwargs: None
        agent_first.call_backend_query = FakeBackend(ledger_first, response_factory=_research_response_factory)  # type: ignore[assignment]

        async def research_analysis(question: str) -> Dict[str, Any]:
            return {
                "type": "research",
                "apis": ["archive"],
                "confidence": 0.85,
                "analysis_mode": "mixed",
            }

        agent_first._analyze_request_type = research_analysis  # type: ignore[assignment]

        async def backend_ready_first() -> Tuple[bool, str]:
            return True, ""

        agent_first._ensure_backend_ready = backend_ready_first  # type: ignore[assignment]

        async def fake_search(query: str, limit: int = 5) -> Dict[str, Any]:
            return {
                "results": [
                    {
                        "title": "Tesla Energy Impact",
                        "year": 2024,
                        "authors": ["Analyst"],
                        "doi": "10.1234/tesla.energy",
                    }
                ],
                "sources_tried": ["semantic_scholar"],
            }

        agent_first.search_academic_papers = fake_search  # type: ignore[assignment]
        question_first = "Summarize Tesla sustainability research findings."
        response_first = await agent_first.process_request(
            ChatRequest(question=question_first, user_id="demo", conversation_id="session")
        )
        summary_payload = agent_first._format_archive_summary(
            question_first,
            response_first.response,
            {"research": {"results": [{"title": "Tesla Energy Impact"}]}}
        )
        agent_first.archive.record_entry(
            "demo",
            "session",
            summary_payload["question"],
            summary_payload["summary"],
            ["archive_api"],
            summary_payload["citations"],
        )
        archive_context_first = agent_first.archive.get_recent_context("demo", "session")
        archive_files_after_first = list(Path(tmp).glob("*.json"))
        await agent_first.close()

        ledger_second: List[Dict[str, Any]] = []
        agent_second = EnhancedNocturnalAgent()
        agent_second.archive = ConversationArchive(root=tmp)
        agent_second.workflow.save_query_result = lambda *args, **kwargs: None
        agent_second._analyze_request_type = research_analysis  # type: ignore[assignment]

        async def backend_ready_second() -> Tuple[bool, str]:
            return True, ""

        agent_second._ensure_backend_ready = backend_ready_second  # type: ignore[assignment]
        agent_second.search_academic_papers = fake_search  # type: ignore[assignment]

        archived_summary = summary_payload["summary"]
        agent_second.call_backend_query = FakeBackend(
            ledger_second,
            response_factory=make_archive_resume_factory(archived_summary)
        )  # type: ignore[assignment]

        response_second = await agent_second.process_request(
            ChatRequest(question="Continue the Tesla analysis.", user_id="demo", conversation_id="session")
        )
        await agent_second.close()

        return {
            "response_first": response_first,
            "response_second": response_second,
            "ledger_second": ledger_second,
            "archive_context": agent_second.archive.get_recent_context("demo", "session"),
            "archive_files": [str(p.name) for p in archive_files_after_first],
            "archive_context_first": archive_context_first,
        }


async def run_ambiguous_query_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []
    agent.call_backend_query = FakeBackend(ledger, response_factory=_ambiguous_response_factory)  # type: ignore[assignment]

    async def vague_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "general",
            "apis": [],
            "confidence": 0.4,
            "analysis_mode": "general",
        }

    agent._analyze_request_type = vague_analysis  # type: ignore[assignment]

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    response = await agent.process_request(ChatRequest(question="Compare 2008, 2015, 2019"))
    await agent.close()
    return {"response": response, "ledger": ledger}


async def run_data_analysis_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []
    agent.call_backend_query = FakeBackend(ledger, response_factory=_data_analysis_response)  # type: ignore[assignment]

    async def pipeline_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "system",
            "apis": ["shell"],
            "confidence": 0.8,
            "analysis_mode": "quantitative",
        }

    agent._analyze_request_type = pipeline_analysis  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "sample_data.csv"
        csv_path.write_text("value\n10\n15\n20\n25\n30\n", encoding="utf-8")
        agent.file_context["current_cwd"] = str(tmp_path)

        preview = agent.read_file(str(csv_path))

        def fake_execute(cmd: str) -> str:
            import csv
            import statistics
            import json

            cleaned = cmd.strip()
            if cleaned == "pwd":
                return str(tmp_path)

            values = [float(row['value']) for row in csv.DictReader(csv_path.open())]
            result = {
                "count": len(values),
                "mean": statistics.mean(values),
                "stdev": round(statistics.pstdev(values), 4),
            }
            return json.dumps(result)

        agent.execute_command = fake_execute  # type: ignore[assignment]

        response = await agent.process_request(
            ChatRequest(question="Analyze sample_data.csv and report summary statistics.")
        )

    await agent.close()
    guardrails = {
        "contains_mean": _snippets_present(response.response, ["mean value: 20.0"]),
        "contains_stdev": _snippets_present(response.response, ["population stdev: 7.0711"]),
    }

    return {
        "csv_preview": preview,
        "response": response,
        "ledger": ledger,
        "quality_checks": guardrails,
    }


async def run_repo_overview_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    top_level_dirs = sorted([p.name for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")])[:6]
    key_modules = sorted(
        [
            str(path.relative_to(ROOT))
            for path in ROOT.glob("cite_agent/**/*.py")
            if path.is_file() and path.parent == ROOT / "cite_agent"
        ]
    )[:6]
    docs = sorted([p.name for p in ROOT.glob("docs/*.md")])[:3]
    tests_count = sum(1 for _ in ROOT.glob("tests/**/*.py"))

    services = {
        "top_dirs": top_level_dirs,
        "top_files": key_modules,
        "docs": docs,
        "tests_count": tests_count,
    }

    repo_summary = (
        "Here is the current repository structure based on the local workspace."
        "\nEach package summary is grounded in the actual files."
    )

    agent.call_backend_query = FakeBackend(
        ledger,
        response_factory=_repo_overview_response_factory(repo_summary, services),
    )  # type: ignore[assignment]

    async def fake_analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "system",
            "apis": ["shell"],
            "confidence": 0.85,
            "analysis_mode": "mixed",
        }

    agent._analyze_request_type = fake_analysis  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    def fake_execute(cmd: str) -> str:
        cleaned = cmd.strip()
        if cleaned == "pwd":
            return str(ROOT)
        if cleaned.startswith("ls"):
            entries = []
            for path in sorted(ROOT.iterdir()):
                if path.name.startswith("."):
                    continue
                if path.is_dir():
                    entries.append(f"drwx------ {path.name}/")
                else:
                    entries.append(f"-rw------- {path.name}")
            return "\n".join(entries)
        if cleaned.startswith("find"):
            return "\n".join(
                str(path.relative_to(ROOT))
                for path in sorted(ROOT.glob("**/*.py"))
                if path.is_file()
            )
        return ""

    agent.execute_command = fake_execute  # type: ignore[assignment]

    original_read_file = agent.read_file

    def repo_read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
        target = Path(path)
        if not target.is_absolute():
            target = ROOT / target
        if not target.exists():
            return f"ERROR: File not found: {target}"
        return original_read_file(str(target), offset=offset, limit=limit)

    agent.read_file = repo_read_file  # type: ignore[assignment]

    response = await agent.process_request(
        ChatRequest(question="Give me an overview of this repository's structure and primary modules.")
    )
    await agent.close()
    guardrails = {
        "listed_modules": _snippets_present(response.response, services["top_files"][:2]),
        "listed_docs": _snippets_present(response.response, services["docs"][:1]) if services["docs"] else True,
    }
    return {"response": response, "ledger": ledger, "repo_snapshot": services, "quality_checks": guardrails}


async def run_data_pipeline_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    pipeline_summary = (
        "I inspected the sales dataset, aggregated revenue by region and product, and prepared the results."
    )

    agent.call_backend_query = FakeBackend(
        ledger,
        response_factory=_data_pipeline_response_factory(pipeline_summary),
    )  # type: ignore[assignment]

    async def analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "system",
            "apis": ["shell"],
            "confidence": 0.85,
            "analysis_mode": "quantitative",
        }

    agent._analyze_request_type = analysis  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "sales_data.csv"
        csv_path.write_text(
            "region,product,revenue\n"
            "North,Alpha,12000\n"
            "North,Bravo,9500\n"
            "West,Alpha,14300\n"
            "West,Bravo,15800\n"
            "South,Alpha,11200\n"
            "South,Bravo,10100\n",
            encoding="utf-8",
        )
        agent.file_context["current_cwd"] = str(tmp_path)

        def fake_execute(cmd: str) -> str:
            cleaned = cmd.strip()
            if cleaned == "pwd":
                return str(tmp_path)
            if "sales_data.csv" in cleaned:
                import csv as _csv
                import json as _json

                totals: Dict[Tuple[str, str], float] = {}
                with csv_path.open() as handle:
                    reader = _csv.DictReader(handle)
                    for row in reader:
                        key = (row["region"], row["product"])
                        totals[key] = totals.get(key, 0.0) + float(row["revenue"])
                records = [
                    {"region": region, "product": product, "revenue": revenue}
                    for (region, product), revenue in totals.items()
                ]
                return _json.dumps(records)
            return ""

        agent.execute_command = fake_execute  # type: ignore[assignment]

        original_read_file = agent.read_file

        def temp_read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
            target = Path(path)
            if not target.is_absolute():
                target = tmp_path / path
            return original_read_file(str(target), offset=offset, limit=limit)

        agent.read_file = temp_read_file  # type: ignore[assignment]

        response = await agent.process_request(
            ChatRequest(
                question="Load sales_data.csv, calculate revenue totals by region and product, and highlight the top performer."
            )
        )
    await agent.close()
    guardrails = {
        "reports_top_performer": _snippets_present(response.response, ["Bravo", "West", "15,800"]),
    }
    return {"response": response, "ledger": ledger, "quality_checks": guardrails}


async def run_self_service_shell_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    def response_factory(query: str, _history: Any, api_results: Any) -> str:
        lower = query.lower()
        if "shell command planner" in lower:
            return json.dumps({
                "action": "none",
                "command": "",
                "reason": "Ask the user to list files",
                "updates_context": False,
            })
        listing = api_results.get("shell_info", {}).get("output", "(no output)")
        return f"Directory contents:\n{listing}"

    agent.call_backend_query = FakeBackend(ledger, response_factory=response_factory)  # type: ignore[assignment]

    executed_commands: List[str] = []

    def fake_execute(cmd: str) -> str:
        cleaned = cmd.strip()
        if cleaned.lower() == "pwd":
            return str(Path.cwd())
        executed_commands.append(cleaned)
        if cleaned.startswith("ls") or cleaned.startswith("dir"):
            return "main.py\nREADME.md\nrequirements.txt"
        return ""

    agent.execute_command = fake_execute  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    response = await agent.process_request(
        ChatRequest(question="Can you show me the files in this folder?", conversation_id="ls-demo")
    )
    await agent.close()

    shell_info = response.api_results.get("shell_info", {}) if response.api_results else {}
    guardrails = {
        "auto_executed": bool(executed_commands),
        "ls_command": shell_info.get("command", "").startswith("ls"),
    }
    return {
        "response": response,
        "ledger": ledger,
        "executed_commands": executed_commands,
        "quality_checks": guardrails,
    }


async def run_conversation_memory_showcase() -> Dict[str, Any]:
    ledger: List[Dict[str, Any]] = []
    memory_note: Dict[str, Optional[str]] = {"note": None}

    previous_env = os.environ.get("CITE_AGENT_ARCHIVE_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CITE_AGENT_ARCHIVE_DIR"] = tmp
            agent = EnhancedNocturnalAgent()
            agent.archive = ConversationArchive(root=Path(tmp))
            agent.workflow.save_query_result = lambda *args, **kwargs: None

            def response_factory(query: str, _history: Any, api_results: Any) -> str:
                lower = query.lower()
                if "remember" in lower:
                    memory_note["note"] = query
                    return "Understood. I'll keep that in mind."
                if any(kw in lower for kw in ("earlier", "before", "previously")):
                    note = memory_note.get("note") or "(no prior note detected)"
                    return f"You previously mentioned: {note}"
                return "Synthetic backend summary"

            agent.call_backend_query = FakeBackend(ledger, response_factory=response_factory)  # type: ignore[assignment]

            async def backend_ready() -> Tuple[bool, str]:
                return True, ""

            agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

            first = await agent.process_request(
                ChatRequest(
                    question="Please remember that the final report lives in summary_v2.md.",
                    user_id="demo",
                    conversation_id="thread",
                )
            )
            archives_after_first = agent.archive.list_conversations()
            second = await agent.process_request(
                ChatRequest(
                    question="Which file did I say holds the final report earlier?",
                    user_id="demo",
                    conversation_id="thread",
                )
            )

            archive_entries = agent.archive.list_conversations()
            archive_files = [p.name for p in Path(tmp).glob("*.json")]
            await agent.close()

            guardrails = {
                "memory_recorded": memory_note.get("note") is not None,
                "memory_recited": "summary_v2.md" in second.response,
                "archive_written": bool(archive_entries),
            }

            return {
                "first": first,
                "second": second,
                "ledger": ledger,
                "quality_checks": guardrails,
                "archive_entries": archive_entries,
                "archive_files": archive_files,
                "archive_root": str(Path(tmp)),
                "after_first": archives_after_first,
            }
    finally:
        if previous_env is not None:
            os.environ["CITE_AGENT_ARCHIVE_DIR"] = previous_env
        else:
            os.environ.pop("CITE_AGENT_ARCHIVE_DIR", None)


async def run_multi_hop_research_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    research_payload = {
        "results": [
            {
                "title": "Efficient Transformer Deployment",
                "year": 2024,
                "authors": ["Kim", "Lopez"],
                "doi": "10.5555/efficient.transformer",
            },
            {
                "title": "Inference Optimization Strategies",
                "year": 2023,
                "authors": ["Singh"],
                "doi": "10.5555/inference.optim",
            },
        ],
        "sources_tried": ["semantic_scholar", "openalex"],
    }
    finance_payload = {
        "financial": {
            "NVDA": {
                "revenue": {"value": 28000000000, "source": "FinSight Q2"},
                "netIncome": {"value": 9500000000, "source": "FinSight Q2"},
            }
        }
    }

    agent.call_backend_query = FakeBackend(
        ledger,
        response_factory=_multi_hop_response_factory(research_payload, finance_payload),
    )  # type: ignore[assignment]

    async def analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "mixed",
            "apis": ["archive", "finsight"],
            "confidence": 0.9,
            "analysis_mode": "mixed",
        }

    agent._analyze_request_type = analysis  # type: ignore[assignment]
    agent._plan_financial_request = lambda q, session_key=None: (["NVDA"], ["revenue", "netIncome"])  # type: ignore[assignment]

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    async def fake_search(query: str, limit: int = 5) -> Dict[str, Any]:
        return research_payload

    agent.search_academic_papers = fake_search  # type: ignore[assignment]

    async def fake_metrics(ticker: str, metrics: List[str]) -> Dict[str, Any]:
        return {
            metric: finance_payload["financial"][ticker][metric]
            for metric in metrics
        }

    agent.get_financial_metrics = fake_metrics  # type: ignore[assignment]

    response = await agent.process_request(
        ChatRequest(question="Combine the latest transformer research insights with NVDA financial performance.")
    )
    await agent.close()
    guardrails = {
        "mentions_revenue": _snippets_present(response.response, ["$28,000,000,000"]),
        "mentions_net_income": _snippets_present(response.response, ["$9,500,000,000"]),
        "mentions_papers": _snippets_present(response.response, ["Efficient Transformer Deployment"]),
    }
    return {"response": response, "ledger": ledger, "quality_checks": guardrails}


async def run_repo_refactor_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    insights = {
        "smells": ["duplicated logic", "lack of input validation"],
        "plan": "Extract helper functions into io_utils.py and add type checks for None inputs.",
    }

    agent.call_backend_query = FakeBackend(
        ledger,
        response_factory=_repo_refactor_response_factory(insights),
    )  # type: ignore[assignment]

    async def analysis(question: str) -> Dict[str, Any]:
        return {
            "type": "system",
            "apis": ["shell"],
            "confidence": 0.85,
            "analysis_mode": "mixed",
        }

    agent._analyze_request_type = analysis  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        module_path = tmp_path / "module.py"
        helper_path = tmp_path / "helpers.py"
        module_path.write_text(
            "def process(data):\n"
            "    if not data:\n"
            "        return []\n"
            "    cleaned = []\n"
            "    for item in data:\n"
            "        cleaned.append(item.strip())\n"
            "    return cleaned\n",
            encoding="utf-8",
        )
        helper_path.write_text(
            "# TODO: consolidate sanitization logic\n"
            "def sanitize(text):\n"
            "    return text.strip()\n",
            encoding="utf-8",
        )
        agent.file_context["current_cwd"] = str(tmp_path)

        def fake_execute(cmd: str) -> str:
            cleaned = cmd.strip()
            if cleaned == "pwd":
                return str(tmp_path)
            if cleaned.startswith("ls"):
                return "module.py\nhelpers.py"
            if "module.py" in cleaned:
                return module_path.read_text(encoding="utf-8")
            if "helpers.py" in cleaned:
                return helper_path.read_text(encoding="utf-8")
            return ""

        agent.execute_command = fake_execute  # type: ignore[assignment]

        original_read = agent.read_file

        def refactor_read(path: str, offset: int = 0, limit: int = 2000) -> str:
            target = Path(path)
            if not target.is_absolute():
                target = tmp_path / path
            return original_read(str(target), offset=offset, limit=limit)

        agent.read_file = refactor_read  # type: ignore[assignment]

        response = await agent.process_request(
            ChatRequest(
                question="Review the current module implementation and outline a refactor plan to reduce duplication.",
            )
        )
    await agent.close()
    guardrails = {
        "mentions_smells": _snippets_present(response.response, insights["smells"]),
        "mentions_plan": insights["plan"] in response.response,
    }
    return {"response": response, "ledger": ledger, "refactor_insights": insights, "quality_checks": guardrails}


async def run_workspace_grounding_showcase() -> Dict[str, Any]:
    agent = EnhancedNocturnalAgent()
    agent.workflow.save_query_result = lambda *args, **kwargs: None
    ledger: List[Dict[str, Any]] = []

    def _grounding_factory(query: str, _history: Any, api_results: Any) -> str:
        lower = query.lower()
        if '"use_web_search"' in query or "use_web_search" in lower:
            return json.dumps({"use_web_search": False, "reason": "Workspace context is local"})
        if "shell command planner" in lower:
            return json.dumps(
                {
                    "action": "execute",
                    "command": "pwd",
                    "reason": "Report the current working directory",
                    "updates_context": False,
                }
            )
        shell_output = api_results.get("shell_info", {}).get("output", "").strip()
        listing_hint = "README.md, data.csv, notes.txt"
        if shell_output:
            return (
                f"We are working inside {shell_output}. "
                f'I can see key files such as {listing_hint}.'
            )
        return "Workspace grounding complete."

    agent.call_backend_query = FakeBackend(ledger, response_factory=_grounding_factory)  # type: ignore[assignment]
    agent.shell_session = _StubShell()

    async def backend_ready() -> Tuple[bool, str]:
        return True, ""

    agent._ensure_backend_ready = backend_ready  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "README.md").write_text("# Sample Project\nSome details here.", encoding="utf-8")
        (tmp_path / "data.csv").write_text("col1,col2\n1,2\n3,4\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("Remember to cite all sources.", encoding="utf-8")

        def fake_execute(cmd: str) -> str:
            cleaned = cmd.strip()
            if cleaned == "pwd":
                return str(tmp_path)
            if cleaned.startswith("ls"):
                return "README.md\ndata.csv\nnotes.txt"
            return ""

        agent.execute_command = fake_execute  # type: ignore[assignment]
        agent.file_context["current_cwd"] = str(tmp_path)

        response = await agent.process_request(
            ChatRequest(
                question="Where are we right now? Summarize the workspace.",
            )
        )
    await agent.close()

    guardrails = {
        "mentions_directory": str(tmp_path) in response.response,
        "mentions_files": all(name in response.response for name in ("README.md", "data.csv", "notes.txt")),
    }

    return {"response": response, "ledger": ledger, "quality_checks": guardrails}


SCENARIOS: List[Tuple[str, Any]] = [
    ("finance", run_finance_showcase),
    ("file_ops", run_local_file_showcase),
    ("research", run_research_showcase),
    ("archive_resume", run_archive_resume_showcase),
    ("ambiguous", run_ambiguous_query_showcase),
    ("data_analysis", run_data_analysis_showcase),
    ("repo_overview", run_repo_overview_showcase),
    ("data_pipeline", run_data_pipeline_showcase),
    ("self_service_shell", run_self_service_shell_showcase),
    ("conversation_memory", run_conversation_memory_showcase),
    ("multi_hop_research", run_multi_hop_research_showcase),
    ("repo_refactor", run_repo_refactor_showcase),
    ("workspace_grounding", run_workspace_grounding_showcase),
]


def _aggregate_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    total_elapsed = 0.0
    scenario_count = 0
    guard_total = 0
    guard_pass = 0
    tool_counter: Counter[str] = Counter()

    def _count_tools(response: Optional[ChatResponse]) -> None:
        if not response:
            return
        for tool in response.tools_used:
            tool_counter[tool] += 1

    for name, payload in results.items():
        if name.startswith("_"):
            continue
        scenario_count += 1
        total_elapsed += float(payload.get("elapsed_seconds", 0.0))

        _count_tools(payload.get("response"))
        _count_tools(payload.get("response_first"))
        _count_tools(payload.get("response_second"))

        quality = payload.get("quality_checks")
        if quality:
            guard_total += 1
            if all(quality.values()):
                guard_pass += 1

    guardrail_pass_rate = guard_pass / guard_total if guard_total else 1.0

    return {
        "scenario_count": scenario_count,
        "total_elapsed": total_elapsed,
        "guardrail_pass_rate": guardrail_pass_rate,
        "tool_usage": dict(tool_counter),
    }


async def execute_scenarios(filter_names: Optional[List[str]] = None) -> Dict[str, Any]:
    selected = [(name, fn) for name, fn in SCENARIOS if not filter_names or name in filter_names]
    results: Dict[str, Any] = {}
    for name, runner in selected:
        start = time.perf_counter()
        payload = await runner()
        payload["elapsed_seconds"] = time.perf_counter() - start
        results[name] = payload
    results["_metrics"] = _aggregate_metrics(results)
    return results


def _serialise_response(resp: ChatResponse) -> Dict[str, Any]:
    return {
        "response": resp.response,
        "tools_used": resp.tools_used,
        "confidence": resp.confidence_score,
        "error": resp.error_message,
    }


def _serialise_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    serialised: Dict[str, Any] = {k: v for k, v in payload.items() if k not in {"response", "response_first", "response_second"}}
    if "response" in payload:
        serialised["response"] = _serialise_response(payload["response"])
    if "response_first" in payload:
        serialised["response_first"] = _serialise_response(payload["response_first"])
    if "response_second" in payload:
        serialised["response_second"] = _serialise_response(payload["response_second"])
    return serialised


def _render_text(results: Dict[str, Any]) -> None:
    metrics = results.get("_metrics")
    for name, payload in results.items():
        if name.startswith("_"):
            continue
        print(f"\n=== Scenario: {name} ===")
        if "response" in payload:
            print(payload["response"].response)
            print("Tools used:", payload["response"].tools_used)
        if "response_second" in payload:
            print("Second response:", payload["response_second"].response)
            snippet = payload.get("archive_context", "")
            print("Archive context snippet:", snippet[:160] + ("..." if len(snippet) > 160 else ""))
            print("Archive files:", payload.get("archive_files", []))
            print("Context after first request:", payload.get("archive_context_first", "")[:160])
        if "finance_calls" in payload:
            print("Finance API calls:", payload["finance_calls"])
        print("Backend ledger entries:")
        ledger = payload.get("ledger") or payload.get("ledger_second", [])
        for entry in ledger:
            print("  →", entry)
        print(f"Elapsed: {payload['elapsed_seconds']:.3f}s")
        quality = payload.get("quality_checks")
        if quality:
            all_pass = all(quality.values())
            status = "PASS" if all_pass else "CHECK"
            print(f"Quality guards ({status}): {quality}")
    if metrics:
        print("\n=== Metrics Summary ===")
        print(f"Scenarios: {metrics['scenario_count']}")
        print(f"Total elapsed: {metrics['total_elapsed']:.3f}s")
        print(f"Guardrail pass rate: {metrics['guardrail_pass_rate']:.2%}")
        print(f"Tool usage: {metrics['tool_usage']}")


async def _main_async(args: argparse.Namespace) -> None:
    results = await execute_scenarios(args.only)

    if args.json:
        Path(args.json).write_text(json.dumps({k: _serialise_payload(v) for k, v in results.items()}, indent=2))
        print(f"JSON report written to {args.json}")

    if args.transcript or not args.json:
        _render_text(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Cite-Agent autonomy scenarios")
    parser.add_argument("--json", type=Path, help="Write results to JSON file")
    parser.add_argument("--no-transcript", dest="transcript", action="store_false", help="Skip textual transcript output")
    parser.add_argument("--only", nargs="*", help="Run only specific scenarios (finance, file_ops, research, archive_resume, ambiguous, data_analysis)")
    parser.set_defaults(transcript=True)
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
