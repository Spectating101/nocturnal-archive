"""
FinSight Calculations Engine
Safe expression evaluation with provenance tracking
"""

import re
import structlog
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger(__name__)

class PeriodType(Enum):
    DURATION = "duration"
    INSTANT = "instant"

class OutputType(Enum):
    VALUE = "value"
    PERCENT = "percent"
    RATIO = "ratio"
    DAYS = "days"

@dataclass
class Fact:
    """Represents a single financial fact with provenance"""
    concept: str
    value: float
    unit: str
    period: str
    period_type: PeriodType
    accession: str
    fragment_id: Optional[str]
    url: str
    dimensions: Dict[str, str]
    quality_flags: List[str]

@dataclass
class CalculationResult:
    """Result of a calculation with full breakdown"""
    ticker: str
    metric: str
    period: str
    freq: str
    value: float
    output_type: OutputType
    formula: str
    inputs: Dict[str, Fact]
    citations: List[Dict[str, Any]]
    quality_flags: List[str]
    metadata: Dict[str, Any]

class CalculationEngine:
    """Engine for evaluating financial expressions with provenance"""
    
    def __init__(self, facts_store, kpi_registry):
        """
        Initialize calculation engine
        
        Args:
            facts_store: Store for retrieving financial facts
            kpi_registry: Registry for KPI definitions and expressions
        """
        self.facts_store = facts_store
        self.kpi_registry = kpi_registry
        self.functions = {
            "avg": self._avg_function,
            "ttm": self._ttm_function,
            "yoy": self._yoy_function,
            "qoq": self._qoq_function,
            "cagr": self._cagr_function,
            "per_share": self._per_share_function,
        }
    
    async def calculate_metric(
        self,
        ticker: str,
        metric: str,
        period: str = "latest",
        freq: str = "Q",
        ttm: bool = False,
        segment: Optional[str] = None
    ) -> CalculationResult:
        """
        Calculate a specific metric for a company
        
        Args:
            ticker: Company ticker symbol
            metric: Metric name from KPI registry
            period: Period to calculate for (e.g., "2024-Q4", "latest")
            freq: Frequency ("Q" for quarterly, "A" for annual)
            ttm: Whether to calculate trailing twelve months
            segment: Business segment filter (optional)
            
        Returns:
            CalculationResult with value and full breakdown
        """
        try:
            logger.info(
                "Calculating metric",
                ticker=ticker,
                metric=metric,
                period=period,
                freq=freq,
                ttm=ttm,
                segment=segment
            )
            
            # Get metric definition from registry
            metric_def = self.kpi_registry.get_metric(metric)
            if not metric_def:
                raise ValueError(f"Unknown metric: {metric}")
            
            # Resolve inputs for the expression
            inputs = await self._resolve_inputs(
                ticker, metric_def["inputs"], period, freq, ttm, segment
            )
            
            # Evaluate expression
            value = await self._evaluate_expression(metric_def["expr"], inputs)
            
            # Apply output type formatting
            output_type = OutputType(metric_def.get("output", "value"))
            formatted_value = self._format_value(value, output_type)
            
            # Build citations from inputs
            citations = self._build_citations(inputs)
            
            # Collect quality flags
            quality_flags = self._collect_quality_flags(inputs, metric_def)
            
            # Build metadata
            metadata = {
                "calculated_at": datetime.now().isoformat(),
                "engine_version": "1.0",
                "ttm": ttm,
                "segment": segment,
                "formula": metric_def["expr"]
            }
            
            result = CalculationResult(
                ticker=ticker,
                metric=metric,
                period=period,
                freq=freq,
                value=formatted_value,
                output_type=output_type,
                formula=metric_def["expr"],
                inputs=inputs,
                citations=citations,
                quality_flags=quality_flags,
                metadata=metadata
            )
            
            logger.info(
                "Metric calculation completed",
                ticker=ticker,
                metric=metric,
                value=formatted_value,
                flags_count=len(quality_flags)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Metric calculation failed",
                ticker=ticker,
                metric=metric,
                error=str(e)
            )
            raise
    
    async def explain_expression(
        self,
        ticker: str,
        expr: str,
        period: str = "latest",
        freq: str = "Q",
        ttm: bool = False
    ) -> CalculationResult:
        """
        Explain a custom expression with full breakdown
        
        Args:
            ticker: Company ticker symbol
            expr: Custom expression to evaluate
            period: Period to calculate for
            freq: Frequency
            ttm: Whether to calculate trailing twelve months
            
        Returns:
            CalculationResult with explanation and breakdown
        """
        try:
            logger.info(
                "Explaining expression",
                ticker=ticker,
                expr=expr,
                period=period,
                freq=freq,
                ttm=ttm
            )
            
            # Parse expression to find input concepts
            input_concepts = self._parse_expression_inputs(expr)
            
            # Resolve inputs
            inputs = await self._resolve_concepts(
                ticker, input_concepts, period, freq, ttm
            )
            
            # Evaluate expression
            value = await self._evaluate_expression(expr, inputs)
            
            # Build result
            citations = self._build_citations(inputs)
            quality_flags = self._collect_quality_flags(inputs, {"expr": expr})
            
            metadata = {
                "calculated_at": datetime.now().isoformat(),
                "engine_version": "1.0",
                "ttm": ttm,
                "expression_type": "custom"
            }
            
            result = CalculationResult(
                ticker=ticker,
                metric="custom",
                period=period,
                freq=freq,
                value=value,
                output_type=OutputType.VALUE,
                formula=expr,
                inputs=inputs,
                citations=citations,
                quality_flags=quality_flags,
                metadata=metadata
            )
            
            logger.info(
                "Expression explanation completed",
                ticker=ticker,
                expr=expr,
                value=value
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Expression explanation failed",
                ticker=ticker,
                expr=expr,
                error=str(e)
            )
            raise
    
    async def _resolve_inputs(
        self,
        ticker: str,
        input_defs: Dict[str, Any],
        period: str,
        freq: str,
        ttm: bool,
        segment: Optional[str]
    ) -> Dict[str, Fact]:
        """Resolve all inputs for a metric calculation"""
        inputs = {}
        
        for input_name, input_def in input_defs.items():
            concepts = input_def.get("concepts", [])
            prefer_concept = input_def.get("prefer")
            input_type = input_def.get("type", "duration")
            
            # Try to get fact for this input
            fact = await self._get_best_fact(
                ticker, concepts, prefer_concept, period, freq, ttm, segment
            )
            
            if fact:
                inputs[input_name] = fact
            else:
                logger.warning(
                    "Missing input for calculation",
                    ticker=ticker,
                    input_name=input_name,
                    concepts=concepts,
                    period=period
                )
        
        return inputs
    
    async def _get_best_fact(
        self,
        ticker: str,
        concepts: List[str],
        prefer_concept: Optional[str],
        period: str,
        freq: str,
        ttm: bool,
        segment: Optional[str]
    ) -> Optional[Fact]:
        """Get the best available fact for given concepts"""
        # Try preferred concept first
        if prefer_concept and prefer_concept in concepts:
            fact = await self.facts_store.get_fact(
                ticker, prefer_concept, period, freq, ttm, segment
            )
            if fact:
                return fact
        
        # Try other concepts in order
        for concept in concepts:
            if concept == prefer_concept:
                continue
            
            fact = await self.facts_store.get_fact(
                ticker, concept, period, freq, ttm, segment
            )
            if fact:
                return fact
        
        return None
    
    async def _evaluate_expression(self, expr: str, inputs: Dict[str, Fact]) -> float:
        """Safely evaluate a mathematical expression"""
        try:
            # Replace input names with values
            expression = expr
            for input_name, fact in inputs.items():
                value = fact.value
                # Replace variable names in expression
                pattern = r'\b' + re.escape(input_name) + r'\b'
                expression = re.sub(pattern, str(value), expression)
            
            # Replace function calls
            expression = await self._replace_functions(expression, inputs)
            
            # Validate expression contains only safe operations
            if not self._is_safe_expression(expression):
                raise ValueError(f"Unsafe expression: {expression}")
            
            # Evaluate safely
            result = eval(expression, {"__builtins__": {}}, {})
            
            return float(result)
            
        except Exception as e:
            logger.error("Expression evaluation failed", expr=expr, error=str(e))
            raise ValueError(f"Failed to evaluate expression '{expr}': {str(e)}")
    
    async def _replace_functions(self, expr: str, inputs: Dict[str, Fact]) -> str:
        """Replace function calls in expression with computed values"""
        # Find function calls
        function_pattern = r'(\w+)\s*\(([^)]+)\)'
        
        def replace_function(match):
            func_name = match.group(1)
            args_str = match.group(2)
            
            if func_name in self.functions:
                # Parse arguments
                args = [arg.strip() for arg in args_str.split(',')]
                
                # Get function result
                result = self.functions[func_name](inputs, args)
                return str(result)
            else:
                # Unknown function, leave as is
                return match.group(0)
        
        return re.sub(function_pattern, replace_function, expr)
    
    def _is_safe_expression(self, expr: str) -> bool:
        """Check if expression contains only safe mathematical operations"""
        # Allow only numbers, operators, parentheses, and basic math
        safe_pattern = r'^[0-9+\-*/().\s]+$'
        return bool(re.match(safe_pattern, expr))
    
    def _avg_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate average of concept over N periods"""
        if len(args) != 2:
            raise ValueError("avg() function requires exactly 2 arguments")
        
        concept_name = args[0]
        periods = int(args[1])
        
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # For now, return the single value (would need multiple periods in real implementation)
        return inputs[concept_name].value
    
    def _ttm_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate trailing twelve months"""
        if len(args) != 1:
            raise ValueError("ttm() function requires exactly 1 argument")
        
        concept_name = args[0]
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # For now, return the single value (would sum 4 quarters in real implementation)
        return inputs[concept_name].value
    
    def _yoy_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate year-over-year growth"""
        if len(args) != 1:
            raise ValueError("yoy() function requires exactly 1 argument")
        
        concept_name = args[0]
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # For now, return 0 (would need prior year data in real implementation)
        return 0.0
    
    def _qoq_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate quarter-over-quarter growth"""
        if len(args) != 1:
            raise ValueError("qoq() function requires exactly 1 argument")
        
        concept_name = args[0]
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # For now, return 0 (would need prior quarter data in real implementation)
        return 0.0
    
    def _cagr_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate compound annual growth rate"""
        if len(args) != 2:
            raise ValueError("cagr() function requires exactly 2 arguments")
        
        concept_name = args[0]
        periods = int(args[1])
        
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # For now, return 0 (would need historical data in real implementation)
        return 0.0
    
    def _per_share_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate per-share amount"""
        if len(args) != 1:
            raise ValueError("per_share() function requires exactly 1 argument")
        
        concept_name = args[0]
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")
        
        # Get shares (would need to fetch shares data in real implementation)
        shares = 1000000  # Placeholder
        
        return inputs[concept_name].value / shares
    
    def _format_value(self, value: float, output_type: OutputType) -> float:
        """Format value according to output type"""
        if output_type == OutputType.PERCENT:
            return value * 100  # Convert decimal to percentage
        else:
            return value
    
    def _build_citations(self, inputs: Dict[str, Fact]) -> List[Dict[str, Any]]:
        """Build citation list from input facts"""
        citations = []
        
        for fact in inputs.values():
            citation = {
                "concept": fact.concept,
                "value": fact.value,
                "unit": fact.unit,
                "period": fact.period,
                "source_url": fact.url,
                "accession": fact.accession,
                "fragment_id": fact.fragment_id,
                "dimensions": fact.dimensions
            }
            citations.append(citation)
        
        return citations
    
    def _collect_quality_flags(self, inputs: Dict[str, Fact], metric_def: Dict[str, Any]) -> List[str]:
        """Collect quality flags from inputs and metric definition"""
        flags = []
        
        for fact in inputs.values():
            flags.extend(fact.quality_flags)
        
        # Add metric-specific flags
        if metric_def.get("notes"):
            flags.append(f"note: {metric_def['notes']}")
        
        return list(set(flags))  # Remove duplicates
    
    def _parse_expression_inputs(self, expr: str) -> List[str]:
        """Parse expression to find input variable names"""
        # Simple regex to find variable names (words that aren't functions)
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
        
        # Remove function names
        function_names = set(self.functions.keys())
        input_vars = [var for var in variables if var not in function_names]
        
        return list(set(input_vars))  # Remove duplicates
    
    async def _resolve_concepts(
        self,
        ticker: str,
        concepts: List[str],
        period: str,
        freq: str,
        ttm: bool
    ) -> Dict[str, Fact]:
        """Resolve concepts to facts"""
        inputs = {}
        
        for concept in concepts:
            fact = await self.facts_store.get_fact(ticker, concept, period, freq, ttm)
            if fact:
                inputs[concept] = fact
        
        return inputs

