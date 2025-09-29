"""
Unified routes for cross-module functionality
Provides endpoints that work across FinSight, Archive, and Assistant modules
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import structlog

from config.settings import Settings, get_settings
from services.groq_service import get_groq_service

logger = structlog.get_logger(__name__)
router = APIRouter()


class UnifiedSearchRequest(BaseModel):
    """Request model for unified search"""
    query: str
    modules: List[str] = ["finsight", "archive", "assistant"]
    max_results: int = 10
    user_id: Optional[str] = None


class UnifiedSearchResponse(BaseModel):
    """Response model for unified search"""
    query: str
    results: Dict[str, List[Dict[str, Any]]]
    total_results: int
    modules_searched: List[str]
    timestamp: str


class CrossModuleAnalysisRequest(BaseModel):
    """Request model for cross-module analysis"""
    financial_data: Optional[str] = None
    research_context: Optional[str] = None
    analysis_type: str = "comprehensive"
    user_id: Optional[str] = None


class CrossModuleAnalysisResponse(BaseModel):
    """Response model for cross-module analysis"""
    analysis: str
    insights: List[str]
    recommendations: List[str]
    data_sources: List[str]
    confidence_score: float
    timestamp: str


@router.get("/search")
async def unified_search(
    query: str = Query(..., description="Search query"),
    modules: str = Query("finsight,archive,assistant", description="Comma-separated modules to search"),
    max_results: int = Query(10, description="Maximum results per module"),
    user_id: Optional[str] = Query(None, description="User ID for tracking"),
    settings: Settings = Depends(get_settings)
) -> UnifiedSearchResponse:
    """Unified search across all enabled modules"""
    
    # Parse modules
    module_list = [m.strip() for m in modules.split(",") if m.strip()]
    
    # Filter to only enabled modules
    enabled_modules = [m for m in module_list if settings.is_module_enabled(m)]
    
    if not enabled_modules:
        raise HTTPException(status_code=400, detail="No enabled modules specified")
    
    results = {}
    total_results = 0
    
    # Search each module
    for module in enabled_modules:
        try:
            if module == "finsight":
                # Search financial data
                results[module] = await _search_finsight(query, max_results)
            elif module == "archive":
                # Search research papers
                results[module] = await _search_archive(query, max_results)
            elif module == "assistant":
                # Search R/SQL knowledge
                results[module] = await _search_assistant(query, max_results)
            
            total_results += len(results.get(module, []))
            
        except Exception as e:
            logger.warning(f"Search failed for module {module}: {e}")
            results[module] = []
    
    return UnifiedSearchResponse(
        query=query,
        results=results,
        total_results=total_results,
        modules_searched=enabled_modules,
        timestamp=datetime.now().isoformat()
    )


@router.post("/search", response_model=UnifiedSearchResponse)
async def unified_search_post(
    request: UnifiedSearchRequest,
    settings: Settings = Depends(get_settings)
) -> UnifiedSearchResponse:
    """Unified search with POST request"""
    
    # Filter to only enabled modules
    enabled_modules = [m for m in request.modules if settings.is_module_enabled(m)]
    
    if not enabled_modules:
        raise HTTPException(status_code=400, detail="No enabled modules specified")
    
    results = {}
    total_results = 0
    
    # Search each module
    for module in enabled_modules:
        try:
            if module == "finsight":
                results[module] = await _search_finsight(request.query, request.max_results)
            elif module == "archive":
                results[module] = await _search_archive(request.query, request.max_results)
            elif module == "assistant":
                results[module] = await _search_assistant(request.query, request.max_results)
            
            total_results += len(results.get(module, []))
            
        except Exception as e:
            logger.warning(f"Search failed for module {module}: {e}")
            results[module] = []
    
    return UnifiedSearchResponse(
        query=request.query,
        results=results,
        total_results=total_results,
        modules_searched=enabled_modules,
        timestamp=datetime.now().isoformat()
    )


@router.post("/analyze", response_model=CrossModuleAnalysisResponse)
async def cross_module_analysis(
    request: CrossModuleAnalysisRequest,
    settings: Settings = Depends(get_settings)
) -> CrossModuleAnalysisResponse:
    """Cross-module analysis combining financial and research data"""
    
    groq_service = get_groq_service()
    
    # Prepare analysis prompt
    analysis_prompt = f"""
    Perform a comprehensive {request.analysis_type} analysis combining the following data:
    
    """
    
    data_sources = []
    
    if request.financial_data:
        analysis_prompt += f"""
        FINANCIAL DATA:
        {request.financial_data}
        
        """
        data_sources.append("financial_data")
    
    if request.research_context:
        analysis_prompt += f"""
        RESEARCH CONTEXT:
        {request.research_context}
        
        """
        data_sources.append("research_context")
    
    analysis_prompt += """
    Please provide:
    1. A comprehensive analysis combining both data sources
    2. Key insights and patterns
    3. Actionable recommendations
    4. Confidence assessment
    
    Focus on practical, actionable insights that combine financial and research perspectives.
    """
    
    # Get analysis from Groq
    messages = [
        {
            "role": "system",
            "content": "You are an expert analyst who combines financial data with research insights to provide comprehensive analysis."
        },
        {
            "role": "user",
            "content": analysis_prompt
        }
    ]
    
    try:
        response = await groq_service.chat_completion(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=2000,
            user_id=request.user_id
        )
        
        # Parse response (simplified - in production, use more sophisticated parsing)
        content = response["content"]
        
        # Extract insights and recommendations (simplified parsing)
        insights = []
        recommendations = []
        
        # Simple parsing - in production, use more sophisticated NLP
        lines = content.split("\n")
        for line in lines:
            if "insight" in line.lower() or "finding" in line.lower():
                insights.append(line.strip())
            elif "recommend" in line.lower() or "suggest" in line.lower():
                recommendations.append(line.strip())
        
        # Calculate confidence score (simplified)
        confidence_score = 0.8 if len(data_sources) >= 2 else 0.6
        
        return CrossModuleAnalysisResponse(
            analysis=content,
            insights=insights[:5],  # Limit to 5 insights
            recommendations=recommendations[:5],  # Limit to 5 recommendations
            data_sources=data_sources,
            confidence_score=confidence_score,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Cross-module analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/dashboard")
async def unified_dashboard(
    user_id: Optional[str] = Query(None, description="User ID"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get unified dashboard data"""
    
    dashboard_data = {
        "modules": {},
        "recent_activity": [],
        "statistics": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Get module status
    for module in ["finsight", "archive", "assistant"]:
        if settings.is_module_enabled(module):
            dashboard_data["modules"][module] = {
                "enabled": True,
                "status": "healthy",  # TODO: Implement actual health checks
                "endpoints": f"/api/v1/{module}/*"
            }
        else:
            dashboard_data["modules"][module] = {
                "enabled": False,
                "status": "disabled"
            }
    
    # Get recent activity (simplified - in production, get from database)
    dashboard_data["recent_activity"] = [
        {
            "type": "search",
            "module": "unified",
            "query": "sample query",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Get statistics (simplified - in production, get from monitoring)
    dashboard_data["statistics"] = {
        "total_searches": 0,  # TODO: Get from database
        "total_analyses": 0,  # TODO: Get from database
        "active_users": 0,    # TODO: Get from database
        "api_calls_today": 0  # TODO: Get from monitoring
    }
    
    return dashboard_data


@router.get("/health")
async def unified_health_check(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Unified health check for all modules"""
    
    health_status = {
        "overall_status": "healthy",
        "modules": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Check each module
    for module in ["finsight", "archive", "assistant"]:
        if settings.is_module_enabled(module):
            # TODO: Implement actual health checks for each module
            health_status["modules"][module] = {
                "status": "healthy",
                "enabled": True,
                "last_check": datetime.now().isoformat()
            }
        else:
            health_status["modules"][module] = {
                "status": "disabled",
                "enabled": False
            }
    
    # Check overall health
    unhealthy_modules = [
        module for module, status in health_status["modules"].items()
        if status["enabled"] and status["status"] != "healthy"
    ]
    
    if unhealthy_modules:
        health_status["overall_status"] = "degraded"
        health_status["unhealthy_modules"] = unhealthy_modules
    
    return health_status


# Helper functions for module-specific searches
async def _search_finsight(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Search FinSight module"""
    # TODO: Implement actual FinSight search
    return [
        {
            "title": f"Financial data for {query}",
            "type": "financial_data",
            "relevance": 0.9,
            "source": "finsight"
        }
    ]


async def _search_archive(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Search Archive module"""
    # TODO: Implement actual Archive search
    return [
        {
            "title": f"Research paper about {query}",
            "type": "research_paper",
            "relevance": 0.8,
            "source": "archive"
        }
    ]


async def _search_assistant(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Search Assistant module"""
    # TODO: Implement actual Assistant search
    return [
        {
            "title": f"R/SQL help for {query}",
            "type": "code_example",
            "relevance": 0.7,
            "source": "assistant"
        }
    ]


# Import datetime for timestamps
from datetime import datetime
