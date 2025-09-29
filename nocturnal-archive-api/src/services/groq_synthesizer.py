"""
Groq-powered synthesis service - replaces OpenAI
"""

import structlog
import re
from typing import List, Dict, Any, Optional
from groq import Groq

from src.models.paper import SynthesisResult, Paper

logger = structlog.get_logger(__name__)


class GroqSynthesizer:
    """Research synthesis service using Groq"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Groq's best model
        self.max_tokens = 1000
        self.temperature = 0.7
    
    async def synthesize_papers(
        self,
        paper_ids: List[str],
        max_words: int = 300,
        focus: str = "key_findings",
        style: str = "academic",
        custom_prompt: Optional[str] = None
    ) -> SynthesisResult:
        """Synthesize findings across multiple papers"""
        
        try:
            # TODO: Fetch papers from database/cache
            papers = await self._fetch_papers(paper_ids)
            
            if not papers:
                raise ValueError("No papers found for the given IDs")
            
            # Build synthesis prompt
            prompt = self._build_synthesis_prompt(
                papers, max_words, focus, style, custom_prompt
            )
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert research synthesizer. Provide accurate, well-cited summaries of academic research."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            synthesis_text = response.choices[0].message.content
            
            # Extract key findings and citations
            key_findings = self._extract_key_findings(synthesis_text)
            citations = self._extract_citations(synthesis_text, papers)
            
            return SynthesisResult(
                synthesis_text=synthesis_text,
                key_findings=key_findings,
                citations=citations,
                paper_count=len(papers),
                word_count=len(synthesis_text.split()),
                focus_area=focus,
                style=style
            )
            
        except Exception as e:
            logger.error("Synthesis failed", error=str(e), paper_ids=paper_ids)
            raise
    
    async def _fetch_papers(self, paper_ids: List[str]) -> List[Paper]:
        """Fetch papers from database/cache"""
        # TODO: Implement actual paper fetching
        # For now, return mock papers
        papers = []
        for i, paper_id in enumerate(paper_ids):
            papers.append(Paper(
                id=paper_id,
                title=f"Research Paper {i+1}",
                authors=["Author 1", "Author 2"],
                abstract=f"Abstract for paper {i+1}",
                content=f"Full content for paper {i+1}",
                citations=[],
                keywords=["research", "analysis"],
                publication_date="2024-01-01"
            ))
        return papers
    
    def _build_synthesis_prompt(
        self,
        papers: List[Paper],
        max_words: int,
        focus: str,
        style: str,
        custom_prompt: Optional[str]
    ) -> str:
        """Build synthesis prompt"""
        
        if custom_prompt:
            base_prompt = custom_prompt
        else:
            base_prompt = f"""Synthesize the following research papers focusing on {focus} in {style} style.
            
            Requirements:
            - Maximum {max_words} words
            - Focus on {focus}
            - Use {style} writing style
            - Include specific citations
            - Highlight key findings and insights
            - Identify gaps or contradictions
            """
        
        # Add paper information
        papers_text = ""
        for i, paper in enumerate(papers, 1):
            papers_text += f"\n\nPaper {i}: {paper.title}\n"
            papers_text += f"Authors: {', '.join(paper.authors)}\n"
            papers_text += f"Abstract: {paper.abstract}\n"
            papers_text += f"Keywords: {', '.join(paper.keywords)}\n"
        
        return f"{base_prompt}\n\nPapers to synthesize:{papers_text}"
    
    def _extract_key_findings(self, synthesis_text: str) -> List[str]:
        """Extract key findings from synthesis"""
        # Simple extraction - look for bullet points or numbered lists
        findings = []
        
        # Look for bullet points
        bullet_pattern = r'[•\-\*]\s*(.+?)(?=\n|$)'
        bullets = re.findall(bullet_pattern, synthesis_text, re.MULTILINE)
        findings.extend(bullets)
        
        # Look for numbered lists
        number_pattern = r'\d+\.\s*(.+?)(?=\n|$)'
        numbers = re.findall(number_pattern, synthesis_text, re.MULTILINE)
        findings.extend(numbers)
        
        # If no structured findings, split by sentences
        if not findings:
            sentences = synthesis_text.split('. ')
            findings = [s.strip() for s in sentences[:5]]  # First 5 sentences
        
        return findings[:10]  # Limit to 10 findings
    
    def _extract_citations(self, synthesis_text: str, papers: List[Paper]) -> List[Dict[str, str]]:
        """Extract citations from synthesis"""
        citations = []
        
        for paper in papers:
            # Check if paper title is mentioned in synthesis
            if paper.title.lower() in synthesis_text.lower():
                citations.append({
                    "title": paper.title,
                    "authors": ", ".join(paper.authors),
                    "id": paper.id,
                    "type": "research_paper"
                })
        
        return citations


# Backward compatibility - create alias
Synthesizer = GroqSynthesizer
