#!/usr/bin/env python3
"""
Demonstration of Citation Mapping Integration
Shows how the citation system provides academic credibility to research synthesis
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Mock imports for demonstration
class MockCitationManager:
    """Mock citation manager for demonstration"""
    
    def __init__(self):
        self.sample_citations = [
            {
                "citation_id": "CIT_ABC12345",
                "title": "Advances in Machine Learning for Scientific Discovery",
                "authors": ["Smith, J.", "Johnson, A.", "Brown, M."],
                "year": 2023,
                "journal": "Nature Machine Intelligence",
                "doi": "10.1038/s42256-023-00001-x",
                "citation_count": 150
            },
            {
                "citation_id": "CIT_DEF67890",
                "title": "Deep Learning Applications in Drug Discovery",
                "authors": ["Wilson, R.", "Davis, K."],
                "year": 2022,
                "journal": "Science",
                "doi": "10.1126/science.abc1234",
                "citation_count": 89
            },
            {
                "citation_id": "CIT_GHI11111",
                "title": "Transformer Models for Protein Structure Prediction",
                "authors": ["Anderson, L.", "Taylor, P.", "Miller, S.", "Clark, J."],
                "year": 2024,
                "journal": "Cell",
                "doi": "10.1016/j.cell.2024.01.001",
                "citation_count": 67
            }
        ]
    
    def format_apa_citation(self, citation: Dict) -> str:
        """Format citation in APA style"""
        authors = citation["authors"]
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        else:
            author_str = f"{authors[0]} et al."
        
        return f"{author_str}. ({citation['year']}). {citation['title']}. {citation['journal']}. https://doi.org/{citation['doi']}"
    
    def format_bibtex_citation(self, citation: Dict) -> str:
        """Format citation in BibTeX style"""
        authors = " and ".join(citation["authors"])
        return f"""@article{{{citation['citation_id']},
  title = {{{citation['title']}}},
  author = {{{authors}}},
  year = {{{citation['year']}}},
  journal = {{{citation['journal']}}},
  doi = {{{citation['doi']}}}
}}"""

class MockResearchSynthesizer:
    """Mock research synthesizer with citation integration"""
    
    def __init__(self):
        self.citation_manager = MockCitationManager()
    
    async def synthesize_papers(self, paper_ids: List[str]) -> Dict[str, Any]:
        """Mock synthesis with citation analysis"""
        # Simulate synthesis results
        synthesis = {
            "common_findings": [
                {
                    "finding": "Machine learning models show significant improvements in drug discovery accuracy",
                    "strength": "strong",
                    "supporting_papers": ["paper_1", "paper_2"]
                },
                {
                    "finding": "Transformer architectures outperform traditional methods in protein structure prediction",
                    "strength": "moderate", 
                    "supporting_papers": ["paper_3"]
                }
            ],
            "research_gaps": [
                {
                    "gap": "Limited research on interpretability of deep learning models in drug discovery",
                    "type": "methodological"
                },
                {
                    "gap": "Need for more diverse datasets in protein structure prediction",
                    "type": "data"
                }
            ],
            "contradictions": [
                {
                    "contradiction": "Some studies show high accuracy while others report significant limitations",
                    "papers": ["paper_1", "paper_2"]
                }
            ],
            "methodology_analysis": {
                "deep_learning": {
                    "count": 3,
                    "papers": ["paper_1", "paper_2", "paper_3"],
                    "description": "Primary methodology across all studies"
                },
                "transformer_models": {
                    "count": 2,
                    "papers": ["paper_2", "paper_3"],
                    "description": "Emerging approach showing promise"
                }
            },
            "future_directions": [
                {
                    "direction": "Integration of multi-modal data in drug discovery pipelines",
                    "priority": "high"
                },
                {
                    "direction": "Development of interpretable AI models for scientific applications",
                    "priority": "medium"
                }
            ]
        }
        
        # Add citation analysis
        synthesis["citation_analysis"] = await self._analyze_citations()
        
        return synthesis
    
    async def _analyze_citations(self) -> Dict[str, Any]:
        """Mock citation analysis"""
        citations = self.citation_manager.sample_citations
        
        # Format citations
        apa_citations = []
        bibtex_citations = []
        
        for citation in citations:
            apa_citations.append(self.citation_manager.format_apa_citation(citation))
            bibtex_citations.append(self.citation_manager.format_bibtex_citation(citation))
        
        # Calculate analytics
        total_citations = len(citations)
        years = [c["year"] for c in citations]
        citation_counts = [c["citation_count"] for c in citations]
        
        analytics = {
            "total_citations": total_citations,
            "year_range": {
                "min": min(years),
                "max": max(years),
                "average": sum(years) / len(years)
            },
            "citation_impact": {
                "total_citations_received": sum(citation_counts),
                "average_citations_per_paper": sum(citation_counts) / total_citations,
                "highly_cited_papers": len([c for c in citation_counts if c > 100])
            },
            "journal_distribution": {
                "Nature Machine Intelligence": 1,
                "Science": 1,
                "Cell": 1
            },
            "author_analysis": {
                "total_authors": 7,
                "most_frequent_authors": {
                    "Smith, J.": 1,
                    "Johnson, A.": 1,
                    "Brown, M.": 1
                }
            }
        }
        
        return {
            "total_citations": total_citations,
            "cited_findings": [
                {
                    "finding_id": "FIND_001",
                    "text": "Machine learning models show significant improvements in drug discovery accuracy",
                    "citation": citations[0],
                    "confidence_score": 0.95
                },
                {
                    "finding_id": "FIND_002", 
                    "text": "Transformer architectures outperform traditional methods in protein structure prediction",
                    "citation": citations[2],
                    "confidence_score": 0.88
                }
            ],
            "citation_analytics": analytics,
            "formatted_citations": {
                "apa": "\n\n".join(apa_citations),
                "bibtex": "\n\n".join(bibtex_citations)
            },
            "citation_quality": "high",
            "academic_credibility_score": 8.5
        }
    
    async def export_academic_synthesis(self, synthesis: Dict[str, Any], format_type: str = "APA") -> str:
        """Export synthesis with academic citations"""
        academic_synthesis = []
        academic_synthesis.append("# Research Synthesis Report")
        academic_synthesis.append("")
        academic_synthesis.append(f"*Generated on: {datetime.now().strftime('%B %d, %Y')}*")
        academic_synthesis.append("")
        
        # Key Findings with Citations
        if synthesis.get("common_findings"):
            academic_synthesis.append("## Key Findings")
            academic_synthesis.append("")
            
            citation_analysis = synthesis.get("citation_analysis", {})
            cited_findings = citation_analysis.get("cited_findings", [])
            
            for i, finding in enumerate(synthesis["common_findings"], 1):
                finding_text = finding.get("finding", str(finding))
                academic_synthesis.append(f"{i}. {finding_text}")
                
                # Add citation if available
                if i <= len(cited_findings):
                    citation = cited_findings[i-1].get("citation", {})
                    if citation.get("authors") and citation.get("year"):
                        authors = citation["authors"]
                        if len(authors) == 1:
                            author_cite = authors[0]
                        elif len(authors) == 2:
                            author_cite = f"{authors[0]} and {authors[1]}"
                        else:
                            author_cite = f"{authors[0]} et al."
                        academic_synthesis.append(f"   *Source: {author_cite} ({citation['year']})*")
                academic_synthesis.append("")
        
        # Research Gaps
        if synthesis.get("research_gaps"):
            academic_synthesis.append("## Research Gaps")
            academic_synthesis.append("")
            for gap in synthesis["research_gaps"]:
                gap_text = gap.get("gap", str(gap))
                academic_synthesis.append(f"- {gap_text}")
            academic_synthesis.append("")
        
        # Contradictions
        if synthesis.get("contradictions"):
            academic_synthesis.append("## Contradictions and Disagreements")
            academic_synthesis.append("")
            for contradiction in synthesis["contradictions"]:
                contradiction_text = contradiction.get("contradiction", str(contradiction))
                academic_synthesis.append(f"- {contradiction_text}")
            academic_synthesis.append("")
        
        # Methodology Analysis
        if synthesis.get("methodology_analysis"):
            academic_synthesis.append("## Methodology Analysis")
            academic_synthesis.append("")
            methodology = synthesis["methodology_analysis"]
            for key, value in methodology.items():
                if key != "error":
                    academic_synthesis.append(f"### {key.replace('_', ' ').title()}")
                    academic_synthesis.append(f"**Count:** {value.get('count', 0)} papers")
                    academic_synthesis.append(f"**Description:** {value.get('description', 'N/A')}")
                    academic_synthesis.append("")
        
        # Future Directions
        if synthesis.get("future_directions"):
            academic_synthesis.append("## Future Research Directions")
            academic_synthesis.append("")
            for direction in synthesis["future_directions"]:
                direction_text = direction.get("direction", str(direction))
                priority = direction.get("priority", "medium")
                academic_synthesis.append(f"- {direction_text} *(Priority: {priority})*")
            academic_synthesis.append("")
        
        # Citations Section
        citation_analysis = synthesis.get("citation_analysis", {})
        formatted_citations = citation_analysis.get("formatted_citations", {})
        
        if formatted_citations:
            academic_synthesis.append("## References")
            academic_synthesis.append("")
            
            if format_type == "APA" and formatted_citations.get("apa"):
                citations_text = formatted_citations["apa"]
                citations_list = citations_text.split("\n\n")
                for i, citation in enumerate(citations_list, 1):
                    if citation.strip():
                        academic_synthesis.append(f"{i}. {citation.strip()}")
            elif format_type == "BIBTEX" and formatted_citations.get("bibtex"):
                academic_synthesis.append("```bibtex")
                academic_synthesis.append(formatted_citations["bibtex"])
                academic_synthesis.append("```")
        
        # Citation Analytics
        if citation_analysis.get("citation_analytics"):
            analytics = citation_analysis["citation_analytics"]
            academic_synthesis.append("")
            academic_synthesis.append("## Citation Analytics")
            academic_synthesis.append("")
            academic_synthesis.append(f"- **Total citations analyzed:** {analytics.get('total_citations', 0)}")
            academic_synthesis.append(f"- **Year range:** {analytics.get('year_range', {}).get('min', 0)} - {analytics.get('year_range', {}).get('max', 0)}")
            academic_synthesis.append(f"- **Average citations per paper:** {analytics.get('citation_impact', {}).get('average_citations_per_paper', 0):.1f}")
            academic_synthesis.append(f"- **Academic credibility score:** {citation_analysis.get('academic_credibility_score', 0):.1f}/10.0")
            academic_synthesis.append("")
            academic_synthesis.append("### Journal Distribution")
            for journal, count in analytics.get("journal_distribution", {}).items():
                academic_synthesis.append(f"- {journal}: {count} papers")
            academic_synthesis.append("")
            academic_synthesis.append("### Author Analysis")
            academic_synthesis.append(f"- **Total unique authors:** {analytics.get('author_analysis', {}).get('total_authors', 0)}")
            academic_synthesis.append("- **Most frequent authors:**")
            for author, count in analytics.get("author_analysis", {}).get("most_frequent_authors", {}).items():
                academic_synthesis.append(f"  - {author}: {count} papers")
        
        return "\n".join(academic_synthesis)

async def demonstrate_citation_integration():
    """Demonstrate the citation mapping integration"""
    print("🎯 CITATION MAPPING INTEGRATION DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Initialize mock synthesizer
    synthesizer = MockResearchSynthesizer()
    
    # Simulate paper synthesis
    print("📚 Synthesizing papers with citation analysis...")
    paper_ids = ["paper_1", "paper_2", "paper_3"]
    synthesis = await synthesizer.synthesize_papers(paper_ids)
    
    print(f"✅ Synthesis completed with {synthesis['citation_analysis']['total_citations']} citations")
    print()
    
    # Show citation analysis
    citation_analysis = synthesis["citation_analysis"]
    print("📊 CITATION ANALYSIS RESULTS:")
    print(f"   • Total citations: {citation_analysis['total_citations']}")
    print(f"   • Academic credibility score: {citation_analysis['academic_credibility_score']}/10.0")
    print(f"   • Citation quality: {citation_analysis['citation_quality']}")
    print()
    
    # Show analytics
    analytics = citation_analysis["citation_analytics"]
    print("📈 CITATION ANALYTICS:")
    print(f"   • Year range: {analytics['year_range']['min']} - {analytics['year_range']['max']}")
    print(f"   • Average citations per paper: {analytics['citation_impact']['average_citations_per_paper']:.1f}")
    print(f"   • Highly cited papers (>100 citations): {analytics['citation_impact']['highly_cited_papers']}")
    print()
    
    # Export in different formats
    print("📄 EXPORTING ACADEMIC SYNTHESIS...")
    print()
    
    # APA format
    print("🔤 APA FORMAT EXPORT:")
    print("-" * 40)
    apa_export = await synthesizer.export_academic_synthesis(synthesis, "APA")
    print(apa_export[:1000] + "..." if len(apa_export) > 1000 else apa_export)
    print()
    
    # BibTeX format
    print("📋 BIBTEX FORMAT EXPORT:")
    print("-" * 40)
    bibtex_export = await synthesizer.export_academic_synthesis(synthesis, "BIBTEX")
    print(bibtex_export[:1000] + "..." if len(bibtex_export) > 1000 else bibtex_export)
    print()
    
    # Show citation network example
    print("🕸️  CITATION NETWORK EXAMPLE:")
    print("-" * 40)
    print("Paper A (2023)")
    print("├── References Paper B (2022)")
    print("├── References Paper C (2021)")
    print("└── Cited by Paper D (2024)")
    print()
    
    # Show academic credibility features
    print("🎓 ACADEMIC CREDIBILITY FEATURES:")
    print("-" * 40)
    print("✅ Proper citation formatting (APA, MLA, Chicago, Harvard, BibTeX)")
    print("✅ Citation network analysis")
    print("✅ Citation impact metrics")
    print("✅ Author and journal distribution analysis")
    print("✅ Academic credibility scoring")
    print("✅ Exportable reference lists")
    print("✅ Integration with research synthesis")
    print()
    
    print("🚀 CITATION MAPPING INTEGRATION COMPLETE!")
    print("The system now provides academic credibility and proper citation tracking.")

if __name__ == "__main__":
    asyncio.run(demonstrate_citation_integration())
