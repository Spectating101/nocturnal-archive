"""
Request models
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class SearchFilters(BaseModel):
    """Search filters model"""
    year_min: Optional[int] = Field(None, ge=1900, le=2030, description="Minimum publication year")
    year_max: Optional[int] = Field(None, ge=1900, le=2030, description="Maximum publication year")
    open_access: Optional[bool] = Field(None, description="Only return open access papers")
    min_citations: Optional[int] = Field(None, ge=0, description="Minimum number of citations")
    venue: Optional[str] = Field(None, description="Specific venue or journal")
    authors: Optional[List[str]] = Field(None, description="Filter by specific authors")


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    sources: List[str] = Field(["openalex"], description="Data sources to search")
    filters: Optional[SearchFilters] = Field(None, description="Search filters")
    
    @validator('sources')
    def validate_sources(cls, v):
        valid_sources = ['openalex', 'pubmed', 'arxiv']
        for source in v:
            if source not in valid_sources:
                raise ValueError(f"Invalid source: {source}. Must be one of {valid_sources}")
        return v


class FormatOptions(BaseModel):
    """Format options model"""
    include_abstract: bool = Field(False, description="Include abstract in formatted output")
    include_keywords: bool = Field(False, description="Include keywords in formatted output")
    include_url: bool = Field(True, description="Include URL/DOI in formatted output")


class FormatRequest(BaseModel):
    """Format request model"""
    paper_ids: List[str] = Field(..., min_items=1, max_items=50, description="List of paper IDs to format")
    style: str = Field(..., description="Citation style")
    options: Optional[FormatOptions] = Field(None, description="Formatting options")
    
    @validator('style')
    def validate_style(cls, v):
        valid_styles = ['bibtex', 'apa', 'mla', 'chicago', 'harvard']
        if v not in valid_styles:
            raise ValueError(f"Invalid style: {v}. Must be one of {valid_styles}")
        return v


class SynthesizeRequest(BaseModel):
    """Synthesize request model"""
    paper_ids: List[str] = Field(..., min_items=1, max_items=20, description="List of paper IDs to synthesize")
    max_words: int = Field(300, ge=100, le=2000, description="Maximum word count for synthesis")
    focus: str = Field("key_findings", description="Focus area for synthesis")
    style: str = Field("academic", description="Writing style")
    custom_prompt: Optional[str] = Field(None, max_length=1000, description="Custom synthesis prompt")
    papers: Optional[List[Dict[str, Any]]] = Field(None, description="Optional: full paper objects including abstracts")
    original_query: Optional[str] = Field(None, description="Optional: original user query to assess relevance of synthesis")
    
    @validator('focus')
    def validate_focus(cls, v):
        valid_focuses = ['key_findings', 'comprehensive', 'methodology', 'results', 'discussion']
        if v not in valid_focuses:
            raise ValueError(f"Invalid focus: {v}. Must be one of {valid_focuses}")
        return v
    
    @validator('style')
    def validate_style(cls, v):
        valid_styles = ['academic', 'technical', 'accessible', 'concise']
        if v not in valid_styles:
            raise ValueError(f"Invalid style: {v}. Must be one of {valid_styles}")
        return v

    @validator('papers')
    def validate_papers(cls, v):
        if v is None:
            return v
        for p in v:
            if 'id' not in p:
                raise ValueError("Each paper must include an 'id'")
            if not any(k in p for k in ['abstract', 'title']):
                raise ValueError("Each paper must include at least 'abstract' or 'title'")
        return v
