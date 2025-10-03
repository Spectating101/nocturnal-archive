"""
FinSight Calculations Engine
Safe expression evaluation with provenance tracking
"""

import re
import structlog
from typing import Any, Dict, List, Optional, Union, Tuple, Set
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
            input_defs = self.kpi_registry.get_metric_inputs(metric)
            if not input_defs:
                logger.warning("No inputs found for metric", metric=metric)

            optional_inputs = self._find_optional_inputs(metric_def.get("expr", ""))

            inputs = await self._resolve_inputs(
                ticker, input_defs, period, freq, ttm, segment, optional_inputs
            )

            missing_required_inputs = [
                name for name in input_defs.keys()
                if name not in inputs and name not in optional_inputs
            ]
            if missing_required_inputs:
                raise ValueError(
                    f"Missing required inputs for metric '{metric}': {', '.join(sorted(missing_required_inputs))}"
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

            # Add validation flags (sanity checks)
            validation_flags = self._validate_calculation_result(ticker, metric, value, inputs)
            quality_flags.extend(validation_flags)

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

            # Find optional inputs in expression
            optional_inputs = self._find_optional_inputs(expr)

            # Resolve inputs
            inputs = await self._resolve_concepts(
                ticker, input_concepts, period, freq, ttm, optional_inputs
            )
            
            # Evaluate expression
            value = await self._evaluate_expression(expr, inputs)
            
            # Build result
            citations = self._build_citations(inputs)
            quality_flags = self._collect_quality_flags(inputs, {"expr": expr})

            # Add validation flags (sanity checks)
            # Try to extract metric name from expression for better validation
            metric_name = "custom" if "-" in expr else expr.split()[0] if expr else "custom"
            validation_flags = self._validate_calculation_result(ticker, metric_name, value, inputs)
            quality_flags.extend(validation_flags)

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
        segment: Optional[str],
        optional_inputs: Set[str]
    ) -> Dict[str, Fact]:
        """Resolve all inputs for a metric calculation"""
        inputs: Dict[str, Fact] = {}
        sec_adapter = None
        concept_map: Dict[str, List[str]] = {}

        try:
            from src.adapters.sec_facts import get_sec_facts_adapter
            sec_adapter = get_sec_facts_adapter()
            concept_map = getattr(sec_adapter, "concept_map", {})
        except Exception as e:
            logger.debug("SEC adapter unavailable for input resolution", error=str(e))

        for input_name, input_def in input_defs.items():
            concepts = input_def.get("concepts", [])
            prefer_concept = input_def.get("prefer")

            # Try to get fact for this input
            fact = await self._get_best_fact(
                ticker, concepts, prefer_concept, period, freq, ttm, segment
            )

            if fact:
                inputs[input_name] = fact
            else:
                if input_name in optional_inputs:
                    logger.info(
                        "Optional input missing, defaulting to zero",
                        ticker=ticker,
                        input_name=input_name,
                        concepts=concepts,
                        period=period
                    )
                else:
                    logger.warning(
                        "Missing input for calculation",
                        ticker=ticker,
                        input_name=input_name,
                        concepts=concepts,
                        period=period
                    )

        adapter_supported = [
            name for name in input_defs.keys()
            if concept_map and name in concept_map
        ]

        if sec_adapter and adapter_supported:
            accessions = {
                fact.accession for fact in inputs.values() if fact.accession
            }
            missing_supported = [
                name for name in adapter_supported if name not in inputs
            ]

            need_same_filing = len(accessions) > 1 and len(inputs) > 1

            requested_inputs = set(missing_supported)
            if need_same_filing:
                requested_inputs.update(adapter_supported)

            if requested_inputs:
                try:
                    adapter_facts = await sec_adapter.get_facts_from_same_filing(
                        ticker,
                        list(requested_inputs),
                        period=period,
                        freq=freq
                    )
                    for input_name, fact_data in adapter_facts.items():
                        inputs[input_name] = self._fact_data_to_object(fact_data)
                except Exception as e:
                    logger.debug(
                        "Failed to resolve adapter inputs from same filing",
                        error=str(e)
                    )

        # Log accession mismatches if still present
        accessions = {
            fact.accession for fact in inputs.values() if fact.accession
        }
        if len(accessions) > 1:
            logger.warning(
                "Input accession mismatch detected",
                ticker=ticker,
                period=period,
                freq=freq,
                accessions=list(accessions)
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
                return self._convert_store_fact(fact)
        
        # Try other concepts in order
        for concept in concepts:
            if concept == prefer_concept:
                continue
            
            fact = await self.facts_store.get_fact(
                ticker, concept, period, freq, ttm, segment
            )
            if fact:
                return self._convert_store_fact(fact)
        
        return None

    def _fact_data_to_object(self, fact_data: Dict[str, Any]) -> Fact:
        """Convert fact data dictionary (adapter response) into Fact object"""
        period_type_raw = fact_data.get("period_type") or fact_data.get("periodType") or PeriodType.DURATION.value
        try:
            period_type = PeriodType(period_type_raw)
        except Exception:
            period_type = PeriodType.DURATION

        return Fact(
            concept=fact_data.get("concept", ""),
            value=float(fact_data.get("value", 0.0) or 0.0),
            unit=fact_data.get("unit", "USD") or "USD",
            period=fact_data.get("period") or fact_data.get("end_date") or "",
            period_type=period_type,
            accession=fact_data.get("accession", ""),
            fragment_id=fact_data.get("fragment_id"),
            url=fact_data.get("url", ""),
            dimensions=fact_data.get("dimensions", {}) or {},
            quality_flags=list(fact_data.get("quality_flags", []) or [])
        )

    def _convert_store_fact(self, store_fact: Any) -> Fact:
        """Convert FactsStore Fact into CalculationEngine Fact"""
        period_type_attr = getattr(store_fact, "period_type", PeriodType.DURATION)
        if isinstance(period_type_attr, PeriodType):
            period_type = period_type_attr
        else:
            period_type_value = getattr(period_type_attr, "value", None) or str(period_type_attr)
            try:
                period_type = PeriodType(period_type_value)
            except Exception:
                period_type = PeriodType.DURATION

        return Fact(
            concept=getattr(store_fact, "concept", ""),
            value=float(getattr(store_fact, "value", 0.0) or 0.0),
            unit=getattr(store_fact, "unit", "USD") or "USD",
            period=getattr(store_fact, "period", ""),
            period_type=period_type,
            accession=getattr(store_fact, "accession", ""),
            fragment_id=getattr(store_fact, "fragment_id", None),
            url=getattr(store_fact, "url", ""),
            dimensions=getattr(store_fact, "dimensions", {}) or {},
            quality_flags=list(getattr(store_fact, "quality_flags", []) or [])
        )
    
    async def _evaluate_expression(self, expr: str, inputs: Dict[str, Fact]) -> float:
        """Safely evaluate a mathematical expression"""
        try:
            # Replace input names with values
            expression = expr

            # Replace optional placeholders (variable?) first
            def replace_optional(match: re.Match) -> str:
                name = match.group(1)
                if name in inputs:
                    return str(inputs[name].value)
                return "0"

            expression = re.sub(r'([A-Za-z_][A-Za-z0-9_]*)\?', replace_optional, expression)

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
    
    async def _ttm_function_async(self, concept_name: str, current_fact: Fact) -> float:
        """Calculate actual trailing twelve months by summing 4 quarters"""
        # This needs to be implemented with proper quarterly data fetching
        # For now, return the placeholder with clear logging
        logger.info(
            "TTM calculation - using approximation",
            concept=concept_name,
            current_value=current_fact.value,
            note="Proper implementation requires fetching last 4 quarters"
        )
        # Return current value * 4 as approximation
        # In production, this should fetch and sum actual 4 quarters
        return current_fact.value * 4

    def _ttm_function(self, inputs: Dict[str, Fact], args: List[str]) -> float:
        """Calculate trailing twelve months - Synchronous wrapper"""
        if len(args) != 1:
            raise ValueError("ttm() function requires exactly 1 argument")

        concept_name = args[0]
        if concept_name not in inputs:
            raise ValueError(f"Unknown concept: {concept_name}")

        # For synchronous context, use approximation
        # TODO: Refactor to async or implement proper quarterly fetch here
        fact_value = inputs[concept_name].value
        logger.warning(
            "TTM approximation used",
            concept=concept_name,
            value=fact_value,
            ttm_estimate=fact_value * 4
        )
        return fact_value * 4
    
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

    def _validate_calculation_result(
        self,
        ticker: str,
        metric: str,
        result: float,
        inputs: Dict[str, Fact]
    ) -> List[str]:
        """Validate calculation makes business sense - catch data errors"""
        flags = []
        from datetime import datetime

        # Check 1: Gross profit shouldn't exceed revenue
        if metric == "grossProfit" and "revenue" in inputs:
            revenue = inputs["revenue"].value
            if result > revenue:
                flags.append(f"INVALID_GROSS_PROFIT_EXCEEDS_REVENUE:{result}>{revenue}")

        # Check 2: COGS should be positive
        if "costOfRevenue" in inputs:
            cogs = inputs["costOfRevenue"].value
            if cogs < 0:
                flags.append(f"NEGATIVE_COGS:{cogs}")

        # Check 3: Period mismatch detection (different dates for inputs)
        periods = {name: fact.period for name, fact in inputs.items() if fact.period}
        unique_periods = set(periods.values())
        if len(unique_periods) > 1:
            flags.append(f"PERIOD_MISMATCH:{','.join(unique_periods)}")

        # Check 4: Data freshness - warn if data is old
        current_year = datetime.now().year
        for name, fact in inputs.items():
            if fact.period:
                try:
                    # Extract year from period (supports 2025-Q2, 2025-06-30, etc.)
                    year = int(fact.period.split("-")[0])
                    age_years = current_year - year
                    if age_years > 2:
                        flags.append(f"OLD_DATA_{name}:{fact.period}_{age_years}_years_old")
                except (ValueError, IndexError):
                    pass  # Skip if period format is unexpected

        # Check 5: Result reasonableness (not zero or extremely large)
        if result == 0:
            flags.append("ZERO_RESULT")
        elif abs(result) > 1e15:  # $1 quadrillion
            flags.append(f"UNREASONABLY_LARGE_RESULT:{result}")

        return flags

    def _find_optional_inputs(self, expr: str) -> Set[str]:
        """Identify optional inputs marked with '?' in an expression"""
        if not expr:
            return set()
        return {
            match.group(1)
            for match in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\?', expr)
        }
    
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
        ttm: bool,
        optional_inputs: Set[str]
    ) -> Dict[str, Fact]:
        """Resolve concepts to facts"""
        inputs: Dict[str, Fact] = {}
        sec_adapter = None
        concept_map: Dict[str, List[str]] = {}

        try:
            from src.adapters.sec_facts import get_sec_facts_adapter
            sec_adapter = get_sec_facts_adapter()
            concept_map = getattr(sec_adapter, "concept_map", {})
        except Exception as e:
            logger.debug("SEC adapter unavailable for concept resolution", error=str(e))

        if sec_adapter:
            try:
                same_filing = await sec_adapter.get_facts_from_same_filing(
                    ticker,
                    concepts,
                    period=period,
                    freq=freq
                )
                if same_filing:
                    for concept_name, fact_data in same_filing.items():
                        inputs[concept_name] = self._fact_data_to_object(fact_data)
                    return inputs
            except Exception as e:
                logger.warning(
                    "Failed to resolve concepts from same filing",
                    ticker=ticker,
                    error=str(e)
                )

        for concept in concepts:
            candidate_concepts: List[str] = []
            if ":" in concept:
                candidate_concepts = [concept]
            elif concept in concept_map:
                candidate_concepts = [
                    f"us-gaap:{name}" if ":" not in name else name
                    for name in concept_map[concept]
                ]
            else:
                candidate_concepts = [concept]

            store_fact = None
            for candidate in candidate_concepts:
                store_fact = await self.facts_store.get_fact(ticker, candidate, period, freq, ttm)
                if store_fact:
                    break

            if store_fact:
                inputs[concept] = self._convert_store_fact(store_fact)
            else:
                if concept in optional_inputs:
                    logger.info("Optional concept missing", concept=concept, ticker=ticker)
                else:
                    logger.warning("Concept missing for expression", concept=concept, ticker=ticker)

        return inputs

