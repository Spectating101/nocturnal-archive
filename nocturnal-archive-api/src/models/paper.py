"""
Paper data models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author model"""
    name: str = Field(..., description="Author name")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    affiliation: Optional[str] = Field(None, description="Author affiliation")


class Paper(BaseModel):
    """Paper model"""
    id: str = Field(..., description="Unique paper identifier")
    title: str = Field(..., description="Paper title")
    authors: List[Author] = Field(..., description="List of authors")
    year: int = Field(..., description="Publication year")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    abstract: Optional[str] = Field(None, description="Paper abstract")
    citations_count: Optional[int] = Field(None, description="Number of citations")
    open_access: Optional[bool] = Field(None, description="Whether the paper is open access")
    pdf_url: Optional[str] = Field(None, description="Direct link to PDF")
    source: str = Field(..., description="Data source (openalex, pubmed, arxiv)")
    venue: Optional[str] = Field(None, description="Publication venue")
    keywords: Optional[List[str]] = Field(None, description="Keywords or tags")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class SearchResult(BaseModel):
    """Search result model"""
    papers: List[Paper] = Field(..., description="List of matching papers")
    count: int = Field(..., description="Number of papers returned")
    query_id: str = Field(..., description="Unique identifier for this search query")
    trace_id: str = Field(..., description="Request trace ID for debugging")


class CitationFormat(BaseModel):
    """Citation format model"""
    style: str = Field(..., description="Citation style (bibtex, apa, mla, etc.)")
    formatted: str = Field(..., description="Formatted citation")
    paper_id: str = Field(..., description="Paper ID this citation refers to")


class SynthesisResult(BaseModel):
    """Synthesis result model"""
    summary: str = Field(..., description="Synthesized summary")
    key_findings: List[str] = Field(..., description="Key findings with citations")
    citations_used: Dict[str, str] = Field(..., description="Mapping of citation numbers to paper IDs")
    word_count: int = Field(..., description="Actual word count of summary")
    trace_id: str = Field(..., description="Request trace ID for debugging")
