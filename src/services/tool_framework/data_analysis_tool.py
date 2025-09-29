"""
Data Analysis Tool - Real data analysis capabilities
"""

import asyncio
import logging
import json
import statistics
import math
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAnalysisTool:
    """Real data analysis tool with statistical and analytical capabilities."""
    
    def __init__(self):
        logger.info("Data Analysis Tool initialized")
    
    async def execute(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute data analysis based on task description."""
        try:
            # Extract data from context or task description
            data = self._extract_data(task_description, context)
            analysis_type = self._determine_analysis_type(task_description, data)
            
            if analysis_type == "basic":
                return await self._basic_analysis(data)
            elif analysis_type == "statistical":
                return await self._statistical_analysis(data)
            elif analysis_type == "visualization":
                return await self._visualization_analysis(data)
            elif analysis_type == "correlation":
                return await self._correlation_analysis(data)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown analysis type: {analysis_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_data(self, task_description: str, context: Dict[str, Any]) -> List[Union[int, float, str]]:
        """Extract data from task description or context."""
        if context and "data" in context:
            return context["data"]
        
        # Try to extract data from task description
        import re
        
        # Look for list patterns like [1, 2, 3, 4, 5]
        list_pattern = r'\[([^\]]+)\]'
        matches = re.findall(list_pattern, task_description)
        
        if matches:
            try:
                # Parse the list
                data_str = matches[0]
                # Handle both numeric and string data
                if data_str.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
                    # Numeric data
                    return [float(x.strip()) for x in data_str.split(',')]
                else:
                    # String data
                    return [x.strip().strip('"\'') for x in data_str.split(',')]
            except:
                pass
        
        # Look for individual numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, task_description)
        if numbers:
            return [float(n) for n in numbers]
        
        # Default empty data
        return []
    
    def _determine_analysis_type(self, task_description: str, data: List) -> str:
        """Determine the type of analysis to perform."""
        task_lower = task_description.lower()
        
        if "visualize" in task_lower or "chart" in task_lower or "graph" in task_lower:
            return "visualization"
        elif "correlation" in task_lower or "relationship" in task_lower:
            return "correlation"
        elif "statistical" in task_lower or "statistics" in task_lower:
            return "statistical"
        elif data and all(isinstance(x, (int, float)) for x in data):
            return "statistical"
        else:
            return "basic"
    
    async def _basic_analysis(self, data: List) -> Dict[str, Any]:
        """Perform basic data analysis."""
        if not data:
            return {
                "status": "success",
                "analysis": {
                    "message": "No data provided for analysis",
                    "data_count": 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Analyze data types
        data_types = [type(x).__name__ for x in data]
        unique_types = list(set(data_types))
        
        analysis = {
            "data_count": len(data),
            "data_types": unique_types,
            "sample": data[:5] if len(data) > 5 else data,
            "unique_values": len(set(data)) if data else 0,
            "has_nulls": None in data if data else False
        }
        
        # Additional analysis for numeric data
        numeric_data = [x for x in data if isinstance(x, (int, float))]
        if numeric_data:
            analysis["numeric_count"] = len(numeric_data)
            analysis["numeric_percentage"] = len(numeric_data) / len(data) * 100
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _statistical_analysis(self, data: List) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis."""
        if not data:
            return {
                "status": "error",
                "error": "No data provided for statistical analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Convert to numeric data
        numeric_data = []
        for item in data:
            try:
                numeric_data.append(float(item))
            except (ValueError, TypeError):
                continue
        
        if not numeric_data:
            return {
                "status": "error",
                "error": "No numeric data found for statistical analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate comprehensive statistics
        analysis = {
            "count": len(numeric_data),
            "mean": statistics.mean(numeric_data),
            "median": statistics.median(numeric_data),
            "mode": statistics.mode(numeric_data) if len(set(numeric_data)) < len(numeric_data) else "No mode",
            "min": min(numeric_data),
            "max": max(numeric_data),
            "range": max(numeric_data) - min(numeric_data),
            "variance": statistics.variance(numeric_data) if len(numeric_data) > 1 else 0,
            "std_deviation": statistics.stdev(numeric_data) if len(numeric_data) > 1 else 0,
            "quartiles": {
                "q1": statistics.quantiles(numeric_data, n=4)[0] if len(numeric_data) > 3 else None,
                "q2": statistics.median(numeric_data),
                "q3": statistics.quantiles(numeric_data, n=4)[2] if len(numeric_data) > 3 else None
            }
        }
        
        # Additional insights
        analysis["insights"] = self._generate_statistical_insights(analysis)
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_statistical_insights(self, stats: Dict[str, Any]) -> List[str]:
        """Generate insights from statistical analysis."""
        insights = []
        
        # Variability insights
        cv = stats["std_deviation"] / stats["mean"] if stats["mean"] != 0 else 0
        if cv < 0.1:
            insights.append("Data shows low variability (CV < 0.1)")
        elif cv > 0.5:
            insights.append("Data shows high variability (CV > 0.5)")
        
        # Distribution insights
        if stats["mean"] > stats["median"]:
            insights.append("Data appears right-skewed (mean > median)")
        elif stats["mean"] < stats["median"]:
            insights.append("Data appears left-skewed (mean < median)")
        else:
            insights.append("Data appears approximately symmetric")
        
        # Range insights
        if stats["range"] == 0:
            insights.append("All data points are identical")
        elif stats["range"] < stats["mean"] * 0.1:
            insights.append("Data has very small range relative to mean")
        
        return insights
    
    async def _correlation_analysis(self, data: List) -> Dict[str, Any]:
        """Perform correlation analysis for paired data."""
        if len(data) < 2:
            return {
                "status": "error",
                "error": "Insufficient data for correlation analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # For simplicity, assume data is paired (x, y) values
        # In a real implementation, you'd parse structured data
        analysis = {
            "message": "Correlation analysis requires structured paired data",
            "suggestion": "Provide data as [(x1, y1), (x2, y2), ...] format",
            "data_count": len(data)
        }
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _visualization_analysis(self, data: List) -> Dict[str, Any]:
        """Generate visualization recommendations."""
        if not data:
            return {
                "status": "error",
                "error": "No data provided for visualization",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        numeric_data = [x for x in data if isinstance(x, (int, float))]
        
        recommendations = []
        
        if len(numeric_data) == len(data):
            # All numeric data
            if len(set(numeric_data)) < 10:
                recommendations.append("Bar chart (discrete values)")
            else:
                recommendations.append("Histogram (continuous distribution)")
                recommendations.append("Box plot (distribution summary)")
        else:
            # Mixed or categorical data
            recommendations.append("Bar chart (categorical data)")
            recommendations.append("Pie chart (proportions)")
        
        analysis = {
            "data_type": "numeric" if len(numeric_data) == len(data) else "mixed",
            "recommended_charts": recommendations,
            "data_summary": {
                "total_points": len(data),
                "numeric_points": len(numeric_data),
                "unique_values": len(set(data))
            }
        }
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
