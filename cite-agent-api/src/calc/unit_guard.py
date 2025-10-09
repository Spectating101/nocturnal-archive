"""
Unit Guard for Financial Calculations
Prevents non-monetary units in monetary expressions and provides unit classification
"""

import structlog
from typing import Dict, Any, Optional, Literal, Set
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException, status

logger = structlog.get_logger(__name__)

class UnitClassification(BaseModel):
    """Unit classification and validation"""
    unit: str
    unit_class: Literal["monetary", "shares", "ratio", "pure", "unknown"]
    is_monetary: bool
    currency: Optional[str] = None
    scale: Optional[str] = None

class UnitGuardError(HTTPException):
    """Custom exception for unit guard violations"""
    def __init__(self, detail: str, unit: str, unit_class: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "unsupported_unit",
                "title": "Unsupported Unit Type",
                "detail": detail,
                "unit": unit,
                "unit_class": unit_class,
                "supported_units": ["monetary units (USD, EUR, etc.)"]
            }
        )

class UnitGuard:
    """Guards against inappropriate unit usage in financial calculations"""
    
    def __init__(self):
        # Monetary unit patterns
        self.monetary_patterns = {
            "USD", "US$", "$", "EUR", "€", "GBP", "£", "JPY", "¥", 
            "CAD", "C$", "AUD", "A$", "CHF", "TWD", "NT$", "CNY"
        }
        
        # Share-based units
        self.share_units = {
            "shares", "share", "sh", "common", "preferred", "outstanding",
            "issued", "authorized", "treasury"
        }
        
        # Ratio/percentage units
        self.ratio_units = {
            "ratio", "percent", "%", "pct", "basis_points", "bp",
            "multiple", "x", "times"
        }
        
        # Pure numbers (no unit)
        self.pure_units = {
            "pure", "unitless", "count", "number", "ratio"
        }
        
        # Scale indicators
        self.scale_indicators = {"K", "M", "B", "T", "U"}
    
    def classify_unit(self, unit: str) -> UnitClassification:
        """
        Classify a unit string
        
        Args:
            unit: Unit string to classify
            
        Returns:
            Unit classification
        """
        if not unit:
            return UnitClassification(
                unit="",
                unit_class="unknown",
                is_monetary=False
            )
        
        unit_upper = unit.upper()
        
        # Check for monetary units
        for monetary in self.monetary_patterns:
            if monetary in unit_upper:
                # Extract currency and scale
                currency = self._extract_currency(unit_upper)
                scale = self._extract_scale(unit_upper)
                
                return UnitClassification(
                    unit=unit,
                    unit_class="monetary",
                    is_monetary=True,
                    currency=currency,
                    scale=scale
                )
        
        # Check for share units
        for share in self.share_units:
            if share in unit_upper.lower():
                return UnitClassification(
                    unit=unit,
                    unit_class="shares",
                    is_monetary=False
                )
        
        # Check for ratio units
        for ratio in self.ratio_units:
            if ratio in unit_upper.lower():
                return UnitClassification(
                    unit=unit,
                    unit_class="ratio",
                    is_monetary=False
                )
        
        # Check for pure units
        for pure in self.pure_units:
            if pure in unit_upper.lower():
                return UnitClassification(
                    unit=unit,
                    unit_class="pure",
                    is_monetary=False
                )
        
        # Default to unknown
        return UnitClassification(
            unit=unit,
            unit_class="unknown",
            is_monetary=False
        )
    
    def validate_monetary_expression(
        self,
        expression: str,
        input_units: Dict[str, str]
    ) -> Dict[str, UnitClassification]:
        """
        Validate that all inputs to a monetary expression are monetary units
        
        Args:
            expression: Mathematical expression
            input_units: Dictionary of variable -> unit mappings
            
        Returns:
            Dictionary of variable -> unit classification
            
        Raises:
            UnitGuardError: If non-monetary units found in monetary expression
        """
        classifications = {}
        non_monetary_vars = []
        
        for var, unit in input_units.items():
            classification = self.classify_unit(unit)
            classifications[var] = classification
            
            if not classification.is_monetary:
                non_monetary_vars.append(f"{var} ({unit})")
        
        if non_monetary_vars:
            raise UnitGuardError(
                detail=f"Non-monetary units found in monetary expression: {', '.join(non_monetary_vars)}",
                unit=", ".join([input_units[var] for var in non_monetary_vars]),
                unit_class="non-monetary"
            )
        
        logger.debug(
            "Monetary expression validated",
            expression=expression,
            input_units=input_units,
            classifications={var: cls.unit_class for var, cls in classifications.items()}
        )
        
        return classifications
    
    def _extract_currency(self, unit: str) -> Optional[str]:
        """Extract currency code from unit string"""
        for currency in self.monetary_patterns:
            if currency in unit:
                return currency
        return None
    
    def _extract_scale(self, unit: str) -> Optional[str]:
        """Extract scale indicator from unit string"""
        for scale in self.scale_indicators:
            if f"-{scale}" in unit or f"{scale}-" in unit:
                return scale
        return "U"  # Default to units
    
    def get_supported_units(self) -> Dict[str, Set[str]]:
        """Get list of supported units by class"""
        return {
            "monetary": self.monetary_patterns,
            "shares": self.share_units,
            "ratio": self.ratio_units,
            "pure": self.pure_units
        }
    
    def is_monetary_expression(self, expression: str) -> bool:
        """
        Determine if an expression is monetary based on common patterns
        
        Args:
            expression: Mathematical expression
            
        Returns:
            True if expression appears to be monetary
        """
        monetary_indicators = {
            "revenue", "income", "profit", "margin", "cost", "expense",
            "cash", "flow", "debt", "equity", "assets", "liabilities",
            "earnings", "dividend", "price", "value"
        }
        
        expression_lower = expression.lower()
        return any(indicator in expression_lower for indicator in monetary_indicators)

# Global instance
unit_guard = UnitGuard()

def get_unit_guard() -> UnitGuard:
    """Get global unit guard instance"""
    return unit_guard
