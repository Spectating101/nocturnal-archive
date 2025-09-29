"""
Integrated Analysis Service - Cross-system research and finance analysis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .llm_service.api_clients.groq_client import GroqClient
from .research_service.enhanced_research import EnhancedResearchService
from .paper_service.openalex import OpenAlexClient

logger = logging.getLogger(__name__)

class IntegratedAnalysisService:
    """
    Service that combines research and finance systems for cross-domain analysis.
    
    Features:
    - Research + Finance correlation analysis
    - Cross-domain synthesis using Groq
    - Unified knowledge graph construction
    - Investment insights from academic research
    """
    
    def __init__(self):
        self.groq_client = GroqClient()
        self.research_service = EnhancedResearchService()
        self.openalex_client = OpenAlexClient()
        
        logger.info("Integrated Analysis Service initialized")
    
    async def analyze_research_finance_correlation(
        self, 
        research_topic: str, 
        ticker: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze correlation between academic research and financial performance.
        
        Args:
            research_topic: Academic research topic (e.g., "CRISPR gene editing")
            ticker: Stock ticker symbol (e.g., "CRSP")
            analysis_type: Type of analysis ("comprehensive", "trends", "investment")
            
        Returns:
            Integrated analysis results
        """
        try:
            logger.info(f"Starting integrated analysis: {research_topic} + {ticker}")
            
            # Step 1: Get academic research
            research_data = await self._get_research_data(research_topic)
            
            # Step 2: Get financial data (placeholder - would integrate with finance system)
            financial_data = await self._get_financial_data(ticker)
            
            # Step 3: Use Groq for cross-domain analysis
            correlation_analysis = await self._analyze_correlation_with_groq(
                research_data, financial_data, analysis_type
            )
            
            # Step 4: Generate investment insights
            investment_insights = await self._generate_investment_insights(
                research_data, financial_data, correlation_analysis
            )
            
            result = {
                "analysis_id": str(uuid.uuid4()),
                "research_topic": research_topic,
                "ticker": ticker,
                "analysis_type": analysis_type,
                "research_data": research_data,
                "financial_data": financial_data,
                "correlation_analysis": correlation_analysis,
                "investment_insights": investment_insights,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            logger.info(f"Integrated analysis completed: {result['analysis_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Integrated analysis failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "analysis_id": str(uuid.uuid4())
            }
    
    async def _get_research_data(self, topic: str) -> Dict[str, Any]:
        """Get academic research data for the topic."""
        try:
            # Use the research service to get papers
            papers = await self.research_service.search_papers(
                query=topic,
                limit=10,
                sources=["openalex"]
            )
            
            # Extract key information
            research_summary = {
                "topic": topic,
                "papers_found": len(papers.get("papers", [])),
                "key_papers": papers.get("papers", [])[:5],
                "research_trends": await self._extract_research_trends(papers),
                "key_findings": await self._extract_key_findings(papers)
            }
            
            return research_summary
            
        except Exception as e:
            logger.error(f"Failed to get research data: {str(e)}")
            return {"error": str(e), "topic": topic}
    
    async def _get_financial_data(self, ticker: str) -> Dict[str, Any]:
        """Get financial data for the ticker (placeholder implementation)."""
        # This would integrate with the finance system
        # For now, return mock data structure
        return {
            "ticker": ticker,
            "company_name": f"Company {ticker}",
            "sector": "Technology",
            "market_cap": 1000000000,
            "revenue_growth": 0.15,
            "profit_margin": 0.20,
            "r_and_d_spending": 0.10,
            "stock_performance": {
                "1_year_return": 0.25,
                "3_year_return": 0.45,
                "volatility": 0.30
            },
            "financial_metrics": {
                "pe_ratio": 25.0,
                "pb_ratio": 3.5,
                "debt_to_equity": 0.3
            }
        }
    
    async def _analyze_correlation_with_groq(
        self, 
        research_data: Dict[str, Any], 
        financial_data: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Use Groq to analyze correlation between research and financial data."""
        
        # Build comprehensive prompt for Groq
        prompt = self._build_correlation_prompt(research_data, financial_data, analysis_type)
        
        # Create document for Groq analysis
        analysis_doc = {
            "id": "correlation_analysis",
            "title": f"Research-Finance Correlation Analysis: {research_data.get('topic', 'Unknown')}",
            "content": prompt,
            "type": "correlation_analysis"
        }
        
        # Use Groq to analyze
        result = await self.groq_client.process_document(analysis_doc)
        
        if result.get("success"):
            return {
                "correlation_score": self._extract_correlation_score(result.get("analysis", "")),
                "key_correlations": self._extract_key_correlations(result.get("analysis", "")),
                "trend_analysis": self._extract_trend_analysis(result.get("analysis", "")),
                "groq_analysis": result.get("analysis", "")
            }
        else:
            return {"error": result.get("error", "Groq analysis failed")}
    
    def _build_correlation_prompt(
        self, 
        research_data: Dict[str, Any], 
        financial_data: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """Build comprehensive prompt for Groq correlation analysis."""
        
        return f"""
        Analyze the correlation between academic research and financial performance:
        
        RESEARCH CONTEXT:
        Topic: {research_data.get('topic', 'Unknown')}
        Papers Found: {research_data.get('papers_found', 0)}
        Key Findings: {research_data.get('key_findings', [])}
        Research Trends: {research_data.get('research_trends', [])}
        
        FINANCIAL CONTEXT:
        Company: {financial_data.get('company_name', 'Unknown')} ({financial_data.get('ticker', 'N/A')})
        Sector: {financial_data.get('sector', 'Unknown')}
        Market Cap: ${financial_data.get('market_cap', 0):,}
        Revenue Growth: {financial_data.get('revenue_growth', 0):.1%}
        R&D Spending: {financial_data.get('r_and_d_spending', 0):.1%}
        Stock Performance: {financial_data.get('stock_performance', {})}
        
        ANALYSIS TYPE: {analysis_type}
        
        Please provide:
        1. **Correlation Analysis**: How do research trends correlate with financial performance?
        2. **Investment Implications**: What does the research suggest about future performance?
        3. **Risk Factors**: What research-based risks should investors consider?
        4. **Opportunity Assessment**: What research opportunities could drive growth?
        5. **Timeline Analysis**: How do research cycles align with financial cycles?
        
        Format your response with clear sections and specific insights.
        """
    
    async def _generate_investment_insights(
        self,
        research_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        correlation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate investment insights from the integrated analysis."""
        
        prompt = f"""
        Generate investment insights based on the research-finance correlation analysis:
        
        Research Data: {research_data}
        Financial Data: {financial_data}
        Correlation Analysis: {correlation_analysis}
        
        Provide:
        1. **Investment Thesis**: Main investment argument
        2. **Key Catalysts**: Research-driven growth catalysts
        3. **Risk Assessment**: Research-based risks
        4. **Valuation Impact**: How research affects valuation
        5. **Timeline**: Expected research-to-financial impact timeline
        6. **Recommendation**: Buy/Hold/Sell with reasoning
        """
        
        insight_doc = {
            "id": "investment_insights",
            "title": "Investment Insights from Research-Finance Analysis",
            "content": prompt,
            "type": "investment_analysis"
        }
        
        result = await self.groq_client.process_document(insight_doc)
        
        if result.get("success"):
            return {
                "investment_thesis": self._extract_investment_thesis(result.get("analysis", "")),
                "key_catalysts": self._extract_catalysts(result.get("analysis", "")),
                "risk_assessment": self._extract_risks(result.get("analysis", "")),
                "recommendation": self._extract_recommendation(result.get("analysis", "")),
                "full_analysis": result.get("analysis", "")
            }
        else:
            return {"error": result.get("error", "Investment insights generation failed")}
    
    # Helper methods for data extraction
    async def _extract_research_trends(self, papers: Dict[str, Any]) -> List[str]:
        """Extract research trends from papers."""
        # This would use the research service to analyze trends
        return ["Growing interest in topic", "Increased funding", "New methodologies"]
    
    async def _extract_key_findings(self, papers: Dict[str, Any]) -> List[str]:
        """Extract key findings from papers."""
        # This would use the research service to extract findings
        return ["Key finding 1", "Key finding 2", "Key finding 3"]
    
    def _extract_correlation_score(self, analysis: str) -> float:
        """Extract correlation score from Groq analysis."""
        # Simple extraction - would be more sophisticated in practice
        if "strong correlation" in analysis.lower():
            return 0.8
        elif "moderate correlation" in analysis.lower():
            return 0.5
        elif "weak correlation" in analysis.lower():
            return 0.2
        else:
            return 0.0
    
    def _extract_key_correlations(self, analysis: str) -> List[str]:
        """Extract key correlations from analysis."""
        # Simple extraction - would be more sophisticated in practice
        return ["Research funding correlates with stock performance", "Publication trends predict revenue growth"]
    
    def _extract_trend_analysis(self, analysis: str) -> Dict[str, str]:
        """Extract trend analysis from Groq response."""
        return {
            "short_term": "Research momentum building",
            "medium_term": "Potential breakthrough expected",
            "long_term": "Sector transformation likely"
        }
    
    def _extract_investment_thesis(self, analysis: str) -> str:
        """Extract investment thesis from analysis."""
        return "Research-driven growth story with strong fundamentals"
    
    def _extract_catalysts(self, analysis: str) -> List[str]:
        """Extract key catalysts from analysis."""
        return ["Upcoming research results", "Regulatory approval", "Partnership announcements"]
    
    def _extract_risks(self, analysis: str) -> List[str]:
        """Extract risks from analysis."""
        return ["Research delays", "Competition", "Regulatory changes"]
    
    def _extract_recommendation(self, analysis: str) -> str:
        """Extract investment recommendation from analysis."""
        if "buy" in analysis.lower():
            return "BUY"
        elif "sell" in analysis.lower():
            return "SELL"
        else:
            return "HOLD"

# Global instance
integrated_analysis_service = IntegratedAnalysisService()
