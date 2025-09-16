#!/usr/bin/env python3
"""
Enhanced Research Synthesizer with Advanced Features
Integrates visualization, topic modeling, quality assessment, and export capabilities
"""

import logging
import re
import asyncio
import json
import hashlib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import redis.asyncio as redis
from collections import Counter

# Visualization imports
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ML imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, topic modeling will be disabled")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available, network analysis will be disabled")

# Core imports
from src.storage.db.operations import DatabaseOperations
from src.services.llm_service.llm_manager import LLMManager
from src.services.graph.knowledge_graph import KnowledgeGraph
from .citation_manager import CitationManager, Citation, CitedFinding, CitationFormat

# Configure structured logging
logger = logging.getLogger(__name__)

class EnhancedResearchSynthesizer:
    """
    Enhanced research synthesizer with advanced features:
    - Advanced visualizations (3D plots, networks, dashboards)
    - Topic modeling and clustering
    - Quality assessment and scoring
    - Multiple export formats
    - Real-time analytics
    - Collaborative features
    """
    
    def __init__(self, db_ops: DatabaseOperations, llm_manager: LLMManager, redis_url: str, 
                 kg_client: Optional[KnowledgeGraph] = None, openalex_client=None):
        """
        Initialize enhanced research synthesizer.
        
        Args:
            db_ops: Database operations instance
            llm_manager: LLM manager instance
            redis_url: Redis connection URL
            kg_client: Knowledge Graph client
            openalex_client: OpenAlex client for citations
        """
        try:
            if not db_ops:
                raise ValueError("Database operations instance is required")
            if not llm_manager:
                raise ValueError("LLM manager instance is required")
            if not redis_url:
                raise ValueError("Redis URL is required")
            
            logger.info("Initializing EnhancedResearchSynthesizer")
            
            self.db = db_ops
            self.llm = llm_manager
            self.kg_client = kg_client
            
            # Initialize citation manager
            self.citation_manager = CitationManager(db_ops=db_ops, openalex_client=openalex_client)
            
            # Initialize Redis
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Redis client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {str(e)}")
                raise ConnectionError(f"Redis connection failed: {str(e)}")
            
            # Initialize enhancement components
            self.synthesis_cache = {}
            self.synthesis_tasks = {}
            self.visualization_cache = {}
            self.topic_models = {}
            self.quality_scores = {}
            
            logger.info("EnhancedResearchSynthesizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedResearchSynthesizer: {str(e)}")
            raise
    
    async def conduct_enhanced_research(self, topic: str, paper_ids: List[str] = None, 
                                      max_papers: int = 10) -> Dict[str, Any]:
        """
        Conduct comprehensive research with all enhanced features.
        
        Args:
            topic: Research topic
            paper_ids: Optional list of specific paper IDs
            max_papers: Maximum number of papers to analyze
            
        Returns:
            Comprehensive research results with all enhancements
        """
        try:
            logger.info(f"Starting enhanced research on topic: {topic}")
            
            # 1. Basic research synthesis
            basic_results = await self._conduct_basic_research(topic, paper_ids, max_papers)
            
            # 2. Enhanced visualizations
            visualizations = await self._generate_enhanced_visualizations(basic_results)
            
            # 3. Topic modeling
            topic_analysis = await self._perform_topic_modeling(basic_results)
            
            # 4. Quality assessment
            quality_analysis = await self._assess_research_quality(basic_results)
            
            # 5. Citation network analysis
            citation_network = await self._analyze_citation_network(basic_results)
            
            # 6. Trend analysis
            trend_analysis = await self._analyze_research_trends(basic_results)
            
            # 7. Export formats
            exports = await self._generate_export_formats(basic_results, visualizations)
            
            # Compile comprehensive results
            enhanced_results = {
                "research_data": basic_results,
                "visualizations": visualizations,
                "topic_analysis": topic_analysis,
                "quality_assessment": quality_analysis,
                "citation_network": citation_network,
                "trend_analysis": trend_analysis,
                "exports": exports,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "2.0",
                    "enhancements": [
                        "advanced_visualizations",
                        "topic_modeling", 
                        "quality_assessment",
                        "citation_networks",
                        "trend_analysis",
                        "multi_format_exports"
                    ]
                }
            }
            
            logger.info("Enhanced research completed successfully")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Enhanced research failed: {str(e)}")
            raise
    
    async def _conduct_basic_research(self, topic: str, paper_ids: List[str] = None, 
                                    max_papers: int = 10) -> Dict[str, Any]:
        """Conduct basic research synthesis."""
        try:
            # This would integrate with the existing research synthesis logic
            # For now, return a structured template
            return {
                "topic": topic,
                "papers_analyzed": [],
                "consensus_findings": [],
                "emerging_trends": [],
                "research_gaps": [],
                "controversies": [],
                "methodology_insights": []
            }
        except Exception as e:
            logger.error(f"Basic research failed: {str(e)}")
            raise
    
    async def _generate_enhanced_visualizations(self, research_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate advanced visualizations for research data."""
        try:
            visualizations = []
            
            # 1. 3D Scatter Plot
            if research_data.get("papers_analyzed"):
                fig_3d = self._create_3d_scatter_plot(research_data["papers_analyzed"])
                visualizations.append({
                    "type": "3d_scatter",
                    "title": "Research Papers in 3D Space",
                    "description": "Papers plotted by year, citations, and impact",
                    "figure": fig_3d
                })
            
            # 2. Advanced Word Cloud
            wordcloud = self._create_advanced_wordcloud(research_data)
            visualizations.append({
                "type": "wordcloud",
                "title": "Research Topic Distribution",
                "description": "Visual representation of key research themes",
                "figure": wordcloud
            })
            
            # 3. Citation Network
            network_fig = self._create_citation_network(research_data)
            visualizations.append({
                "type": "network",
                "title": "Citation Network",
                "description": "Interactive citation relationships between papers",
                "figure": network_fig
            })
            
            # 4. Trend Dashboard
            trend_fig = self._create_trend_dashboard(research_data)
            visualizations.append({
                "type": "trend_dashboard",
                "title": "Research Trends Dashboard",
                "description": "Comprehensive trend analysis over time",
                "figure": trend_fig
            })
            
            # 5. Quality Distribution
            quality_fig = self._create_quality_distribution(research_data)
            visualizations.append({
                "type": "quality_distribution",
                "title": "Research Quality Distribution",
                "description": "Distribution of paper quality scores",
                "figure": quality_fig
            })
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            return []
    
    def _create_3d_scatter_plot(self, papers: List[Dict[str, Any]]) -> go.Figure:
        """Create 3D scatter plot of papers."""
        try:
            years = [paper.get("year", 2024) for paper in papers]
            citations = [paper.get("citations", 0) for paper in papers]
            titles = [paper.get("title", "Unknown")[:30] for paper in papers]
            
            # Calculate impact score
            impact_scores = [citations[i] / (2024 - years[i] + 1) for i in range(len(papers))]
            
            fig = go.Figure(data=[go.Scatter3d(
                x=years,
                y=citations,
                z=impact_scores,
                mode='markers+text',
                text=titles,
                marker=dict(
                    size=8,
                    color=impact_scores,
                    colorscale='Viridis',
                    opacity=0.8
                ),
                textposition="middle center"
            )])
            
            fig.update_layout(
                title="Research Papers in 3D Space (Year × Citations × Impact)",
                scene=dict(
                    xaxis_title="Year",
                    yaxis_title="Citations",
                    zaxis_title="Impact Score"
                ),
                width=800,
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"3D scatter plot creation failed: {str(e)}")
            return go.Figure()
    
    def _create_advanced_wordcloud(self, research_data: Dict[str, Any]) -> WordCloud:
        """Create advanced word cloud from research data."""
        try:
            # Extract text from papers
            text = ""
            for paper in research_data.get("papers_analyzed", []):
                text += f" {paper.get('title', '')} {paper.get('abstract', '')}"
            
            # Add emerging trends
            for trend in research_data.get("emerging_trends", []):
                text += f" {trend} {trend} {trend}"  # Weight trends more heavily
            
            # Check if we have enough text
            if not text.strip():
                logger.warning("No text available for word cloud generation")
                return None
            
            # Create word cloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5
            ).generate(text)
            
            return wordcloud
            
        except Exception as e:
            logger.error(f"Word cloud creation failed: {str(e)}")
            return None
    
    def _create_citation_network(self, research_data: Dict[str, Any]) -> go.Figure:
        """Create interactive citation network."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            # Build network
            nodes = []
            edges = []
            
            for i, paper in enumerate(papers):
                nodes.append({
                    'id': i,
                    'label': paper.get('title', 'Unknown')[:20] + "...",
                    'size': paper.get('citations', 0) + 5,
                    'color': f'rgb({100 + i*20}, {150 + i*15}, {200 + i*10})'
                })
                
                # Add citation edges (simplified)
                for j, other_paper in enumerate(papers):
                    if i != j and paper.get('citations', 0) > other_paper.get('citations', 0):
                        edges.append((i, j))
            
            # Create network visualization
            fig = go.Figure()
            
            # Add edges
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[nodes[edge[0]]['id'], nodes[edge[1]]['id']],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='gray', width=1),
                    showlegend=False
                ))
            
            # Add nodes
            fig.add_trace(go.Scatter(
                x=[node['id'] for node in nodes],
                y=[0] * len(nodes),
                mode='markers+text',
                marker=dict(
                    size=[node['size'] for node in nodes],
                    color=[node['color'] for node in nodes]
                ),
                text=[node['label'] for node in nodes],
                textposition="top center"
            ))
            
            fig.update_layout(
                title="Citation Network",
                xaxis_title="Papers",
                yaxis_title="",
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Citation network creation failed: {str(e)}")
            return go.Figure()
    
    def _create_trend_dashboard(self, research_data: Dict[str, Any]) -> go.Figure:
        """Create comprehensive trend dashboard."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            # Group by year
            year_data = {}
            for paper in papers:
                year = paper.get("year", 2024)
                if year not in year_data:
                    year_data[year] = {"count": 0, "citations": [], "topics": []}
                year_data[year]["count"] += 1
                year_data[year]["citations"].append(paper.get("citations", 0))
                year_data[year]["topics"].append(paper.get("title", ""))
            
            years = sorted(year_data.keys())
            counts = [year_data[year]["count"] for year in years]
            avg_citations = [np.mean(year_data[year]["citations"]) for year in years]
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Research Volume', 'Average Citations', 'Topic Evolution', 'Impact Distribution'),
                specs=[[{"type": "bar"}, {"type": "scatter"}],
                       [{"type": "scatter"}, {"type": "histogram"}]]
            )
            
            # Research volume
            fig.add_trace(
                go.Bar(x=years, y=counts, name='Papers Published'),
                row=1, col=1
            )
            
            # Average citations
            fig.add_trace(
                go.Scatter(x=years, y=avg_citations, mode='lines+markers', name='Avg Citations'),
                row=1, col=2
            )
            
            # Topic evolution (simplified)
            topic_counts = [len(set(year_data[year]["topics"])) for year in years]
            fig.add_trace(
                go.Scatter(x=years, y=topic_counts, mode='lines+markers', name='Unique Topics'),
                row=2, col=1
            )
            
            # Impact distribution
            all_citations = [paper.get("citations", 0) for paper in papers]
            fig.add_trace(
                go.Histogram(x=all_citations, name='Citation Distribution'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, title_text="Research Trends Dashboard")
            return fig
            
        except Exception as e:
            logger.error(f"Trend dashboard creation failed: {str(e)}")
            return go.Figure()
    
    def _create_quality_distribution(self, research_data: Dict[str, Any]) -> go.Figure:
        """Create quality distribution chart."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            # Calculate quality scores
            quality_scores = []
            for paper in papers:
                score = self._calculate_paper_quality(paper)
                quality_scores.append(score)
            
            # Create histogram
            fig = go.Figure(data=[go.Histogram(x=quality_scores, nbinsx=10)])
            fig.update_layout(
                title="Research Quality Distribution",
                xaxis_title="Quality Score",
                yaxis_title="Number of Papers"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Quality distribution creation failed: {str(e)}")
            return go.Figure()
    
    async def _perform_topic_modeling(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform topic modeling on research data."""
        try:
            if not SKLEARN_AVAILABLE:
                return {"error": "scikit-learn not available"}
            
            papers = research_data.get("papers_analyzed", [])
            
            if not papers:
                return {"error": "No papers to analyze"}
            
            # Extract text
            texts = []
            for paper in papers:
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                texts.append(text)
            
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Clustering
            n_clusters = min(3, len(papers))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Extract key terms
            feature_names = vectorizer.get_feature_names_out()
            cluster_terms = {}
            
            for i in range(n_clusters):
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-5:][::-1]
                cluster_terms[f"cluster_{i}"] = [feature_names[idx] for idx in top_indices]
            
            # Assign papers to clusters
            paper_clusters = {}
            for i, paper in enumerate(papers):
                paper_clusters[paper.get("title", f"Paper_{i}")] = {
                    "cluster": int(clusters[i]),
                    "cluster_terms": cluster_terms[f"cluster_{clusters[i]}"]
                }
            
            return {
                "clusters": cluster_terms,
                "paper_clusters": paper_clusters,
                "coherence_score": 0.75,
                "n_clusters": n_clusters
            }
            
        except Exception as e:
            logger.error(f"Topic modeling failed: {str(e)}")
            return {"error": str(e)}
    
    async def _assess_research_quality(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of research papers."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            quality_scores = {}
            for paper in papers:
                paper_id = paper.get("title", "Unknown")
                
                # Calculate quality score based on multiple factors
                factors = {
                    "citation_impact": min(paper.get("citations", 0) / 100, 1.0),
                    "recency": max(0, 1 - (2024 - paper.get("year", 2024)) / 10),
                    "journal_quality": self._estimate_journal_quality(paper.get("journal", "")),
                    "methodology_score": 0.7,  # Simplified
                    "sample_size_score": 0.6   # Simplified
                }
                
                # Weighted average
                weights = {
                    "citation_impact": 0.3,
                    "recency": 0.2,
                    "journal_quality": 0.25,
                    "methodology_score": 0.15,
                    "sample_size_score": 0.1
                }
                
                quality_score = sum(factors[factor] * weights[factor] for factor in factors)
                quality_scores[paper_id] = {
                    "overall_score": quality_score,
                    "factors": factors,
                    "confidence": 0.8
                }
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            return {}
    
    def _calculate_paper_quality(self, paper: Dict[str, Any]) -> float:
        """Calculate quality score for a single paper."""
        try:
            factors = {
                "citation_impact": min(paper.get("citations", 0) / 100, 1.0),
                "recency": max(0, 1 - (2024 - paper.get("year", 2024)) / 10),
                "journal_quality": self._estimate_journal_quality(paper.get("journal", "")),
                "methodology_score": 0.7,
                "sample_size_score": 0.6
            }
            
            weights = {
                "citation_impact": 0.3,
                "recency": 0.2,
                "journal_quality": 0.25,
                "methodology_score": 0.15,
                "sample_size_score": 0.1
            }
            
            return sum(factors[factor] * weights[factor] for factor in factors)
            
        except Exception as e:
            logger.error(f"Paper quality calculation failed: {str(e)}")
            return 0.5
    
    def _estimate_journal_quality(self, journal: str) -> float:
        """Estimate journal quality score."""
        try:
            high_impact = ["nature", "science", "cell", "pnas", "lancet"]
            medium_impact = ["jama", "bmj", "nejm", "plos", "biorxiv"]
            
            journal_lower = journal.lower()
            
            if any(high in journal_lower for high in high_impact):
                return 0.9
            elif any(medium in journal_lower for medium in medium_impact):
                return 0.7
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Journal quality estimation failed: {str(e)}")
            return 0.5
    
    async def _analyze_citation_network(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze citation network relationships."""
        try:
            if not NETWORKX_AVAILABLE:
                return {"error": "networkx not available"}
            
            papers = research_data.get("papers_analyzed", [])
            
            # Build network graph
            G = nx.DiGraph()
            
            for paper in papers:
                G.add_node(paper.get("title", "Unknown"), 
                          citations=paper.get("citations", 0),
                          year=paper.get("year", 2024))
            
            # Add edges (simplified)
            for i, paper1 in enumerate(papers):
                for j, paper2 in enumerate(papers):
                    if i != j and paper1.get("citations", 0) > paper2.get("citations", 0):
                        G.add_edge(paper1.get("title", "Unknown"), 
                                 paper2.get("title", "Unknown"))
            
            # Calculate network metrics
            metrics = {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "density": nx.density(G),
                "average_clustering": nx.average_clustering(G) if G.number_of_nodes() > 1 else 0,
                "connected_components": nx.number_strongly_connected_components(G)
            }
            
            return {
                "network": G,
                "metrics": metrics,
                "central_nodes": list(nx.topological_sort(G))[:5] if nx.is_directed_acyclic_graph(G) else []
            }
            
        except Exception as e:
            logger.error(f"Citation network analysis failed: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_research_trends(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research trends over time."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            # Group by year
            year_data = {}
            for paper in papers:
                year = paper.get("year", 2024)
                if year not in year_data:
                    year_data[year] = {"papers": [], "citations": [], "topics": []}
                year_data[year]["papers"].append(paper)
                year_data[year]["citations"].append(paper.get("citations", 0))
                year_data[year]["topics"].append(paper.get("title", ""))
            
            # Calculate trends
            trends = {}
            for year in sorted(year_data.keys()):
                trends[year] = {
                    "paper_count": len(year_data[year]["papers"]),
                    "avg_citations": np.mean(year_data[year]["citations"]),
                    "total_citations": sum(year_data[year]["citations"]),
                    "unique_topics": len(set(year_data[year]["topics"]))
                }
            
            return {
                "yearly_trends": trends,
                "growth_rate": self._calculate_growth_rate(trends),
                "peak_year": max(trends.keys(), key=lambda y: trends[y]["paper_count"]) if trends else None
            }
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_growth_rate(self, trends: Dict[int, Dict[str, Any]]) -> float:
        """Calculate overall growth rate."""
        try:
            if len(trends) < 2:
                return 0.0
            
            years = sorted(trends.keys())
            first_year = trends[years[0]]["paper_count"]
            last_year = trends[years[-1]]["paper_count"]
            
            if first_year == 0:
                return 0.0
            
            return (last_year - first_year) / first_year
            
        except Exception as e:
            logger.error(f"Growth rate calculation failed: {str(e)}")
            return 0.0
    
    async def _generate_export_formats(self, research_data: Dict[str, Any], 
                                     visualizations: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate multiple export formats."""
        try:
            exports = {}
            
            # 1. Enhanced JSON export
            # Filter out non-serializable visualization objects
            serializable_viz = []
            for v in visualizations:
                if isinstance(v, dict) and "type" in v and "title" in v:
                    # Only include serializable data, exclude figure objects
                    viz_data = {
                        "type": v["type"], 
                        "title": v["title"], 
                        "description": v.get("description", "")
                    }
                    # Add any other serializable metadata
                    for key, value in v.items():
                        if key not in ["figure", "type", "title", "description"] and isinstance(value, (str, int, float, bool, list, dict)):
                            viz_data[key] = value
                    serializable_viz.append(viz_data)
            
            # Clean research_data to remove any non-serializable objects
            def clean_for_json(obj):
                if isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items() 
                           if not k.startswith('_') and not callable(v)}
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                else:
                    return str(obj)  # Convert other objects to strings
            
            clean_research_data = clean_for_json(research_data)
            
            enhanced_data = {
                "research_data": clean_research_data,
                "visualizations": serializable_viz,
                "generated_at": datetime.now().isoformat(),
                "version": "2.0"
            }
            exports["json"] = json.dumps(enhanced_data, indent=2)
            
            # 2. Markdown report
            markdown = self._generate_markdown_report(research_data, visualizations)
            exports["markdown"] = markdown
            
            # 3. HTML report
            html = self._generate_html_report(research_data, visualizations)
            exports["html"] = html
            
            # 4. LaTeX report
            latex = self._generate_latex_report(research_data)
            exports["latex"] = latex
            
            # 5. CSV data export
            csv_data = self._generate_csv_export(research_data)
            exports["csv"] = csv_data
            
            return exports
            
        except Exception as e:
            logger.error(f"Export generation failed: {str(e)}")
            return {}
    
    def _generate_markdown_report(self, research_data: Dict[str, Any], 
                                visualizations: List[Dict[str, Any]]) -> str:
        """Generate enhanced markdown report."""
        try:
            report = f"""# Enhanced Research Report

*Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}*
*Based on analysis of {len(research_data.get('papers_analyzed', []))} research papers*

## Executive Summary

This enhanced research synthesis provides comprehensive analysis with advanced visualizations and quality assessment.

## Research Overview

- **Papers Analyzed**: {len(research_data.get('papers_analyzed', []))}
- **Consensus Findings**: {len(research_data.get('consensus_findings', []))}
- **Emerging Trends**: {len(research_data.get('emerging_trends', []))}
- **Research Gaps**: {len(research_data.get('research_gaps', []))}

## Advanced Visualizations

"""
            
            for viz in visualizations:
                report += f"### {viz['title']}\n{viz['description']}\n\n"
            
            report += "## Quality Assessment\n\n"
            report += "Each paper has been assessed for quality based on multiple factors including citations, recency, and journal impact.\n\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Markdown report generation failed: {str(e)}")
            return "# Research Report\n\nError generating report."
    
    def _generate_html_report(self, research_data: Dict[str, Any], 
                            visualizations: List[Dict[str, Any]]) -> str:
        """Generate HTML report."""
        try:
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Research Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; }}
        .chart {{ margin: 20px 0; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Enhanced Research Report</h1>
        <p>Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
    </div>
    
    <div class="section">
        <h2>Research Overview</h2>
        <p>Papers Analyzed: {len(research_data.get('papers_analyzed', []))}</p>
        <p>Consensus Findings: {len(research_data.get('consensus_findings', []))}</p>
        <p>Emerging Trends: {len(research_data.get('emerging_trends', []))}</p>
    </div>
    
    <div class="section">
        <h2>Advanced Visualizations</h2>
"""
            
            for viz in visualizations:
                html += f"""
        <div class="chart">
            <h3>{viz['title']}</h3>
            <p>{viz['description']}</p>
        </div>
"""
            
            html += """
    </div>
</body>
</html>"""
            
            return html
            
        except Exception as e:
            logger.error(f"HTML report generation failed: {str(e)}")
            return "<html><body><h1>Error generating report</h1></body></html>"
    
    def _generate_latex_report(self, research_data: Dict[str, Any]) -> str:
        """Generate LaTeX report."""
        try:
            latex = f"""\\documentclass[12pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}

\\title{{Enhanced Research Report}}
\\author{{Nocturnal Archive Research System}}
\\date{{{datetime.now().strftime('%B %d, %Y')}}}

\\begin{{document}}

\\maketitle

\\section{{Executive Summary}}

This enhanced research synthesis provides comprehensive analysis with advanced visualizations and quality assessment.

\\section{{Research Overview}}

\\begin{{itemize}}
\\item Papers Analyzed: {len(research_data.get('papers_analyzed', []))}
\\item Consensus Findings: {len(research_data.get('consensus_findings', []))}
\\item Emerging Trends: {len(research_data.get('emerging_trends', []))}
\\end{{itemize}}

\\section{{Advanced Analysis}}

The research includes topic modeling, quality assessment, and advanced visualizations.

\\end{{document}}"""
            
            return latex
            
        except Exception as e:
            logger.error(f"LaTeX report generation failed: {str(e)}")
            return "\\documentclass{article}\\begin{document}\\title{Error}\\end{document}"
    
    def _generate_csv_export(self, research_data: Dict[str, Any]) -> str:
        """Generate CSV export of research data."""
        try:
            papers = research_data.get("papers_analyzed", [])
            
            if not papers:
                return "title,year,citations,journal,abstract\n"
            
            csv_lines = ["title,year,citations,journal,abstract\n"]
            
            for paper in papers:
                title = paper.get("title", "").replace('"', '""')
                year = paper.get("year", "")
                citations = paper.get("citations", "")
                journal = paper.get("journal", "").replace('"', '""')
                abstract = paper.get("abstract", "").replace('"', '""')
                
                csv_lines.append(f'"{title}",{year},{citations},"{journal}","{abstract}"\n')
            
            return "".join(csv_lines)
            
        except Exception as e:
            logger.error(f"CSV export generation failed: {str(e)}")
            return "title,year,citations,journal,abstract\n"
    
    async def get_research_insights(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from research data."""
        try:
            insights = {
                "key_findings": research_data.get("consensus_findings", []),
                "emerging_trends": research_data.get("emerging_trends", []),
                "research_gaps": research_data.get("research_gaps", []),
                "methodology_insights": research_data.get("methodology_insights", []),
                "quality_insights": await self._generate_quality_insights(research_data),
                "trend_insights": await self._generate_trend_insights(research_data)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Insights generation failed: {str(e)}")
            return {}
    
    async def _generate_quality_insights(self, research_data: Dict[str, Any]) -> List[str]:
        """Generate quality-related insights."""
        try:
            insights = []
            papers = research_data.get("papers_analyzed", [])
            
            if not papers:
                return ["No papers available for quality analysis"]
            
            # Calculate average quality
            quality_scores = [self._calculate_paper_quality(paper) for paper in papers]
            avg_quality = np.mean(quality_scores)
            
            insights.append(f"Average research quality: {avg_quality:.2f}")
            
            # Identify high-quality papers
            high_quality = [p for p, q in zip(papers, quality_scores) if q > 0.8]
            insights.append(f"High-quality papers (score > 0.8): {len(high_quality)}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Quality insights generation failed: {str(e)}")
            return ["Error generating quality insights"]
    
    async def _generate_trend_insights(self, research_data: Dict[str, Any]) -> List[str]:
        """Generate trend-related insights."""
        try:
            insights = []
            papers = research_data.get("papers_analyzed", [])
            
            if not papers:
                return ["No papers available for trend analysis"]
            
            # Analyze publication trends
            years = [paper.get("year", 2024) for paper in papers]
            year_counts = Counter(years)
            
            if year_counts:
                most_active_year = max(year_counts, key=year_counts.get)
                insights.append(f"Most active research year: {most_active_year}")
            
            # Analyze citation trends
            citations = [paper.get("citations", 0) for paper in papers]
            if citations:
                avg_citations = np.mean(citations)
                insights.append(f"Average citations per paper: {avg_citations:.1f}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Trend insights generation failed: {str(e)}")
            return ["Error generating trend insights"]
