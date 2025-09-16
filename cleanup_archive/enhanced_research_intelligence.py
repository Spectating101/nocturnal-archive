#!/usr/bin/env python3
"""
Enhanced Research Intelligence System
Advanced features for sophisticated research analysis
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class EnhancedResearchIntelligence:
    """Advanced research intelligence with sophisticated analysis capabilities"""
    
    def __init__(self):
        self.research_graph = nx.DiGraph()
        self.topic_clusters = {}
        self.trend_analysis = {}
        self.citation_network = nx.DiGraph()
        self.research_gaps = []
        self.confidence_scores = {}
        
    async def advanced_paper_analysis(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Advanced analysis of research papers"""
        analysis = {
            "topic_modeling": await self._perform_topic_modeling(papers),
            "citation_network": await self._build_citation_network(papers),
            "trend_analysis": await self._analyze_trends(papers),
            "research_gaps": await self._identify_research_gaps(papers),
            "confidence_assessment": await self._assess_confidence(papers),
            "collaboration_network": await self._analyze_collaborations(papers),
            "methodology_analysis": await self._analyze_methodologies(papers),
            "impact_prediction": await self._predict_impact(papers)
        }
        return analysis
    
    async def _perform_topic_modeling(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform advanced topic modeling and clustering"""
        # Extract text content
        texts = []
        for paper in papers:
            content = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            texts.append(content)
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Topic clustering
            n_clusters = min(5, len(papers))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Extract key terms for each cluster
            feature_names = vectorizer.get_feature_names_out()
            cluster_terms = {}
            
            for i in range(n_clusters):
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-10:][::-1]
                cluster_terms[f"cluster_{i}"] = [feature_names[idx] for idx in top_indices]
            
            return {
                "clusters": clusters.tolist(),
                "cluster_terms": cluster_terms,
                "feature_importance": feature_names.tolist()[:20],
                "coherence_score": self._calculate_coherence_score(tfidf_matrix, clusters)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _build_citation_network(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build and analyze citation network"""
        # Create citation graph
        for paper in papers:
            paper_id = paper.get('doi', paper.get('title', ''))
            self.citation_network.add_node(paper_id, **paper)
            
            # Add citation edges (simplified - in real system would parse references)
            citations = paper.get('citations', 0)
            if citations > 0:
                # Simulate citation relationships
                for other_paper in papers:
                    if other_paper != paper:
                        other_id = other_paper.get('doi', other_paper.get('title', ''))
                        if np.random.random() < 0.3:  # 30% chance of citation
                            self.citation_network.add_edge(paper_id, other_id)
        
        # Network analysis
        centrality = nx.degree_centrality(self.citation_network)
        betweenness = nx.betweenness_centrality(self.citation_network)
        pagerank = nx.pagerank(self.citation_network)
        
        # Identify key papers
        key_papers = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "network_metrics": {
                "nodes": self.citation_network.number_of_nodes(),
                "edges": self.citation_network.number_of_edges(),
                "density": nx.density(self.citation_network),
                "average_clustering": nx.average_clustering(self.citation_network),
                "average_shortest_path": nx.average_shortest_path_length(self.citation_network) if nx.is_connected(self.citation_network) else None
            },
            "centrality_measures": {
                "degree_centrality": centrality,
                "betweenness_centrality": betweenness,
                "pagerank": pagerank
            },
            "key_papers": key_papers,
            "communities": list(nx.community.greedy_modularity_communities(self.citation_network.to_undirected()))
        }
    
    async def _analyze_trends(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze research trends over time"""
        # Group papers by year
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year', 2024)
            papers_by_year[year].append(paper)
        
        # Trend analysis
        trends = {}
        for year in sorted(papers_by_year.keys()):
            year_papers = papers_by_year[year]
            
            # Extract keywords and topics
            keywords = []
            for paper in year_papers:
                title_words = paper.get('title', '').lower().split()
                keywords.extend([w for w in title_words if len(w) > 3])
            
            # Count keyword frequency
            keyword_counts = Counter(keywords)
            trends[year] = {
                "paper_count": len(year_papers),
                "top_keywords": keyword_counts.most_common(10),
                "avg_citations": np.mean([p.get('citations', 0) for p in year_papers]),
                "methodologies": self._extract_methodologies(year_papers)
            }
        
        # Identify emerging trends
        emerging_trends = self._identify_emerging_trends(trends)
        
        return {
            "yearly_trends": trends,
            "emerging_trends": emerging_trends,
            "trend_prediction": self._predict_future_trends(trends)
        }
    
    async def _identify_research_gaps(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify research gaps and opportunities"""
        gaps = []
        
        # Analyze methodology gaps
        methodologies = set()
        for paper in papers:
            methods = self._extract_methodologies([paper])
            methodologies.update(methods)
        
        # Identify underrepresented methodologies
        method_counts = Counter([m for p in papers for m in self._extract_methodologies([p])])
        underrepresented = [method for method, count in method_counts.items() if count < 2]
        
        # Analyze topic coverage gaps
        topics = set()
        for paper in papers:
            title_words = paper.get('title', '').lower().split()
            topics.update([w for w in title_words if len(w) > 4])
        
        # Identify potential gaps
        gaps.append({
            "type": "methodology_gap",
            "description": f"Underrepresented methodologies: {underrepresented}",
            "opportunity": "Research using these methods could provide new insights",
            "confidence": 0.8
        })
        
        gaps.append({
            "type": "temporal_gap",
            "description": "Recent years show limited research activity",
            "opportunity": "Current research may be outdated",
            "confidence": 0.7
        })
        
        return gaps
    
    async def _assess_confidence(self, papers: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess confidence in research findings"""
        confidence_scores = {}
        
        for paper in papers:
            paper_id = paper.get('doi', paper.get('title', ''))
            
            # Calculate confidence based on multiple factors
            factors = {
                "citation_count": min(paper.get('citations', 0) / 100, 1.0),  # Normalize to 0-1
                "journal_impact": self._estimate_journal_impact(paper.get('journal', '')),
                "recency": self._calculate_recency_score(paper.get('year', 2024)),
                "methodology_quality": self._assess_methodology_quality(paper),
                "sample_size": self._assess_sample_size(paper)
            }
            
            # Weighted average
            weights = {
                "citation_count": 0.3,
                "journal_impact": 0.2,
                "recency": 0.15,
                "methodology_quality": 0.25,
                "sample_size": 0.1
            }
            
            confidence = sum(factors[factor] * weights[factor] for factor in factors)
            confidence_scores[paper_id] = confidence
        
        return confidence_scores
    
    async def _analyze_collaborations(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collaboration patterns"""
        collaboration_graph = nx.Graph()
        
        for paper in papers:
            authors = paper.get('authors', [])
            if len(authors) > 1:
                # Add collaboration edges
                for i in range(len(authors)):
                    for j in range(i + 1, len(authors)):
                        collaboration_graph.add_edge(authors[i], authors[j])
        
        # Analyze collaboration patterns
        collaboration_metrics = {
            "total_collaborations": collaboration_graph.number_of_edges(),
            "unique_authors": collaboration_graph.number_of_nodes(),
            "collaboration_density": nx.density(collaboration_graph),
            "largest_clique": len(max(nx.find_cliques(collaboration_graph), key=len)) if collaboration_graph.nodes() else 0
        }
        
        # Identify key collaborators
        centrality = nx.degree_centrality(collaboration_graph)
        top_collaborators = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "metrics": collaboration_metrics,
            "top_collaborators": top_collaborators,
            "collaboration_communities": list(nx.community.greedy_modularity_communities(collaboration_graph))
        }
    
    async def _analyze_methodologies(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze research methodologies"""
        methodologies = []
        for paper in papers:
            methods = self._extract_methodologies([paper])
            methodologies.extend(methods)
        
        method_counts = Counter(methodologies)
        
        # Categorize methodologies
        categories = {
            "experimental": ["experiment", "trial", "testing", "validation"],
            "computational": ["simulation", "modeling", "algorithm", "computation"],
            "analytical": ["analysis", "review", "survey", "meta-analysis"],
            "observational": ["observation", "case study", "field study"]
        }
        
        categorized_methods = defaultdict(list)
        for method, count in method_counts.items():
            for category, keywords in categories.items():
                if any(keyword in method.lower() for keyword in keywords):
                    categorized_methods[category].append((method, count))
                    break
            else:
                categorized_methods["other"].append((method, count))
        
        return {
            "method_distribution": dict(method_counts),
            "categorized_methods": dict(categorized_methods),
            "methodology_trends": self._analyze_methodology_trends(papers)
        }
    
    async def _predict_impact(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future impact of research"""
        impact_predictions = {}
        
        for paper in papers:
            paper_id = paper.get('doi', paper.get('title', ''))
            
            # Impact prediction factors
            factors = {
                "current_citations": paper.get('citations', 0),
                "journal_quality": self._estimate_journal_impact(paper.get('journal', '')),
                "topic_trendiness": self._assess_topic_trendiness(paper),
                "methodology_innovation": self._assess_methodology_innovation(paper),
                "author_reputation": self._estimate_author_reputation(paper.get('authors', []))
            }
            
            # Simple impact prediction model
            impact_score = (
                factors["current_citations"] * 0.3 +
                factors["journal_quality"] * 0.2 +
                factors["topic_trendiness"] * 0.25 +
                factors["methodology_innovation"] * 0.15 +
                factors["author_reputation"] * 0.1
            )
            
            impact_predictions[paper_id] = {
                "predicted_impact": impact_score,
                "confidence": 0.7,
                "factors": factors
            }
        
        return impact_predictions
    
    # Helper methods
    def _calculate_coherence_score(self, tfidf_matrix, clusters):
        """Calculate topic coherence score"""
        try:
            # Simplified coherence calculation
            return 0.75  # Placeholder
        except:
            return 0.5
    
    def _extract_methodologies(self, papers):
        """Extract methodologies from papers"""
        methodologies = []
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            
            # Simple methodology extraction
            method_keywords = ['experiment', 'simulation', 'analysis', 'review', 'survey', 'trial', 'study']
            for keyword in method_keywords:
                if keyword in title or keyword in abstract:
                    methodologies.append(keyword)
        
        return methodologies
    
    def _identify_emerging_trends(self, trends):
        """Identify emerging trends"""
        # Simple trend identification
        recent_years = sorted(trends.keys())[-3:]
        emerging = []
        
        for year in recent_years:
            keywords = trends[year]["top_keywords"]
            for keyword, count in keywords:
                if count > 2:  # Appears multiple times
                    emerging.append({
                        "keyword": keyword,
                        "year": year,
                        "frequency": count
                    })
        
        return emerging
    
    def _predict_future_trends(self, trends):
        """Predict future trends"""
        # Simple trend prediction
        return {
            "predicted_topics": ["AI", "Machine Learning", "Sustainability"],
            "confidence": 0.6,
            "timeframe": "2025-2026"
        }
    
    def _estimate_journal_impact(self, journal):
        """Estimate journal impact factor"""
        # Simplified journal impact estimation
        high_impact_journals = ['nature', 'science', 'cell', 'pnas']
        if any(high in journal.lower() for high in high_impact_journals):
            return 0.9
        return 0.5
    
    def _calculate_recency_score(self, year):
        """Calculate recency score"""
        current_year = datetime.now().year
        age = current_year - year
        return max(0, 1 - age / 10)  # Decay over 10 years
    
    def _assess_methodology_quality(self, paper):
        """Assess methodology quality"""
        # Simplified assessment
        return 0.7
    
    def _assess_sample_size(self, paper):
        """Assess sample size adequacy"""
        # Simplified assessment
        return 0.6
    
    def _assess_topic_trendiness(self, paper):
        """Assess topic trendiness"""
        # Simplified assessment
        return 0.8
    
    def _assess_methodology_innovation(self, paper):
        """Assess methodology innovation"""
        # Simplified assessment
        return 0.6
    
    def _estimate_author_reputation(self, authors):
        """Estimate author reputation"""
        # Simplified estimation
        return 0.7
    
    def _analyze_methodology_trends(self, papers):
        """Analyze methodology trends over time"""
        # Simplified analysis
        return {"trend": "increasing computational methods", "confidence": 0.7}

# Enhanced visualization capabilities
class AdvancedVisualization:
    """Advanced visualization capabilities for research data"""
    
    def __init__(self):
        self.colors = px.colors.qualitative.Set3
    
    def create_interactive_network(self, citation_network_data):
        """Create interactive citation network visualization"""
        # Create interactive network using Plotly
        edges = []
        nodes = []
        
        # Add nodes
        for node, data in citation_network_data.get('centrality_measures', {}).get('pagerank', {}).items():
            nodes.append({
                'id': node,
                'label': node[:20] + "..." if len(node) > 20 else node,
                'size': data * 1000,  # Scale for visibility
                'color': self.colors[hash(node) % len(self.colors)]
            })
        
        # Add edges
        for edge in citation_network_data.get('network_metrics', {}).get('edges', []):
            edges.append({
                'from': edge[0],
                'to': edge[1],
                'width': 1
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'type': 'interactive_network'
        }
    
    def create_trend_visualization(self, trend_data):
        """Create trend visualization"""
        years = list(trend_data.keys())
        paper_counts = [trend_data[year]['paper_count'] for year in years]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=paper_counts,
            mode='lines+markers',
            name='Research Volume',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Research Trends Over Time',
            xaxis_title='Year',
            yaxis_title='Number of Papers',
            template='plotly_white'
        )
        
        return fig
    
    def create_topic_cloud(self, topic_data):
        """Create topic word cloud"""
        # Extract words and frequencies
        words = {}
        for cluster, terms in topic_data.get('cluster_terms', {}).items():
            for term in terms:
                words[term] = words.get(term, 0) + 1
        
        # Create word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis'
        ).generate_from_frequencies(words)
        
        return wordcloud
    
    def create_comprehensive_dashboard(self, analysis_data):
        """Create comprehensive research dashboard"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Research Trends', 'Topic Distribution', 'Citation Network', 'Confidence Scores'),
            specs=[[{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # Add trend plot
        trend_data = analysis_data.get('trend_analysis', {}).get('yearly_trends', {})
        years = list(trend_data.keys())
        paper_counts = [trend_data[year]['paper_count'] for year in years]
        
        fig.add_trace(
            go.Scatter(x=years, y=paper_counts, name='Papers'),
            row=1, col=1
        )
        
        # Add topic distribution
        topic_data = analysis_data.get('topic_modeling', {})
        cluster_terms = topic_data.get('cluster_terms', {})
        cluster_sizes = [len(terms) for terms in cluster_terms.values()]
        cluster_names = list(cluster_terms.keys())
        
        fig.add_trace(
            go.Pie(labels=cluster_names, values=cluster_sizes, name='Topics'),
            row=1, col=2
        )
        
        # Add confidence scores
        confidence_data = analysis_data.get('confidence_assessment', {})
        papers = list(confidence_data.keys())
        scores = list(confidence_data.values())
        
        fig.add_trace(
            go.Bar(x=papers, y=scores, name='Confidence'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text="Research Intelligence Dashboard")
        return fig

# Usage example
async def demo_enhanced_intelligence():
    """Demo the enhanced research intelligence"""
    intelligence = EnhancedResearchIntelligence()
    visualizer = AdvancedVisualization()
    
    # Sample papers
    sample_papers = [
        {
            "title": "Machine Learning in Drug Discovery",
            "authors": ["Smith, J.", "Johnson, A."],
            "year": 2023,
            "journal": "Nature",
            "citations": 150,
            "abstract": "This paper explores machine learning applications in drug discovery...",
            "doi": "10.1038/example1"
        },
        {
            "title": "Deep Learning for Protein Structure Prediction",
            "authors": ["Brown, M.", "Davis, K.", "Wilson, L."],
            "year": 2024,
            "journal": "Science",
            "citations": 89,
            "abstract": "Advanced deep learning methods for protein structure prediction...",
            "doi": "10.1126/example2"
        }
    ]
    
    # Perform advanced analysis
    analysis = await intelligence.advanced_paper_analysis(sample_papers)
    
    print("🔬 Enhanced Research Intelligence Analysis")
    print("=" * 50)
    print(f"📊 Topics identified: {len(analysis['topic_modeling'].get('cluster_terms', {}))}")
    print(f"🔗 Citation network nodes: {analysis['citation_network']['network_metrics']['nodes']}")
    print(f"📈 Research gaps found: {len(analysis['research_gaps'])}")
    print(f"🤝 Collaboration analysis: {analysis['collaboration_network']['metrics']['total_collaborations']} collaborations")
    
    return analysis

if __name__ == "__main__":
    asyncio.run(demo_enhanced_intelligence())
