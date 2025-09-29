"""
Amendment and Restatement Control for Financial Facts
Handles as-reported vs. amended data with explicit accession pinning
"""

import structlog
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class AmendmentInfo(BaseModel):
    """Information about amendments and restatements"""
    accession: str
    amended: bool
    as_reported: bool
    original_accession: Optional[str] = None
    amendment_date: Optional[datetime] = None
    restatement_reason: Optional[str] = None

class FactWithAmendment(BaseModel):
    """Financial fact with amendment metadata"""
    value: float
    period: str
    concept: str
    unit: str
    amendment_info: AmendmentInfo
    citation: Dict[str, Any]

class AmendmentController:
    """Controls amendment and restatement handling for financial facts"""
    
    def __init__(self):
        self.amendment_cache: Dict[str, List[AmendmentInfo]] = {}
    
    def get_fact_with_amendment_control(
        self,
        ticker: str,
        concept: str,
        period: str,
        as_reported: bool = False,
        accession: Optional[str] = None
    ) -> Optional[FactWithAmendment]:
        """
        Get financial fact with amendment control
        
        Args:
            ticker: Company ticker
            concept: XBRL concept
            period: Reporting period
            as_reported: If True, return as originally reported (ignore amendments)
            accession: Pin to specific accession number for reproducibility
            
        Returns:
            Fact with amendment metadata
        """
        try:
            # This would integrate with your facts store
            # For now, return a structured example
            
            if accession:
                # Pin to specific accession
                amendment_info = AmendmentInfo(
                    accession=accession,
                    amended=False,
                    as_reported=True
                )
            elif as_reported:
                # Get as originally reported (latest non-amended)
                amendment_info = AmendmentInfo(
                    accession="0000320193-24-000006",
                    amended=False,
                    as_reported=True
                )
            else:
                # Get latest (may include amendments)
                amendment_info = AmendmentInfo(
                    accession="0000320193-24-000007",
                    amended=True,
                    as_reported=False,
                    original_accession="0000320193-24-000006",
                    amendment_date=datetime(2024, 1, 15),
                    restatement_reason="Correction of revenue recognition timing"
                )
            
            # Mock fact data
            fact = FactWithAmendment(
                value=119575000000,
                period=period,
                concept=concept,
                unit="USD",
                amendment_info=amendment_info,
                citation={
                    "source": "SEC EDGAR",
                    "accession": amendment_info.accession,
                    "url": f"https://www.sec.gov/Archives/edgar/data/320193/{amendment_info.accession}/",
                    "amended": amendment_info.amended,
                    "as_reported": amendment_info.as_reported,
                    "original_accession": amendment_info.original_accession,
                    "amendment_date": amendment_info.amendment_date.isoformat() if amendment_info.amendment_date else None,
                    "restatement_reason": amendment_info.restatement_reason
                }
            )
            
            logger.debug(
                "Fact retrieved with amendment control",
                ticker=ticker,
                concept=concept,
                period=period,
                as_reported=as_reported,
                accession=accession,
                amended=amendment_info.amended
            )
            
            return fact
            
        except Exception as e:
            logger.error(
                "Failed to get fact with amendment control",
                ticker=ticker,
                concept=concept,
                period=period,
                error=str(e)
            )
            return None
    
    def get_amendment_history(
        self,
        ticker: str,
        concept: str,
        period: str
    ) -> List[AmendmentInfo]:
        """
        Get amendment history for a fact
        
        Args:
            ticker: Company ticker
            concept: XBRL concept
            period: Reporting period
            
        Returns:
            List of amendments in chronological order
        """
        try:
            # This would query your facts store for amendment history
            # For now, return mock data
            
            history = [
                AmendmentInfo(
                    accession="0000320193-24-000006",
                    amended=False,
                    as_reported=True
                ),
                AmendmentInfo(
                    accession="0000320193-24-000007",
                    amended=True,
                    as_reported=False,
                    original_accession="0000320193-24-000006",
                    amendment_date=datetime(2024, 1, 15),
                    restatement_reason="Correction of revenue recognition timing"
                )
            ]
            
            logger.debug(
                "Amendment history retrieved",
                ticker=ticker,
                concept=concept,
                period=period,
                amendments_count=len(history)
            )
            
            return history
            
        except Exception as e:
            logger.error(
                "Failed to get amendment history",
                ticker=ticker,
                concept=concept,
                period=period,
                error=str(e)
            )
            return []
    
    def validate_accession(self, accession: str) -> bool:
        """
        Validate accession number format
        
        Args:
            accession: SEC accession number
            
        Returns:
            True if valid format
        """
        # SEC accession format: 0000320193-24-000006
        import re
        pattern = r'^\d{10}-\d{2}-\d{6}$'
        return bool(re.match(pattern, accession))

# Global instance
amendment_controller = AmendmentController()

def get_amendment_controller() -> AmendmentController:
    """Get global amendment controller instance"""
    return amendment_controller
