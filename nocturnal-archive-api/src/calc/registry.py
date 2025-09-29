"""
FinSight KPI Registry
Loads and manages KPI definitions from YAML configuration
"""

import yaml
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = structlog.get_logger(__name__)

class KPIRegistry:
    """Registry for KPI definitions and expressions"""
    
    def __init__(self, config_path: str = "config/kpi.yml"):
        """
        Initialize KPI registry
        
        Args:
            config_path: Path to KPI configuration file
        """
        self.config_path = Path(config_path)
        self.inputs = {}
        self.metrics = {}
        self.functions = {}
        self.output_types = {}
        self.overrides = {}
        
        self._load_config()
    
    def _load_config(self):
        """Load KPI configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning("KPI config file not found", path=self.config_path)
                return
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load inputs
            self.inputs = config.get("inputs", {})
            
            # Load metrics
            self.metrics = config.get("metrics", {})
            
            # Load functions
            self.functions = config.get("functions", {})
            
            # Load output types
            self.output_types = config.get("output_types", {})
            
            # Load overrides
            self.overrides = config.get("overrides", {})
            
            logger.info(
                "KPI registry loaded",
                inputs_count=len(self.inputs),
                metrics_count=len(self.metrics),
                functions_count=len(self.functions),
                overrides_count=len(self.overrides)
            )
            
        except Exception as e:
            logger.error("Failed to load KPI config", error=str(e))
            raise
    
    def get_input(self, input_name: str) -> Optional[Dict[str, Any]]:
        """Get input definition by name"""
        return self.inputs.get(input_name)
    
    def get_metric(self, metric_name: str, cik: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get metric definition by name, with optional issuer override
        
        Args:
            metric_name: Name of the metric
            cik: Company CIK for issuer-specific overrides
            
        Returns:
            Metric definition with any issuer overrides applied
        """
        metric_def = self.metrics.get(metric_name)
        if not metric_def:
            return None
        
        # Check for issuer-specific overrides
        if cik and cik in self.overrides:
            issuer_overrides = self.overrides[cik].get("metrics", {})
            if metric_name in issuer_overrides:
                # Merge override with base definition
                metric_def = {**metric_def, **issuer_overrides[metric_name]}
        
        return metric_def
    
    def get_metric_inputs(self, metric_name: str) -> Dict[str, Any]:
        """Get input definitions for a metric"""
        metric_def = self.get_metric(metric_name)
        if not metric_def:
            return {}
        
        # Parse expression to find required inputs
        expr = metric_def.get("expr", "")
        required_inputs = self._parse_expression_inputs(expr)
        
        # Get input definitions
        inputs = {}
        for input_name in required_inputs:
            input_def = self.get_input(input_name)
            if input_def:
                inputs[input_name] = input_def
        
        return inputs
    
    def get_function(self, func_name: str) -> Optional[Dict[str, Any]]:
        """Get function definition by name"""
        return self.functions.get(func_name)
    
    def get_output_type(self, output_type: str) -> Optional[Dict[str, Any]]:
        """Get output type definition"""
        return self.output_types.get(output_type)
    
    def list_metrics(self) -> List[str]:
        """List all available metrics"""
        return list(self.metrics.keys())
    
    def list_inputs(self) -> List[str]:
        """List all available inputs"""
        return list(self.inputs.keys())
    
    def list_functions(self) -> List[str]:
        """List all available functions"""
        return list(self.functions.keys())
    
    def get_metrics_by_category(self, category: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics grouped by category
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary of metrics grouped by category
        """
        categories = {}
        
        for metric_name, metric_def in self.metrics.items():
            metric_category = metric_def.get("category", "other")
            
            if category is None or metric_category == category:
                if metric_category not in categories:
                    categories[metric_category] = {}
                categories[metric_category][metric_name] = metric_def
        
        return categories
    
    def validate_expression(self, expr: str) -> Dict[str, Any]:
        """
        Validate an expression for syntax and available inputs/functions
        
        Args:
            expr: Expression to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "inputs": [],
            "functions": []
        }
        
        try:
            # Parse expression to find inputs and functions
            inputs = self._parse_expression_inputs(expr)
            functions = self._parse_expression_functions(expr)
            
            result["inputs"] = inputs
            result["functions"] = functions
            
            # Check if inputs exist
            for input_name in inputs:
                if input_name not in self.inputs:
                    result["errors"].append(f"Unknown input: {input_name}")
                    result["valid"] = False
            
            # Check if functions exist
            for func_name in functions:
                if func_name not in self.functions:
                    result["errors"].append(f"Unknown function: {func_name}")
                    result["valid"] = False
            
            # Basic syntax validation
            if not self._is_valid_syntax(expr):
                result["errors"].append("Invalid expression syntax")
                result["valid"] = False
            
        except Exception as e:
            result["errors"].append(f"Parse error: {str(e)}")
            result["valid"] = False
        
        return result
    
    def _parse_expression_inputs(self, expr: str) -> List[str]:
        """Parse expression to find input variable names"""
        import re
        
        # Find variable names (words that aren't functions)
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
        
        # Remove function names
        function_names = set(self.functions.keys())
        input_vars = [var for var in variables if var not in function_names]
        
        return list(set(input_vars))  # Remove duplicates
    
    def _parse_expression_functions(self, expr: str) -> List[str]:
        """Parse expression to find function calls"""
        import re
        
        # Find function calls
        function_pattern = r'(\w+)\s*\('
        functions = re.findall(function_pattern, expr)
        
        return list(set(functions))  # Remove duplicates
    
    def _is_valid_syntax(self, expr: str) -> bool:
        """Basic syntax validation for expressions"""
        import re
        
        # Check for balanced parentheses
        paren_count = 0
        for char in expr:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count < 0:
                    return False
        
        if paren_count != 0:
            return False
        
        # Check for valid characters
        valid_pattern = r'^[a-zA-Z0-9+\-*/().\s_,]+$'
        return bool(re.match(valid_pattern, expr))
    
    def reload(self):
        """Reload configuration from file"""
        logger.info("Reloading KPI registry")
        self._load_config()
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry contents"""
        return {
            "inputs_count": len(self.inputs),
            "metrics_count": len(self.metrics),
            "functions_count": len(self.functions),
            "output_types_count": len(self.output_types),
            "overrides_count": len(self.overrides),
            "config_path": str(self.config_path),
            "last_modified": self.config_path.stat().st_mtime if self.config_path.exists() else None
        }

