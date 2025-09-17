"""
Citation formatting service
"""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.paper import Paper, Author
from src.models.request import FormatOptions

logger = structlog.get_logger(__name__)


class CitationFormatter:
    """Citation formatting service"""
    
    def __init__(self):
        self.formatters = {
            'bibtex': self._format_bibtex,
            'apa': self._format_apa,
            'mla': self._format_mla,
            'chicago': self._format_chicago,
            'harvard': self._format_harvard
        }
    
    async def format_papers(
        self,
        paper_ids: List[str],
        style: str,
        options: Optional[FormatOptions] = None
    ) -> str:
        """Format papers into citations"""
        
        if style not in self.formatters:
            raise ValueError(f"Unsupported citation style: {style}")
        
        # TODO: Fetch papers from database/cache
        # For now, we'll create mock papers
        papers = await self._fetch_papers(paper_ids)
        
        if not papers:
            raise ValueError("No papers found for the given IDs")
        
        # Format each paper
        formatted_citations = []
        for paper in papers:
            formatted = self.formatters[style](paper, options)
            formatted_citations.append(formatted)
        
        # Join citations
        if style == 'bibtex':
            return '\n\n'.join(formatted_citations)
        else:
            return '\n\n'.join(formatted_citations)
    
    async def _fetch_papers(self, paper_ids: List[str]) -> List[Paper]:
        """Fetch papers by IDs (mock implementation)"""
        
        # TODO: Implement actual paper fetching from database
        # For now, return mock papers
        mock_papers = []
        
        for i, paper_id in enumerate(paper_ids):
            mock_paper = Paper(
                id=paper_id,
                title=f"Sample Paper {i+1}",
                authors=[
                    Author(name="Smith, J.", orcid="0000-0000-0000-0000"),
                    Author(name="Doe, A.", orcid="0000-0000-0000-0001")
                ],
                year=2023,
                doi=f"10.1000/example.{i+1}",
                abstract="This is a sample abstract for testing purposes.",
                citations_count=42,
                open_access=True,
                pdf_url=f"https://example.com/paper{i+1}.pdf",
                source="openalex",
                venue="Nature",
                keywords=["sample", "test", "example"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_papers.append(mock_paper)
        
        return mock_papers
    
    def _format_bibtex(self, paper: Paper, options: Optional[FormatOptions] = None) -> str:
        """Format paper as BibTeX"""
        
        # Generate BibTeX key
        first_author = paper.authors[0].name.split(',')[0].lower() if paper.authors else "unknown"
        year = paper.year
        title_words = paper.title.split()[:3]
        title_key = "".join([word[0].lower() for word in title_words if word])
        bibtex_key = f"{first_author}{year}{title_key}"
        
        # Build BibTeX entry
        bibtex = f"@article{{{bibtex_key},\n"
        bibtex += f"  title={{{paper.title}}},\n"
        
        # Authors
        author_names = " and ".join([author.name for author in paper.authors])
        bibtex += f"  author={{{author_names}}},\n"
        
        # Journal/Venue
        if paper.venue:
            bibtex += f"  journal={{{paper.venue}}},\n"
        
        # Year
        bibtex += f"  year={{{paper.year}}},\n"
        
        # DOI
        if paper.doi:
            bibtex += f"  doi={{{paper.doi}}},\n"
        
        # Abstract (if requested)
        if options and options.include_abstract and paper.abstract:
            # Escape braces in abstract
            abstract = paper.abstract.replace("{", "\\{").replace("}", "\\}")
            bibtex += f"  abstract={{{abstract}}},\n"
        
        # Keywords (if requested)
        if options and options.include_keywords and paper.keywords:
            keywords = ", ".join(paper.keywords)
            bibtex += f"  keywords={{{keywords}}},\n"
        
        # URL (if requested and available)
        if options and options.include_url and paper.pdf_url:
            bibtex += f"  url={{{paper.pdf_url}}},\n"
        
        bibtex += "}"
        
        return bibtex
    
    def _format_apa(self, paper: Paper, options: Optional[FormatOptions] = None) -> str:
        """Format paper in APA style"""
        
        # Authors
        if len(paper.authors) == 1:
            authors = paper.authors[0].name
        elif len(paper.authors) == 2:
            authors = f"{paper.authors[0].name} & {paper.authors[1].name}"
        else:
            authors = f"{paper.authors[0].name}, et al."
        
        # Title
        title = paper.title
        if not title.endswith('.'):
            title += '.'
        
        # Journal
        journal = paper.venue or "Unknown Journal"
        
        # Year
        year = paper.year
        
        # DOI
        doi_part = f" https://doi.org/{paper.doi}" if paper.doi else ""
        
        # Build APA citation
        apa = f"{authors} ({year}). {title} {journal}.{doi_part}"
        
        return apa
    
    def _format_mla(self, paper: Paper, options: Optional[FormatOptions] = None) -> str:
        """Format paper in MLA style"""
        
        # Authors
        if len(paper.authors) == 1:
            authors = paper.authors[0].name
        elif len(paper.authors) == 2:
            authors = f"{paper.authors[0].name} and {paper.authors[1].name}"
        else:
            authors = f"{paper.authors[0].name}, et al."
        
        # Title
        title = f'"{paper.title}."'
        
        # Journal
        journal = paper.venue or "Unknown Journal"
        
        # Year
        year = paper.year
        
        # Build MLA citation
        mla = f"{authors}. {title} {journal}, {year}."
        
        return mla
    
    def _format_chicago(self, paper: Paper, options: Optional[FormatOptions] = None) -> str:
        """Format paper in Chicago style"""
        
        # Authors
        if len(paper.authors) == 1:
            authors = paper.authors[0].name
        elif len(paper.authors) == 2:
            authors = f"{paper.authors[0].name} and {paper.authors[1].name}"
        else:
            authors = f"{paper.authors[0].name} et al."
        
        # Title
        title = f'"{paper.title}."'
        
        # Journal
        journal = paper.venue or "Unknown Journal"
        
        # Year
        year = paper.year
        
        # Build Chicago citation
        chicago = f"{authors}. {title} {journal} ({year})."
        
        return chicago
    
    def _format_harvard(self, paper: Paper, options: Optional[FormatOptions] = None) -> str:
        """Format paper in Harvard style"""
        
        # Authors
        if len(paper.authors) == 1:
            authors = paper.authors[0].name
        elif len(paper.authors) == 2:
            authors = f"{paper.authors[0].name} & {paper.authors[1].name}"
        else:
            authors = f"{paper.authors[0].name} et al."
        
        # Title
        title = paper.title
        
        # Journal
        journal = paper.venue or "Unknown Journal"
        
        # Year
        year = paper.year
        
        # Build Harvard citation
        harvard = f"{authors} {year}, '{title}', {journal}."
        
        return harvard
