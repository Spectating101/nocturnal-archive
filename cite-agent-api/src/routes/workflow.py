"""
Workflow Integration API endpoints
Reduces context switching for scholars
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel

from src.services.workflow_integration import WorkflowIntegration
from src.middleware.api_auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])

# Initialize workflow integration
workflow = WorkflowIntegration()

class SavePaperRequest(BaseModel):
    paper: dict
    tags: Optional[List[str]] = []
    notes: Optional[str] = ""

class ExportRequest(BaseModel):
    paper_ids: List[str]
    format: str  # "bibtex", "markdown", "json"
    filename: Optional[str] = None

class CitationSuggestionRequest(BaseModel):
    paper: dict
    context: Optional[str] = ""

@router.post("/save-paper")
async def save_paper(
    request: SavePaperRequest,
    user_id: str = Depends(get_current_user)
):
    """Save a paper to user's library"""
    try:
        paper_id = workflow.save_paper_to_library(
            paper=request.paper,
            user_id=user_id
        )
        
        return {
            "success": True,
            "paper_id": paper_id,
            "message": "Paper saved to library"
        }
    except Exception as e:
        logger.error("Error saving paper", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to save paper")

@router.get("/library")
async def get_library(
    user_id: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """Get user's saved paper library"""
    try:
        library = workflow.get_user_library(user_id)
        return {
            "success": True,
            "papers": library[:limit],
            "total": len(library)
        }
    except Exception as e:
        logger.error("Error getting library", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to get library")

@router.get("/search-library")
async def search_library(
    query: str = Query(..., min_length=1),
    user_id: str = Depends(get_current_user)
):
    """Search user's saved paper library"""
    try:
        results = workflow.search_library(user_id, query)
        return {
            "success": True,
            "results": results,
            "query": query,
            "count": len(results)
        }
    except Exception as e:
        logger.error("Error searching library", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to search library")

@router.post("/export")
async def export_papers(
    request: ExportRequest,
    user_id: str = Depends(get_current_user)
):
    """Export papers in various formats"""
    try:
        # Get papers from library
        library = workflow.get_user_library(user_id)
        papers_to_export = []
        
        for paper_data in library:
            if paper_data.get('id') in request.paper_ids:
                papers_to_export.append(paper_data.get('paper', {}))
        
        if not papers_to_export:
            raise HTTPException(status_code=404, detail="No papers found to export")
        
        # Export based on format
        if request.format == "bibtex":
            filename = request.filename or f"citations_{user_id}.bib"
            file_path = workflow.export_to_bibtex(papers_to_export, filename)
        elif request.format == "markdown":
            filename = request.filename or f"papers_{user_id}.md"
            file_path = workflow.export_to_markdown(papers_to_export, filename)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting papers", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to export papers")

@router.post("/citation-suggestions")
async def get_citation_suggestions(
    request: CitationSuggestionRequest,
    user_id: str = Depends(get_current_user)
):
    """Get citation suggestions for a paper"""
    try:
        suggestions = workflow.generate_citation_suggestions(request.paper)
        return {
            "success": True,
            "suggestions": suggestions,
            "paper_title": request.paper.get('title', 'Unknown Title')
        }
    except Exception as e:
        logger.error("Error generating suggestions", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")

@router.get("/session-history")
async def get_session_history(
    user_id: str = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """Get user's recent session history"""
    try:
        sessions = workflow.get_session_history(user_id, limit)
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error("Error getting session history", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to get session history")

@router.post("/save-session")
async def save_session(
    query: str,
    response: dict,
    user_id: str = Depends(get_current_user)
):
    """Save a query and response to session history"""
    try:
        session_id = workflow.save_session_history(user_id, query, response)
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session saved"
        }
    except Exception as e:
        logger.error("Error saving session", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to save session")

@router.get("/citation-network")
async def get_citation_network(
    user_id: str = Depends(get_current_user)
):
    """Get citation network data for visualization"""
    try:
        library = workflow.get_user_library(user_id)
        papers = [paper_data.get('paper', {}) for paper_data in library]
        network = workflow.create_citation_network(papers)
        
        return {
            "success": True,
            "network": network,
            "paper_count": len(papers)
        }
    except Exception as e:
        logger.error("Error creating citation network", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to create citation network")

@router.get("/stats")
async def get_workflow_stats(
    user_id: str = Depends(get_current_user)
):
    """Get user's workflow statistics"""
    try:
        library = workflow.get_user_library(user_id)
        sessions = workflow.get_session_history(user_id, 100)
        
        # Calculate stats
        total_papers = len(library)
        total_sessions = len(sessions)
        
        # Papers by year
        papers_by_year = {}
        for paper_data in library:
            paper = paper_data.get('paper', {})
            year = paper.get('year', 'Unknown')
            papers_by_year[year] = papers_by_year.get(year, 0) + 1
        
        # Most used tools
        tools_used = {}
        for session in sessions:
            for tool in session.get('tools_used', []):
                tools_used[tool] = tools_used.get(tool, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_papers": total_papers,
                "total_sessions": total_sessions,
                "papers_by_year": papers_by_year,
                "most_used_tools": dict(sorted(tools_used.items(), key=lambda x: x[1], reverse=True)[:5])
            }
        }
    except Exception as e:
        logger.error("Error getting workflow stats", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to get workflow stats")