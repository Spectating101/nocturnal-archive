"""
Real XBRL Segment Parser
Parses segment facts from SEC EDGAR with proper dimension/member qnames
"""

import structlog
from typing import Dict, Any, List, Optional
from src.adapters.sec_facts import get_sec_facts_adapter

logger = structlog.get_logger(__name__)

class SegmentParser:
    """Parse real XBRL segment data from SEC filings"""
    
    def __init__(self):
        self.sec_adapter = get_sec_facts_adapter()
        
        # Map internal dimensions to XBRL axis concepts
        self.dimension_map = {
            "Geography": [
                "us-gaap:StatementGeographicalAxis",
                "us-gaap:GeographicAxis", 
                "us-gaap:GeographicRegionAxis"
            ],
            "Business": [
                "us-gaap:BusinessSegmentAxis",
                "us-gaap:SegmentAxis",
                "us-gaap:OperatingSegmentAxis"
            ],
            "Product": [
                "us-gaap:ProductAxis",
                "us-gaap:ProductLineAxis",
                "us-gaap:ServiceAxis"
            ]
        }
        
        # Common revenue concepts for segments
        self.revenue_concepts = [
            "SalesRevenueNet",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "Revenue"
        ]
    
    async def get_segment_series(
        self,
        ticker: str,
        kpi: str,
        dim: str,
        freq: str = "Q",
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get real segment data from SEC filings
        
        Returns:
            List of segment series with proper XBRL dimension/member qnames
        """
        try:
            # Get company facts
            cik = self.sec_adapter.ticker_to_cik.get(ticker.upper())
            if not cik:
                logger.warning("Unknown ticker for segments", ticker=ticker)
                return []
            
            session = await self.sec_adapter._get_session()
            url = f"{self.sec_adapter.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
            
            logger.info("Fetching segment data", ticker=ticker, dim=dim, kpi=kpi)
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to fetch company facts for segments", 
                               ticker=ticker, status=response.status)
                    return []
                
                data = await response.json()
                facts = data.get("facts", {}).get("us-gaap", {})
                
                # Find segment facts with dimensions
                segment_facts = self._extract_segment_facts(facts, dim, kpi)
                
                if not segment_facts:
                    logger.warning("No segment facts found", ticker=ticker, dim=dim, kpi=kpi)
                    # Production mode - no mock data
                    return []
                
                # Group by segment member and build series
                return self._build_segment_series(segment_facts, ticker, kpi, dim, limit)
                
        except Exception as e:
            logger.error("Failed to parse segments", ticker=ticker, dim=dim, kpi=kpi, error=str(e))
            return []
    
    def _extract_segment_facts(self, facts: Dict[str, Any], dim: str, kpi: str) -> List[Dict[str, Any]]:
        """Extract facts that have the specified dimension"""
        segment_facts = []
        
        # Get possible dimension axes for this dimension type
        dimension_axes = self.dimension_map.get(dim, [])
        revenue_concepts = self.revenue_concepts if kpi == "revenue" else [kpi]
        
        for concept in revenue_concepts:
            if concept not in facts:
                continue
                
            concept_data = facts[concept]
            if "units" not in concept_data:
                continue
            
            # Check each unit (USD, etc.)
            for unit, periods in concept_data["units"].items():
                for period_data in periods:
                    # Check if this fact has segment dimensions
                    if "segment" in period_data:
                        segment_info = period_data["segment"]
                        
                        # Check if this matches our target dimension
                        for axis_qname in dimension_axes:
                            if axis_qname in segment_info:
                                member_info = segment_info[axis_qname]
                                
                                # Extract member qname and label
                                member_qname = member_info.get("member", "")
                                member_label = member_info.get("label", "")
                                
                                # Build fact with dimension info
                                fact_with_dim = {
                                    **period_data,
                                    "concept": concept,
                                    "unit": unit,
                                    "dimension": {
                                        "axis": axis_qname,
                                        "member": member_qname,
                                        "member_label": member_label
                                    }
                                }
                                
                                segment_facts.append(fact_with_dim)
                                logger.debug("Found segment fact", 
                                           concept=concept,
                                           axis=axis_qname,
                                           member=member_qname,
                                           member_label=member_label,
                                           value=period_data.get("val"))
        
        return segment_facts
    
    def _build_segment_series(
        self, 
        segment_facts: List[Dict[str, Any]], 
        ticker: str, 
        kpi: str, 
        dim: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Build segment series from facts"""
        # Group by segment member
        member_groups = {}
        
        for fact in segment_facts:
            member_qname = fact["dimension"]["member"]
            member_label = fact["dimension"]["member_label"]
            
            if member_qname not in member_groups:
                member_groups[member_qname] = {
                    "member_qname": member_qname,
                    "member_label": member_label,
                    "axis_qname": fact["dimension"]["axis"],
                    "facts": []
                }
            
            member_groups[member_qname]["facts"].append(fact)
        
        # Build series for each member
        series_list = []
        
        for member_qname, group in member_groups.items():
            # Sort facts by period
            sorted_facts = sorted(
                group["facts"], 
                key=lambda x: x.get("end", ""), 
                reverse=True
            )[:limit]
            
            points = []
            for fact in sorted_facts:
                # Build citation with dimension info
                citation = {
                    "source": "SEC EDGAR",
                    "accession": fact.get("accn"),
                    "url": f"https://www.sec.gov/Archives/edgar/data/{self.sec_adapter.ticker_to_cik.get(ticker, '')}/{fact.get('accn')}/",
                    "concept": fact["concept"],
                    "taxonomy": "us-gaap",
                    "unit": fact["unit"],
                    "scale": "U",
                    "fx_used": None,
                    "amended": False,
                    "as_reported": True,
                    "filed": fact.get("filed"),
                    "form": fact.get("form"),
                    "fiscal_year": fact.get("fy"),
                    "fiscal_period": fact.get("fp"),
                    # XBRL dimension info
                    "dimension": {
                        "axis": group["axis_qname"],
                        "member": member_qname,
                        "member_label": group["member_label"]
                    }
                }
                
                points.append({
                    "period": fact.get("end"),
                    "value": fact.get("val"),
                    "unit": fact["unit"],
                    "citations": [citation],
                    "quality_flags": []
                })
            
            if points:
                series_list.append({
                    "segment": group["member_label"],  # User-friendly label
                    "points": points,
                    "metadata": {
                        "axis_qname": group["axis_qname"],
                        "member_qname": member_qname,
                        "member_label": group["member_label"]
                    }
                })
        
        logger.info("Built segment series", 
                   ticker=ticker, dim=dim, kpi=kpi, 
                   segments=len(series_list), total_facts=len(segment_facts))
        
        return series_list
    
# Global instance
segment_parser = SegmentParser()

def get_segment_parser() -> SegmentParser:
    """Get global segment parser instance"""
    return segment_parser
