"""Fallback synthesizer used when the sophisticated engine is unavailable."""

from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


class Synthesizer:
    """Heuristic research synthesizer used as a safe fallback path."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def synthesize_papers(
        self,
        *,
        paper_ids: Iterable[str],
        max_words: int = 300,
        focus: Optional[str] = None,
        style: str = "academic",
        papers: Optional[List[Dict[str, Any]]] = None,
        original_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized = self._normalise_papers(list(paper_ids), papers or [])
        cache_key = self._cache_key(normalized, max_words, focus, style)

        async with self._lock:
            cached = self._cache.get(cache_key)
            if cached:
                cached["routing_metadata"]["cached"] = True
                return dict(cached)

        summary = self._compose_summary(normalized, max_words, focus, style)
        key_findings = self._extract_findings(normalized, max_items=5)
        citations = self._build_citations(normalized)
        confidence = self._estimate_confidence(normalized, key_findings, summary)
        relevance = self._estimate_relevance(summary, original_query)

        result = {
            "summary": summary,
            "key_findings": key_findings,
            "citations_used": citations,
            "word_count": len(summary.split()),
            "metadata": {
                "paper_sample_size": len(normalized),
                "confidence": confidence,
                "domain_alignment": self._infer_domain(normalized, focus or ""),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "routing_metadata": {
                "routing_decision": {
                    "model": "heuristic-fallback",
                    "provider": "local",
                    "complexity": "standard",
                    "strategy": "baseline_synthesizer",
                },
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                },
                "cached": False,
            },
        }
        if relevance is not None:
            result["relevance_score"] = relevance

        async with self._lock:
            self._cache[cache_key] = dict(result)
        return result

    # ------------------------------------------------------------------
    def _normalise_papers(self, paper_ids: List[str], provided: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        provided_map = {str(paper.get("id")): paper for paper in provided if paper.get("id")}
        normalized: List[Dict[str, Any]] = []
        for paper_id in paper_ids:
            payload = provided_map.get(str(paper_id)) or {}
            title = payload.get("title") or f"Paper {paper_id}"
            abstract = payload.get("abstract") or payload.get("summary") or self._placeholder_abstract(paper_id)
            keywords = payload.get("keywords") or payload.get("concepts") or []
            if isinstance(keywords, list) and keywords and isinstance(keywords[0], dict):
                keywords = [kw.get("display_name", "") for kw in keywords if isinstance(kw, dict)]
            normalized.append({
                "id": str(paper_id),
                "title": title,
                "abstract": abstract,
                "keywords": [kw for kw in keywords if kw],
                "year": payload.get("publication_year") or payload.get("year"),
                "authors": payload.get("authors", []),
                "reference": payload.get("url") or payload.get("doi") or f"https://openalex.org/{paper_id}",
            })
        return normalized

    def _compose_summary(self, papers: List[Dict[str, Any]], max_words: int, focus: Optional[str], style: str) -> str:
        if not papers:
            return "No eligible papers were provided for synthesis."

        focus_hint = f" Focus on {focus.replace('_', ' ')}." if focus else ""
        style_hint = f" Style: {style}." if style else ""
        intro = f"Synthesizing {len(papers)} papers.{focus_hint}{style_hint}"

        sentences: List[str] = [intro]
        for paper in papers:
            abstract = str(paper["abstract"])[:1000]
            bullet = self._first_sentence(abstract)
            if bullet:
                sentences.append(f"{paper['title']}: {bullet}")
        summary = " ".join(sentences)

        words = summary.split()
        if len(words) > max_words:
            summary = " ".join(words[:max_words]) + "..."
        return summary

    def _extract_findings(self, papers: List[Dict[str, Any]], *, max_items: int) -> List[str]:
        findings: List[str] = []
        for paper in papers:
            abstract = str(paper["abstract"])
            sentences = [s.strip() for s in abstract.split('.') if s.strip()]
            for sentence in sentences[:2]:
                if len(findings) >= max_items:
                    break
                findings.append(f"{paper['title']}: {sentence}.")
            if len(findings) >= max_items:
                break
        return findings

    def _build_citations(self, papers: List[Dict[str, Any]]) -> Dict[str, str]:
        citations: Dict[str, str] = {}
        for idx, paper in enumerate(papers, start=1):
            citations[f"[{idx}]"] = paper.get("reference")
        return citations

    def _estimate_confidence(self, papers: List[Dict[str, Any]], findings: List[str], summary: str) -> float:
        diversity = len({paper.get("title") for paper in papers})
        base = 0.5
        if diversity >= 5:
            base += 0.15
        if len(findings) >= 3:
            base += 0.1
        if len(summary.split()) > 150:
            base += 0.1
        return max(0.2, min(0.95, round(base, 3)))

    def _estimate_relevance(self, summary: str, query: Optional[str]) -> Optional[float]:
        if not summary or not query:
            return None
        tokens = {token.lower() for token in query.split() if len(token) > 3}
        if not tokens:
            return None
        summary_lower = summary.lower()
        matches = sum(1 for token in tokens if token in summary_lower)
        return round(matches / len(tokens), 3)

    def _infer_domain(self, papers: List[Dict[str, Any]], focus: str) -> str:
        keywords = {kw.lower() for paper in papers for kw in paper.get("keywords", [])}
        keywords.update(word.lower() for word in focus.split())
        if any(term in keywords for term in {"equity", "market", "finance", "stock"}):
            return "quant_finance"
        if any(term in keywords for term in {"polymer", "resin", "materials", "manufacturing"}):
            return "advanced_materials"
        if any(term in keywords for term in {"nlp", "language", "transformer"}):
            return "ai_research"
        return "general"

    def _first_sentence(self, text: str) -> str:
        sentence = text.split('. ')[0].strip()
        if len(sentence.split()) < 6:
            return text[:140].strip()
        return sentence if sentence.endswith('.') else sentence + '.'

    def _placeholder_abstract(self, paper_id: str) -> str:
        return (
            f"Paper {paper_id} contributes to the research conversation by providing "
            "structured insights, but a detailed abstract was not supplied."
        )

    def _cache_key(self, papers: List[Dict[str, Any]], max_words: int, focus: Optional[str], style: str) -> str:
        ids = ":".join(sorted(paper["id"] for paper in papers))
        return f"{ids}|{max_words}|{focus or ''}|{style}"


__all__ = ["Synthesizer"]
