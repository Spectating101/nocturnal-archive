"""
Data visualization service for generating charts, graphs, and visual representations
of research data and findings.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

@dataclass
class ChartData:
    """Represents chart data for visualization."""
    chart_type: str
    title: str
    labels: List[str]
    data: List[Any]
    colors: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None

@dataclass
class Visualization:
    """Represents a complete visualization."""
    id: str
    title: str
    description: str
    chart_data: ChartData
    html_code: str
    config: Dict[str, Any]

class DataVisualizer:
    """Service for creating data visualizations from research data."""
    
    def __init__(self):
        self.default_colors = [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
            '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
        ]
    
    def create_keyword_frequency_chart(self, keywords: List[Tuple[str, int]], title: str = "Keyword Frequency") -> Visualization:
        """Create a bar chart showing keyword frequencies."""
        labels = [kw[0] for kw in keywords[:10]]  # Top 10 keywords
        data = [kw[1] for kw in keywords[:10]]
        
        chart_data = ChartData(
            chart_type="bar",
            title=title,
            labels=labels,
            data=data,
            colors=self.default_colors[:len(labels)]
        )
        
        html_code = self._generate_chart_html(chart_data, "keyword-frequency")
        config = {
            "type": "keyword_frequency",
            "data_points": len(labels),
            "max_frequency": max(data) if data else 0
        }
        
        return Visualization(
            id="keyword_frequency",
            title=title,
            description=f"Frequency distribution of {len(labels)} most common keywords",
            chart_data=chart_data,
            html_code=html_code,
            config=config
        )
    
    def create_source_analysis_chart(self, sources: List[Dict[str, Any]], title: str = "Source Analysis") -> Visualization:
        """Create a pie chart showing source distribution."""
        source_types = {}
        for source in sources:
            source_type = source.get('type', 'Unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        labels = list(source_types.keys())
        data = list(source_types.values())
        
        chart_data = ChartData(
            chart_type="pie",
            title=title,
            labels=labels,
            data=data,
            colors=self.default_colors[:len(labels)]
        )
        
        html_code = self._generate_chart_html(chart_data, "source-analysis")
        config = {
            "type": "source_analysis",
            "total_sources": sum(data),
            "source_types": len(labels)
        }
        
        return Visualization(
            id="source_analysis",
            title=title,
            description=f"Distribution of {sum(data)} sources across {len(labels)} categories",
            chart_data=chart_data,
            html_code=html_code,
            config=config
        )
    
    def create_timeline_chart(self, events: List[Dict[str, Any]], title: str = "Research Timeline") -> Visualization:
        """Create a timeline chart showing research events."""
        labels = [event.get('date', 'Unknown') for event in events]
        data = [event.get('importance', 1) for event in events]
        
        chart_data = ChartData(
            chart_type="line",
            title=title,
            labels=labels,
            data=data,
            colors=[self.default_colors[0]]
        )
        
        html_code = self._generate_chart_html(chart_data, "timeline")
        config = {
            "type": "timeline",
            "events": len(events),
            "date_range": f"{min(labels)} to {max(labels)}" if labels else "Unknown"
        }
        
        return Visualization(
            id="timeline",
            title=title,
            description=f"Timeline of {len(events)} research events",
            chart_data=chart_data,
            html_code=html_code,
            config=config
        )
    
    def create_relevance_heatmap(self, findings: List[Dict[str, Any]], title: str = "Finding Relevance Heatmap") -> Visualization:
        """Create a heatmap showing finding relevance scores."""
        categories = list(set(finding.get('category', 'General') for finding in findings))
        relevance_scores = [finding.get('relevance', 0) for finding in findings]
        
        chart_data = ChartData(
            chart_type="heatmap",
            title=title,
            labels=categories,
            data=relevance_scores,
            colors=self.default_colors[:len(categories)]
        )
        
        html_code = self._generate_heatmap_html(chart_data, "relevance-heatmap")
        config = {
            "type": "relevance_heatmap",
            "findings": len(findings),
            "categories": len(categories),
            "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        }
        
        return Visualization(
            id="relevance_heatmap",
            title=title,
            description=f"Relevance heatmap for {len(findings)} findings across {len(categories)} categories",
            chart_data=chart_data,
            html_code=html_code,
            config=config
        )
    
    def create_citation_network(self, citations: List[Dict[str, Any]], title: str = "Citation Network") -> Visualization:
        """Create a network visualization of citations."""
        nodes = []
        edges = []
        
        for citation in citations:
            nodes.append({
                'id': citation.get('id', 'unknown'),
                'label': citation.get('title', 'Unknown')[:50] + '...',
                'group': citation.get('source_type', 'web')
            })
        
        chart_data = ChartData(
            chart_type="network",
            title=title,
            labels=[node['label'] for node in nodes],
            data=nodes,
            colors=self.default_colors
        )
        
        html_code = self._generate_network_html(chart_data, "citation-network")
        config = {
            "type": "citation_network",
            "nodes": len(nodes),
            "edges": len(edges),
            "source_types": len(set(node['group'] for node in nodes))
        }
        
        return Visualization(
            id="citation_network",
            title=title,
            description=f"Network visualization of {len(nodes)} citations",
            chart_data=chart_data,
            html_code=html_code,
            config=config
        )
    
    def generate_research_dashboard(self, research_data: Dict[str, Any]) -> str:
        """Generate a complete research dashboard with multiple visualizations."""
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Research Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .dashboard { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 30px; }
                .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
                .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-number { font-size: 24px; font-weight: bold; color: #3B82F6; }
                .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>Research Dashboard</h1>
                    <p>Generated on: {timestamp}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{total_sources}</div>
                        <div class="stat-label">Sources Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_findings}</div>
                        <div class="stat-label">Key Findings</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_keywords}</div>
                        <div class="stat-label">Keywords Identified</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_relevance}</div>
                        <div class="stat-label">Avg Relevance</div>
                    </div>
                </div>
                
                <div class="charts-grid">
                    <div class="chart-container">
                        <div class="chart-title">Keyword Frequency</div>
                        <canvas id="keywordChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">Source Distribution</div>
                        <canvas id="sourceChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">Relevance Heatmap</div>
                        <canvas id="relevanceChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">Research Timeline</div>
                        <canvas id="timelineChart"></canvas>
                    </div>
                </div>
            </div>
            
            <script>
                {chart_scripts}
            </script>
        </body>
        </html>
        """
        
        # Generate chart scripts
        chart_scripts = self._generate_dashboard_scripts(research_data)
        
        # Fill in template
        dashboard_html = dashboard_html.format(
            timestamp=research_data.get('timestamp', 'Unknown'),
            total_sources=research_data.get('total_sources', 0),
            total_findings=len(research_data.get('findings', [])),
            total_keywords=len(research_data.get('keywords', [])),
            avg_relevance=round(research_data.get('avg_relevance', 0), 2),
            chart_scripts=chart_scripts
        )
        
        return dashboard_html
    
    def _generate_chart_html(self, chart_data: ChartData, chart_id: str) -> str:
        """Generate HTML for a Chart.js chart."""
        html = f"""
        <div style="width: 100%; height: 400px;">
            <canvas id="{chart_id}"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx, {{
                type: '{chart_data.chart_type}',
                data: {{
                    labels: {json.dumps(chart_data.labels)},
                    datasets: [{{
                        label: '{chart_data.title}',
                        data: {json.dumps(chart_data.data)},
                        backgroundColor: {json.dumps(chart_data.colors)},
                        borderColor: {json.dumps(chart_data.colors)},
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{chart_data.title}'
                        }}
                    }}
                }}
            }});
        </script>
        """
        return html
    
    def _generate_heatmap_html(self, chart_data: ChartData, chart_id: str) -> str:
        """Generate HTML for a heatmap visualization."""
        html = f"""
        <div style="width: 100%; height: 400px;">
            <canvas id="{chart_id}"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(chart_data.labels)},
                    datasets: [{{
                        data: {json.dumps(chart_data.data)},
                        backgroundColor: {json.dumps(chart_data.colors)},
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{chart_data.title}'
                        }}
                    }}
                }}
            }});
        </script>
        """
        return html
    
    def _generate_network_html(self, chart_data: ChartData, chart_id: str) -> str:
        """Generate HTML for a network visualization."""
        # Simplified network visualization using Chart.js
        html = f"""
        <div style="width: 100%; height: 400px;">
            <canvas id="{chart_id}"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx, {{
                type: 'scatter',
                data: {{
                    datasets: [{{
                        label: '{chart_data.title}',
                        data: {json.dumps(chart_data.data)},
                        backgroundColor: {json.dumps(chart_data.colors)}
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{chart_data.title}'
                        }}
                    }}
                }}
            }});
        </script>
        """
        return html
    
    def _generate_dashboard_scripts(self, research_data: Dict[str, Any]) -> str:
        """Generate JavaScript for dashboard charts."""
        scripts = []
        
        # Keyword frequency chart
        if 'keywords' in research_data:
            keywords = research_data['keywords'][:10]
            labels = [kw[0] for kw in keywords]
            data = [kw[1] for kw in keywords]
            
            scripts.append(f"""
            new Chart(document.getElementById('keywordChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Frequency',
                        data: {json.dumps(data)},
                        backgroundColor: {json.dumps(self.default_colors[:len(labels)])}
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
            """)
        
        # Source distribution chart
        if 'sources' in research_data:
            source_types = {}
            for source in research_data['sources']:
                source_type = source.get('type', 'Unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1
            
            labels = list(source_types.keys())
            data = list(source_types.values())
            
            scripts.append(f"""
            new Chart(document.getElementById('sourceChart').getContext('2d'), {{
                type: 'pie',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        data: {json.dumps(data)},
                        backgroundColor: {json.dumps(self.default_colors[:len(labels)])}
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
            """)
        
        return "\n".join(scripts)

# Global instance
data_visualizer = DataVisualizer()
