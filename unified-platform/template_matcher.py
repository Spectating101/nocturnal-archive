#!/usr/bin/env python3
"""
Template Matcher - Pre-built templates for common operations
Eliminates LLM calls for standard statistical operations
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class TemplateMatch:
    template_name: str
    code: str
    confidence: float
    variables: Dict[str, Any]

class TemplateMatcher:
    """Matches common queries to pre-built code templates"""
    
    def __init__(self):
        self.templates = {
            "mean": {
                "patterns": [
                    r"calculate\s+mean\s+of\s+(.+)",
                    r"mean\s+of\s+(.+)",
                    r"average\s+of\s+(.+)",
                    r"what\s+is\s+the\s+mean\s+of\s+(.+)"
                ],
                "code": "import numpy as np\ndata = {data}\nresult = np.mean(data)\nprint(f'Mean: {result}')",
                "variables": ["data"]
            },
            "median": {
                "patterns": [
                    r"calculate\s+median\s+of\s+(.+)",
                    r"median\s+of\s+(.+)",
                    r"what\s+is\s+the\s+median\s+of\s+(.+)"
                ],
                "code": "import numpy as np\ndata = {data}\nresult = np.median(data)\nprint(f'Median: {result}')",
                "variables": ["data"]
            },
            "std": {
                "patterns": [
                    r"calculate\s+standard\s+deviation\s+of\s+(.+)",
                    r"std\s+of\s+(.+)",
                    r"standard\s+deviation\s+of\s+(.+)"
                ],
                "code": "import numpy as np\ndata = {data}\nresult = np.std(data)\nprint(f'Standard Deviation: {result}')",
                "variables": ["data"]
            },
            "ols": {
                "patterns": [
                    r"ols\s+regression\s+(.+)",
                    r"linear\s+regression\s+(.+)",
                    r"regress\s+(.+)",
                    r"fit\s+line\s+(.+)"
                ],
                "code": "import statsmodels.api as sm\nimport numpy as np\nX = {X}\ny = {y}\nX = sm.add_constant(X)\nmodel = sm.OLS(y, X).fit()\nprint(model.summary())",
                "variables": ["X", "y"]
            },
            "ttest": {
                "patterns": [
                    r"t.test\s+(.+)",
                    r"t-test\s+(.+)",
                    r"compare\s+means\s+(.+)",
                    r"test\s+difference\s+(.+)"
                ],
                "code": "from scipy import stats\ngroup1 = {group1}\ngroup2 = {group2}\nstat, p_value = stats.ttest_ind(group1, group2)\nprint(f'T-statistic: {{stat}}, P-value: {{p_value}}')",
                "variables": ["group1", "group2"]
            },
            "correlation": {
                "patterns": [
                    r"correlation\s+between\s+(.+)",
                    r"correlate\s+(.+)",
                    r"relationship\s+between\s+(.+)"
                ],
                "code": "import numpy as np\nx = {x}\ny = {y}\ncorrelation = np.corrcoef(x, y)[0, 1]\nprint(f'Correlation: {correlation}')",
                "variables": ["x", "y"]
            },
            "histogram": {
                "patterns": [
                    r"histogram\s+of\s+(.+)",
                    r"plot\s+distribution\s+of\s+(.+)",
                    r"frequency\s+of\s+(.+)"
                ],
                "code": "import matplotlib.pyplot as plt\nimport numpy as np\ndata = {data}\nplt.hist(data, bins=20)\nplt.title('Histogram of Data')\nplt.xlabel('Value')\nplt.ylabel('Frequency')\nplt.show()",
                "variables": ["data"]
            },
            "scatter": {
                "patterns": [
                    r"scatter\s+plot\s+(.+)",
                    r"plot\s+(.+)\s+vs\s+(.+)",
                    r"scatter\s+(.+)"
                ],
                "code": "import matplotlib.pyplot as plt\nx = {x}\ny = {y}\nplt.scatter(x, y)\nplt.xlabel('X')\nplt.ylabel('Y')\nplt.title('Scatter Plot')\nplt.show()",
                "variables": ["x", "y"]
            }
        }
    
    def extract_data_from_query(self, query: str) -> Dict[str, Any]:
        """Extract data arrays from query text"""
        data = {}
        
        # Look for list patterns like [1,2,3,4,5]
        list_pattern = r'\[([^\]]+)\]'
        lists = re.findall(list_pattern, query)
        
        for i, list_str in enumerate(lists):
            try:
                # Parse the list
                values = [float(x.strip()) for x in list_str.split(',')]
                data[f'list_{i}'] = values
            except ValueError:
                continue
        
        # Look for variable assignments
        var_pattern = r'(\w+)\s*=\s*\[([^\]]+)\]'
        var_matches = re.findall(var_pattern, query)
        
        for var_name, list_str in var_matches:
            try:
                values = [float(x.strip()) for x in list_str.split(',')]
                data[var_name] = values
            except ValueError:
                continue
        
        return data
    
    def match_template(self, query: str) -> Optional[TemplateMatch]:
        """Match query to a template"""
        query_lower = query.lower()
        
        best_match = None
        best_confidence = 0.0
        
        for template_name, template_info in self.templates.items():
            for pattern in template_info["patterns"]:
                match = re.search(pattern, query_lower)
                if match:
                    confidence = self._calculate_confidence(query, pattern, template_info)
                    
                    if confidence > best_confidence:
                        # Extract variables
                        variables = self._extract_variables(query, template_info, match)
                        
                        best_match = TemplateMatch(
                            template_name=template_name,
                            code=template_info["code"],
                            confidence=confidence,
                            variables=variables
                        )
                        best_confidence = confidence
        
        return best_match if best_confidence > 0.6 else None
    
    def _calculate_confidence(self, query: str, pattern: str, template_info: Dict[str, Any]) -> float:
        """Calculate confidence score for template match"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for exact pattern match
        if re.search(pattern, query.lower()):
            confidence += 0.3
        
        # Boost confidence if variables are present
        data = self.extract_data_from_query(query)
        if data:
            confidence += 0.2
        
        # Boost confidence for specific keywords
        keywords = {
            "mean": ["mean", "average", "central tendency"],
            "median": ["median", "middle", "50th percentile"],
            "std": ["standard deviation", "std", "variability"],
            "ols": ["regression", "ols", "linear", "fit"],
            "ttest": ["t-test", "compare", "difference", "significance"],
            "correlation": ["correlation", "relationship", "correlate"],
            "histogram": ["histogram", "distribution", "frequency"],
            "scatter": ["scatter", "plot", "vs", "versus"]
        }
        
        template_name = None
        for name, info in self.templates.items():
            if pattern in info["patterns"]:
                template_name = name
                break
        
        if template_name and template_name in keywords:
            for keyword in keywords[template_name]:
                if keyword in query.lower():
                    confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_variables(self, query: str, template_info: Dict[str, Any], match) -> Dict[str, Any]:
        """Extract variables for template"""
        variables = {}
        data = self.extract_data_from_query(query)
        
        # Map data to template variables
        template_vars = template_info["variables"]
        data_keys = list(data.keys())
        
        for i, var_name in enumerate(template_vars):
            if i < len(data_keys):
                variables[var_name] = data[data_keys[i]]
            else:
                # Use the first available data
                variables[var_name] = data[data_keys[0]] if data_keys else []
        
        return variables
    
    def generate_code(self, template_match: TemplateMatch) -> str:
        """Generate code from template match"""
        code = template_match.code
        
        # Replace variables in code
        for var_name, var_value in template_match.variables.items():
            if isinstance(var_value, list):
                # Format list as Python list
                formatted_value = str(var_value)
            else:
                formatted_value = str(var_value)
            
            code = code.replace(f"{{{var_name}}}", formatted_value)
        
        return code
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about available templates"""
        return {
            "total_templates": len(self.templates),
            "template_names": list(self.templates.keys()),
            "total_patterns": sum(len(t["patterns"]) for t in self.templates.values()),
            "supported_operations": [
                "mean", "median", "standard deviation", "OLS regression",
                "t-test", "correlation", "histogram", "scatter plot"
            ]
        }

# Example usage and testing
if __name__ == "__main__":
    matcher = TemplateMatcher()
    
    test_queries = [
        "Calculate mean of [1,2,3,4,5]",
        "What is the median of [10,20,30,40,50]",
        "OLS regression with X=[1,2,3,4,5] and y=[2,4,6,8,10]",
        "t-test between [1,2,3,4,5] and [6,7,8,9,10]",
        "Correlation between [1,2,3,4,5] and [2,4,6,8,10]",
        "Create histogram of [1,1,2,2,3,3,4,4,5,5]",
        "Scatter plot of [1,2,3,4,5] vs [2,4,6,8,10]"
    ]
    
    print("🔧 TEMPLATE MATCHER TEST")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        match = matcher.match_template(query)
        
        if match:
            print(f"✅ Matched: {match.template_name} (confidence: {match.confidence:.2f})")
            print(f"📊 Variables: {match.variables}")
            code = matcher.generate_code(match)
            print(f"💻 Generated code:\n{code}")
        else:
            print("❌ No template match found")
    
    print(f"\n📈 Template Stats: {matcher.get_template_stats()}")
