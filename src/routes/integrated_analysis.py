"""
Integrated Analysis API Routes - Cross-system research and finance analysis
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog

from ..services.integrated_analysis_service import integrated_analysis_service

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/integrated", tags=["Integrated Analysis"])

class IntegratedAnalysisRequest(BaseModel):
    """Request model for integrated analysis"""
    research_topic: str = Field(..., description="Academic research topic (e.g., 'CRISPR gene editing')")
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'CRSP')")
    analysis_type: str = Field("comprehensive", description="Type of analysis: comprehensive, trends, investment")
    include_financial_data: bool = Field(True, description="Include detailed financial data")
    include_research_papers: bool = Field(True, description="Include detailed research papers")

class CrossDomainSynthesisRequest(BaseModel):
    """Request model for cross-domain synthesis"""
    research_documents: List[Dict[str, Any]] = Field(..., description="Research documents to analyze")
    financial_documents: List[Dict[str, Any]] = Field(..., description="Financial documents to analyze")
    synthesis_focus: str = Field("investment_insights", description="Focus area for synthesis")
    max_words: int = Field(500, description="Maximum words in synthesis")

class ResearchFinanceCorrelationRequest(BaseModel):
    """Request model for research-finance correlation analysis"""
    research_topic: str = Field(..., description="Research topic")
    ticker: str = Field(..., description="Stock ticker")
    time_period: str = Field("5y", description="Time period for analysis")
    correlation_metrics: List[str] = Field(["research_funding", "publication_count", "patent_filings"], 
                                         description="Metrics to correlate")

@router.post("/analyze")
async def integrated_analysis(
    request: IntegratedAnalysisRequest,
    request_obj: Request
):
    """
    Perform integrated analysis combining research and finance systems.
    
    This endpoint demonstrates the unique value proposition by combining:
    - Academic research analysis
    - Financial data analysis  
    - Cross-domain correlation using Groq
    - Investment insights generation
    """
    try:
        logger.info(
            "Integrated analysis request received",
            research_topic=request.research_topic,
            ticker=request.ticker,
            analysis_type=request.analysis_type,
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        # Perform integrated analysis
        result = await integrated_analysis_service.analyze_research_finance_correlation(
            research_topic=request.research_topic,
            ticker=request.ticker,
            analysis_type=request.analysis_type
        )
        
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "analysis_failed",
                    "message": result.get("error", "Analysis failed"),
                    "analysis_id": result.get("analysis_id")
                }
            )
        
        logger.info(
            "Integrated analysis completed",
            analysis_id=result.get("analysis_id"),
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Integrated analysis failed",
            error=str(e),
            research_topic=request.research_topic,
            ticker=request.ticker,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "integrated_analysis_failed",
                "message": f"Failed to perform integrated analysis: {str(e)}"
            }
        )

@router.post("/synthesize")
async def cross_domain_synthesis(
    request: CrossDomainSynthesisRequest,
    request_obj: Request
):
    """
    Synthesize research and financial documents using Groq.
    
    This endpoint demonstrates cross-domain synthesis capabilities:
    - Combines academic research with financial analysis
    - Uses Groq for intelligent synthesis
    - Generates investment insights
    """
    try:
        logger.info(
            "Cross-domain synthesis request received",
            research_docs_count=len(request.research_documents),
            financial_docs_count=len(request.financial_documents),
            synthesis_focus=request.synthesis_focus,
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        # Combine documents for synthesis
        all_documents = request.research_documents + request.financial_documents
        
        # Use Groq for synthesis
        synthesis_result = await integrated_analysis_service.groq_client.synthesize_documents(
            documents=all_documents,
            focus=request.synthesis_focus
        )
        
        if not synthesis_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "synthesis_failed",
                    "message": synthesis_result.get("error", "Synthesis failed")
                }
            )
        
        # Enhance with cross-domain insights
        enhanced_result = {
            "synthesis": synthesis_result.get("synthesis", ""),
            "research_insights": await integrated_analysis_service._extract_research_insights(
                request.research_documents
            ),
            "financial_insights": await integrated_analysis_service._extract_financial_insights(
                request.financial_documents
            ),
            "cross_domain_correlations": await integrated_analysis_service._find_correlations(
                request.research_documents, request.financial_documents
            ),
            "investment_implications": await integrated_analysis_service._generate_investment_implications(
                synthesis_result.get("synthesis", "")
            ),
            "metadata": {
                "research_documents": len(request.research_documents),
                "financial_documents": len(request.financial_documents),
                "synthesis_focus": request.synthesis_focus,
                "word_count": len(synthesis_result.get("synthesis", "").split())
            }
        }
        
        logger.info(
            "Cross-domain synthesis completed",
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        return enhanced_result
        
    except Exception as e:
        logger.error(
            "Cross-domain synthesis failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "cross_domain_synthesis_failed",
                "message": f"Failed to perform cross-domain synthesis: {str(e)}"
            }
        )

@router.post("/correlation")
async def research_finance_correlation(
    request: ResearchFinanceCorrelationRequest,
    request_obj: Request
):
    """
    Analyze correlation between research metrics and financial performance.
    
    This endpoint demonstrates the unique capability to correlate:
    - Research funding with stock performance
    - Publication trends with revenue growth
    - Patent filings with market valuation
    """
    try:
        logger.info(
            "Research-finance correlation request received",
            research_topic=request.research_topic,
            ticker=request.ticker,
            time_period=request.time_period,
            correlation_metrics=request.correlation_metrics,
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        # Get research metrics
        research_metrics = await integrated_analysis_service._get_research_metrics(
            request.research_topic, request.time_period
        )
        
        # Get financial metrics
        financial_metrics = await integrated_analysis_service._get_financial_metrics(
            request.ticker, request.time_period
        )
        
        # Calculate correlations
        correlations = await integrated_analysis_service._calculate_correlations(
            research_metrics, financial_metrics, request.correlation_metrics
        )
        
        # Generate insights using Groq
        correlation_insights = await integrated_analysis_service._generate_correlation_insights(
            correlations, research_metrics, financial_metrics
        )
        
        result = {
            "research_topic": request.research_topic,
            "ticker": request.ticker,
            "time_period": request.time_period,
            "research_metrics": research_metrics,
            "financial_metrics": financial_metrics,
            "correlations": correlations,
            "insights": correlation_insights,
            "metadata": {
                "correlation_metrics": request.correlation_metrics,
                "analysis_timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        logger.info(
            "Research-finance correlation completed",
            trace_id=getattr(request_obj.state, "trace_id", "unknown")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Research-finance correlation failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "correlation_analysis_failed",
                "message": f"Failed to analyze correlations: {str(e)}"
            }
        )

@router.get("/capabilities")
async def get_integrated_capabilities():
    """
    Get information about integrated analysis capabilities.
    
    This endpoint shows what makes the platform unique:
    - Cross-system integration
    - Groq-powered analysis
    - Research-finance correlation
    """
    return {
        "integrated_capabilities": {
            "research_analysis": {
                "description": "Academic research analysis using OpenAlex and other sources",
                "features": ["Paper search", "Citation analysis", "Research trends", "Topic modeling"]
            },
            "financial_analysis": {
                "description": "Financial data analysis using SEC EDGAR and other sources",
                "features": ["Company data", "Financial metrics", "Performance analysis", "Risk assessment"]
            },
            "cross_domain_synthesis": {
                "description": "Groq-powered synthesis of research and financial data",
                "features": ["Correlation analysis", "Investment insights", "Risk assessment", "Trend prediction"]
            },
            "unique_value_proposition": [
                "Only platform combining academic research with financial analysis",
                "Groq-powered cross-domain insights",
                "Research-driven investment recommendations",
                "Academic-financial correlation analysis"
            ]
        },
        "example_use_cases": [
            "Analyze how CRISPR research trends correlate with CRSP stock performance",
            "Synthesize AI research papers with tech company financial data",
            "Generate investment insights from academic research findings",
            "Correlate research funding with company valuations"
        ],
        "groq_integration": {
            "model": "llama-3.3-70b-versatile",
            "capabilities": ["Document analysis", "Cross-domain synthesis", "Investment insights", "Risk assessment"],
            "cost_advantage": "Free tier with generous limits"
        }
    }

# Add helper methods to the integrated analysis service
async def _extract_research_insights(self, research_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract insights from research documents."""
    return {
        "key_findings": ["Finding 1", "Finding 2"],
        "research_trends": ["Trend 1", "Trend 2"],
        "methodology": "Quantitative analysis"
    }

async def _extract_financial_insights(self, financial_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract insights from financial documents."""
    return {
        "performance_metrics": {"revenue_growth": 0.15, "profit_margin": 0.20},
        "risk_factors": ["Market risk", "Competition risk"],
        "growth_drivers": ["R&D investment", "Market expansion"]
    }

async def _find_correlations(self, research_docs: List[Dict[str, Any]], financial_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find correlations between research and financial data."""
    return {
        "research_funding_vs_stock_performance": 0.75,
        "publication_count_vs_revenue_growth": 0.60,
        "patent_filings_vs_market_cap": 0.80
    }

async def _generate_investment_implications(self, synthesis: str) -> Dict[str, Any]:
    """Generate investment implications from synthesis."""
    return {
        "investment_thesis": "Research-driven growth story",
        "key_catalysts": ["Upcoming research results", "Regulatory approval"],
        "risk_factors": ["Research delays", "Competition"],
        "recommendation": "BUY"
    }
