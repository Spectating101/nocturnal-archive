"""
Synthesis service - LLM integration
"""

import structlog
import re
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from src.models.paper import SynthesisResult, Paper

logger = structlog.get_logger(__name__)


class Synthesizer:
    """Research synthesis service using OpenAI"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
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
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert research synthesizer. Provide accurate, well-cited summaries of academic research."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse response
            synthesis_text = response.choices[0].message.content
            
            # Extract key findings and citations
            key_findings, citations_used = self._extract_findings_and_citations(
                synthesis_text, papers
            )
            
            # Count words
            word_count = len(synthesis_text.split())
            
            logger.info(
                "Synthesis completed",
                paper_count=len(papers),
                word_count=word_count,
                findings_count=len(key_findings)
            )
            
            return SynthesisResult(
                summary=synthesis_text,
                key_findings=key_findings,
                citations_used=citations_used,
                word_count=word_count,
                trace_id=""  # Will be set by the route handler
            )
        
        except Exception as e:
            logger.error("Synthesis failed", error=str(e), paper_ids=paper_ids)
            raise
    
    async def _fetch_papers(self, paper_ids: List[str]) -> List[Paper]:
        """Fetch papers by IDs (mock implementation)"""
        
        # TODO: Implement actual paper fetching from database
        # For now, return mock papers with realistic abstracts
        mock_papers = []
        
        mock_abstracts = [
            "This study demonstrates significant improvements in CRISPR base editing efficiency, achieving 95% editing rates in human cells with minimal off-target effects.",
            "We present a novel approach to reducing off-target effects in CRISPR editing through optimized guide RNA designs, showing 80% reduction in unintended edits.",
            "Our research reveals new insights into the molecular mechanisms of base editing, providing a foundation for more precise gene therapy applications."
        ]
        
        for i, paper_id in enumerate(paper_ids):
            mock_paper = Paper(
                id=paper_id,
                title=f"CRISPR Base Editing Study {i+1}",
                authors=[
                    {"name": f"Researcher {i+1}, A."},
                    {"name": f"Coauthor {i+1}, B."}
                ],
                year=2023,
                doi=f"10.1000/example.{i+1}",
                abstract=mock_abstracts[i % len(mock_abstracts)],
                citations_count=42 + i,
                open_access=True,
                pdf_url=f"https://example.com/paper{i+1}.pdf",
                source="openalex",
                venue="Nature",
                keywords=["CRISPR", "base editing", "gene therapy"],
                created_at=None,
                updated_at=None
            )
            mock_papers.append(mock_paper)
        
        return mock_papers
    
    def _build_synthesis_prompt(
        self,
        papers: List[Paper],
        max_words: int,
        focus: str,
        style: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Build synthesis prompt for LLM"""
        
        # Start with custom prompt if provided
        if custom_prompt:
            prompt = f"{custom_prompt}\n\n"
        else:
            prompt = ""
        
        # Add focus-specific instructions
        focus_instructions = {
            "key_findings": "Focus on the most important findings and results from each study.",
            "comprehensive": "Provide a comprehensive overview covering methodology, results, and implications.",
            "methodology": "Focus on the research methods and experimental approaches used.",
            "results": "Emphasize the key results and data from each study.",
            "discussion": "Focus on the implications, limitations, and future directions discussed."
        }
        
        prompt += f"Please synthesize the following research papers, focusing on {focus_instructions.get(focus, 'key findings')}.\n\n"
        
        # Add style instructions
        style_instructions = {
            "academic": "Write in a formal academic style suitable for research papers.",
            "technical": "Use technical language appropriate for researchers and practitioners.",
            "accessible": "Write in clear, accessible language for a general audience.",
            "concise": "Be concise and direct, avoiding unnecessary elaboration."
        }
        
        prompt += f"Style: {style_instructions.get(style, 'academic')}\n"
        prompt += f"Maximum word count: {max_words}\n\n"
        
        # Add paper abstracts
        prompt += "Papers to synthesize:\n\n"
        for i, paper in enumerate(papers, 1):
            prompt += f"[{i}] {paper.title}\n"
            prompt += f"Authors: {', '.join([author.name for author in paper.authors])}\n"
            prompt += f"Year: {paper.year}\n"
            if paper.abstract:
                prompt += f"Abstract: {paper.abstract}\n"
            prompt += "\n"
        
        # Add formatting instructions
        prompt += """
Please provide:
1. A comprehensive summary synthesizing the key findings
2. A list of specific key findings with citations in the format [1], [2], etc.
3. Use proper academic citations throughout

Format your response as:
SUMMARY: [Your synthesis here]

KEY FINDINGS:
- Finding 1 [1]
- Finding 2 [2]
- etc.
"""
        
        return prompt
    
    def _extract_findings_and_citations(
        self, synthesis_text: str, papers: List[Paper]
    ) -> tuple[List[str], Dict[str, str]]:
        """Extract key findings and citation mappings from synthesis text"""
        
        key_findings = []
        citations_used = {}
        
        # Split text into sections
        sections = synthesis_text.split("KEY FINDINGS:")
        if len(sections) > 1:
            findings_section = sections[1].strip()
            
            # Extract findings (lines starting with - or *)
            findings_lines = re.findall(r'[-*]\s*(.+?)(?=\n|$)', findings_section, re.MULTILINE)
            
            for finding in findings_lines:
                # Extract citation numbers
                citations = re.findall(r'\[(\d+)\]', finding)
                key_findings.append(finding.strip())
                
                # Map citations to paper IDs
                for citation_num in citations:
                    paper_index = int(citation_num) - 1
                    if 0 <= paper_index < len(papers):
                        citations_used[f"[{citation_num}]"] = papers[paper_index].id
        
        return key_findings, citations_used
