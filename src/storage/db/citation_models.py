#!/usr/bin/env python3
"""
Database models for citation storage and management
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class CitationFormat(str, Enum):
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    BIBTEX = "bibtex"

class Citation(BaseModel):
    """Citation database model"""
    citation_id: str = Field(..., description="Unique citation identifier")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: int = Field(..., description="Publication year")
    journal: Optional[str] = Field(None, description="Journal name")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    url: Optional[str] = Field(None, description="Paper URL")
    volume: Optional[str] = Field(None, description="Journal volume")
    issue: Optional[str] = Field(None, description="Journal issue")
    pages: Optional[str] = Field(None, description="Page numbers")
    publisher: Optional[str] = Field(None, description="Publisher")
    abstract: Optional[str] = Field(None, description="Abstract")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    citation_count: int = Field(default=0, description="Number of citations received")
    source_paper_id: Optional[str] = Field(None, description="ID of paper that cites this")
    confidence_score: float = Field(default=1.0, description="Confidence in citation data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CitedFinding(BaseModel):
    """Cited finding database model"""
    finding_id: str = Field(..., description="Unique finding identifier")
    text: str = Field(..., description="Finding text")
    citation_id: str = Field(..., description="Reference to citation")
    confidence_score: float = Field(default=1.0, description="Confidence in finding")
    context: Optional[str] = Field(None, description="Context of finding")
    methodology: Optional[str] = Field(None, description="Methodology used")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CitationNetwork(BaseModel):
    """Citation network database model"""
    network_id: str = Field(..., description="Unique network identifier")
    paper_id: str = Field(..., description="Central paper ID")
    references: List[str] = Field(default_factory=list, description="List of reference citation IDs")
    citations: List[str] = Field(default_factory=list, description="List of citing paper citation IDs")
    related_papers: List[str] = Field(default_factory=list, description="List of related paper citation IDs")
    network_depth: int = Field(default=2, description="Depth of network exploration")
    total_connections: int = Field(default=0, description="Total number of connections")
    influence_score: float = Field(default=0.0, description="Influence score")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CitationAnalytics(BaseModel):
    """Citation analytics database model"""
    analytics_id: str = Field(..., description="Unique analytics identifier")
    paper_ids: List[str] = Field(default_factory=list, description="List of analyzed paper IDs")
    total_citations: int = Field(default=0, description="Total number of citations")
    year_range: Dict[str, int] = Field(default_factory=dict, description="Year range statistics")
    citation_impact: Dict[str, float] = Field(default_factory=dict, description="Citation impact metrics")
    journal_distribution: Dict[str, int] = Field(default_factory=dict, description="Journal distribution")
    author_analysis: Dict[str, Any] = Field(default_factory=dict, description="Author analysis")
    academic_credibility_score: float = Field(default=0.0, description="Academic credibility score")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CitationExport(BaseModel):
    """Citation export database model"""
    export_id: str = Field(..., description="Unique export identifier")
    synthesis_id: str = Field(..., description="Reference to synthesis")
    format_type: CitationFormat = Field(..., description="Export format")
    content: str = Field(..., description="Exported content")
    citation_count: int = Field(default=0, description="Number of citations exported")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CitationQuery(BaseModel):
    """Citation query model for database operations"""
    paper_id: Optional[str] = Field(None, description="Filter by paper ID")
    author: Optional[str] = Field(None, description="Filter by author")
    journal: Optional[str] = Field(None, description="Filter by journal")
    year_from: Optional[int] = Field(None, description="Filter by year from")
    year_to: Optional[int] = Field(None, description="Filter by year to")
    min_citations: Optional[int] = Field(None, description="Minimum citation count")
    limit: int = Field(default=100, description="Maximum number of results")
    offset: int = Field(default=0, description="Result offset")

class CitationNetworkQuery(BaseModel):
    """Citation network query model"""
    paper_id: str = Field(..., description="Central paper ID")
    depth: int = Field(default=2, description="Network depth")
    include_references: bool = Field(default=True, description="Include references")
    include_citations: bool = Field(default=True, description="Include citations")
    min_citation_count: int = Field(default=0, description="Minimum citation count for inclusion")

class CitationAnalyticsQuery(BaseModel):
    """Citation analytics query model"""
    paper_ids: List[str] = Field(default_factory=list, description="List of paper IDs to analyze")
    include_networks: bool = Field(default=True, description="Include network analysis")
    include_temporal: bool = Field(default=True, description="Include temporal analysis")
    include_impact: bool = Field(default=True, description="Include impact analysis")
