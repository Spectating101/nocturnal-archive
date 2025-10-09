"""
Unit and Scale Normalization for XBRL Facts
Handles unit scaling, currency conversion, and metadata tracking
"""

import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = structlog.get_logger(__name__)

class UnitScaleNormalizer:
    """Normalize XBRL facts for unit scaling and currency conversion"""
    
    def __init__(self, fx_normalizer):
        self.fx_normalizer = fx_normalizer
        
        # XBRL unit scaling factors
        self.scale_factors = {
            "K": 1e3,      # Thousands
            "M": 1e6,      # Millions  
            "B": 1e9,      # Billions
            "T": 1e12,     # Trillions
            "U": 1,        # Units (no scaling)
            "": 1,         # Default to units
        }
        
        # Common currency codes
        self.currency_codes = {
            "USD": "USD", "US$": "USD", "$": "USD",
            "EUR": "EUR", "€": "EUR",
            "GBP": "GBP", "£": "GBP",
            "JPY": "JPY", "¥": "JPY",
            "CAD": "CAD", "C$": "CAD",
            "AUD": "AUD", "A$": "AUD",
            "CHF": "CHF",
            "TWD": "TWD", "NT$": "TWD",
            "CNY": "CNY", "¥": "CNY",
        }
    
    def normalize_fact(
        self,
        value: float,
        unit: str,
        period_end: str,
        target_currency: str = "USD",
        target_scale: str = "U"
    ) -> Dict[str, Any]:
        """
        Normalize a financial fact for unit scaling and currency conversion
        
        Args:
            value: Raw fact value
            unit: XBRL unit string (e.g., "USD", "EUR-M", "TWD-K")
            period_end: Period end date for FX conversion
            target_currency: Target currency for conversion
            target_scale: Target scale (K, M, B, T, U)
            
        Returns:
            Normalized fact with metadata
        """
        try:
            # Parse unit string
            source_currency, source_scale = self._parse_unit(unit)
            
            # Apply scaling
            scale_factor = self.scale_factors.get(source_scale, 1)
            scaled_value = value * scale_factor
            
            # Convert currency if needed
            converted_value = scaled_value
            fx_rate = 1.0
            fx_used = None
            
            if source_currency != target_currency:
                try:
                    converted_value = self.fx_normalizer.normalize(
                        scaled_value,
                        source_currency,
                        target_currency,
                        period_end
                    )
                    fx_rate = converted_value / scaled_value
                    fx_used = {
                        "from_currency": source_currency,
                        "to_currency": target_currency,
                        "rate": fx_rate,
                        "asof": period_end
                    }
                except Exception as e:
                    logger.warning(
                        "FX conversion failed, using original value",
                        from_currency=source_currency,
                        to_currency=target_currency,
                        period=period_end,
                        error=str(e)
                    )
            
            # Apply target scaling
            target_scale_factor = self.scale_factors.get(target_scale, 1)
            final_value = converted_value / target_scale_factor
            
            # Build normalization metadata
            normalization = {
                "original_value": value,
                "original_unit": unit,
                "normalized_value": final_value,
                "target_unit": f"{target_currency}-{target_scale}",
                "scaling_applied": {
                    "source_scale": source_scale,
                    "source_factor": scale_factor,
                    "target_scale": target_scale,
                    "target_factor": target_scale_factor
                },
                "fx_conversion": fx_used
            }
            
            logger.debug(
                "Fact normalized",
                original_value=value,
                original_unit=unit,
                final_value=final_value,
                target_unit=f"{target_currency}-{target_scale}",
                fx_rate=fx_rate
            )
            
            return normalization
            
        except Exception as e:
            logger.error(
                "Fact normalization failed",
                value=value,
                unit=unit,
                period=period_end,
                error=str(e)
            )
            
            # Return original value with error flag
            return {
                "original_value": value,
                "original_unit": unit,
                "normalized_value": value,
                "target_unit": unit,
                "normalization_error": str(e),
                "scaling_applied": {},
                "fx_conversion": None
            }
    
    def _parse_unit(self, unit: str) -> Tuple[str, str]:
        """
        Parse XBRL unit string to extract currency and scale
        
        Args:
            unit: Unit string (e.g., "USD", "EUR-M", "TWD-K")
            
        Returns:
            Tuple of (currency, scale)
        """
        if not unit:
            return "USD", "U"
        
        # Handle common formats
        unit_upper = unit.upper()
        
        # Check for scale suffix (e.g., "USD-M", "EUR-K")
        for scale, _ in self.scale_factors.items():
            if scale != "U" and unit_upper.endswith(f"-{scale}"):
                currency_part = unit_upper[:-len(f"-{scale}")]
                currency = self.currency_codes.get(currency_part, currency_part)
                return currency, scale
        
        # Check for scale prefix (e.g., "M-USD", "K-EUR")
        for scale, _ in self.scale_factors.items():
            if scale != "U" and unit_upper.startswith(f"{scale}-"):
                currency_part = unit_upper[len(f"{scale}-"):]
                currency = self.currency_codes.get(currency_part, currency_part)
                return currency, scale
        
        # Check for currency codes
        for code, normalized in self.currency_codes.items():
            if unit_upper == code or unit_upper == normalized:
                return normalized, "U"
        
        # Default assumptions
        if any(char.isdigit() for char in unit):
            # Contains digits, might be a complex unit
            return "USD", "U"
        
        # Assume it's a currency code
        return unit_upper, "U"
    
    def get_normalized_unit_display(self, unit: str, target_currency: str = "USD") -> str:
        """Get human-readable unit display"""
        currency, scale = self._parse_unit(unit)
        
        if scale == "U":
            return target_currency
        else:
            return f"{target_currency} ({scale})"
    
    def should_normalize(self, unit: str, target_currency: str = "USD") -> bool:
        """Check if normalization is needed"""
        currency, scale = self._parse_unit(unit)
        return currency != target_currency or scale != "U"

# Global instance
unit_scale_normalizer = None

def get_normalizer(fx_normalizer):
    """Get global unit scale normalizer instance"""
    global unit_scale_normalizer
    if unit_scale_normalizer is None:
        unit_scale_normalizer = UnitScaleNormalizer(fx_normalizer)
    return unit_scale_normalizer
