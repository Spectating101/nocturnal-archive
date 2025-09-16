#!/usr/bin/env python3
"""
Simple Citation Mapping Demonstration
Shows key citation features without async complexity
"""

from datetime import datetime
from typing import List, Dict, Any

# Import our citation manager classes
from src.services.research_service.citation_manager import (
    CitationManager, Citation, CitedFinding, CitationNetwork, CitationFormat
)

class SimpleCitationDemo:
    """Simple demonstration of citation mapping features"""
    
    def __init__(self):
        self.citation_manager = CitationManager()
        self.sample_citations = self._create_sample_citations()
    
    def _create_sample_citations(self) -> List[Citation]:
        """Create diverse sample citations for demonstration"""
        return [
            Citation(
                citation_id="CIT_ABC12345",
                title="Advances in Machine Learning for Scientific Discovery",
                authors=["Smith, J.", "Johnson, A.", "Brown, M."],
                year=2023,
                journal="Nature Machine Intelligence",
                doi="10.1038/s42256-023-00001-x",
                citation_count=150,
                volume="5",
                issue="2",
                pages="123-145"
            ),
            Citation(
                citation_id="CIT_DEF67890",
                title="Deep Learning Applications in Drug Discovery",
                authors=["Wilson, R.", "Davis, K."],
                year=2022,
                journal="Science",
                doi="10.1126/science.abc1234",
                citation_count=89,
                volume="375",
                issue="6582",
                pages="456-478"
            ),
            Citation(
                citation_id="CIT_GHI11111",
                title="Transformer Models for Protein Structure Prediction",
                authors=["Anderson, L.", "Taylor, P.", "Miller, S.", "Clark, J."],
                year=2024,
                journal="Cell",
                doi="10.1016/j.cell.2024.01.001",
                citation_count=67,
                volume="187",
                issue="1",
                pages="89-112"
            ),
            Citation(
                citation_id="CIT_JKL22222",
                title="Interpretable AI in Biomedical Research",
                authors=["Garcia, M."],
                year=2023,
                journal="Nature Biotechnology",
                doi="10.1038/nbt.2023.045",
                citation_count=234,
                volume="41",
                issue="8",
                pages="1123-1145"
            ),
            Citation(
                citation_id="CIT_MNO33333",
                title="Multi-modal Data Integration in Drug Discovery",
                authors=["Lee, S.", "Park, J.", "Kim, H.", "Choi, Y.", "Wang, L."],
                year=2024,
                journal="Nature Methods",
                doi="10.1038/nmeth.2024.012",
                citation_count=45,
                volume="21",
                issue="3",
                pages="234-256"
            )
        ]
    
    def demonstrate_citation_formatting(self):
        """Demonstrate different citation formats"""
        print("🔤 CITATION FORMATTING DEMONSTRATION")
        print("=" * 50)
        print()
        
        citation = self.sample_citations[0]  # Use the first citation
        
        print(f"📄 Original Citation: {citation.title}")
        print(f"   Authors: {', '.join(citation.authors)}")
        print(f"   Year: {citation.year}")
        print(f"   Journal: {citation.journal}")
        print(f"   DOI: {citation.doi}")
        print()
        
        # Show different formats
        formats = [
            (CitationFormat.APA, "APA Style"),
            (CitationFormat.MLA, "MLA Style"),
            (CitationFormat.CHICAGO, "Chicago Style"),
            (CitationFormat.HARVARD, "Harvard Style"),
            (CitationFormat.BIBTEX, "BibTeX Format")
        ]
        
        for format_type, format_name in formats:
            formatted = self.citation_manager.format_citation(citation, format_type)
            print(f"📋 {format_name}:")
            print(f"   {formatted}")
            print()
    
    def demonstrate_citation_analytics(self):
        """Demonstrate citation analytics"""
        print("📊 CITATION ANALYTICS DEMONSTRATION")
        print("=" * 50)
        print()
        
        # Calculate basic statistics manually
        total_citations = len(self.sample_citations)
        years = [citation.year for citation in self.sample_citations]
        citation_counts = [citation.citation_count for citation in self.sample_citations]
        
        print("📈 Basic Statistics:")
        print(f"   • Total citations analyzed: {total_citations}")
        print(f"   • Year range: {min(years)} - {max(years)}")
        print(f"   • Average publication year: {sum(years) / len(years):.1f}")
        print()
        
        print("🎯 Citation Impact:")
        print(f"   • Total citations received: {sum(citation_counts)}")
        print(f"   • Average citations per paper: {sum(citation_counts) / total_citations:.1f}")
        print(f"   • Highly cited papers (>100): {len([c for c in citation_counts if c > 100])}")
        print()
        
        print("📚 Journal Distribution:")
        journals = {}
        for citation in self.sample_citations:
            if citation.journal:
                journals[citation.journal] = journals.get(citation.journal, 0) + 1
        
        for journal, count in journals.items():
            print(f"   • {journal}: {count} papers")
        print()
        
        print("👥 Author Analysis:")
        all_authors = []
        for citation in self.sample_citations:
            all_authors.extend(citation.authors)
        
        author_counts = {}
        for author in all_authors:
            author_counts[author] = author_counts.get(author, 0) + 1
        
        print(f"   • Total unique authors: {len(set(all_authors))}")
        print("   • Most frequent authors:")
        sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
        for author, count in sorted_authors[:5]:
            print(f"     - {author}: {count} papers")
        print()
    
    def demonstrate_citation_networks(self):
        """Demonstrate citation network building"""
        print("🕸️  CITATION NETWORK DEMONSTRATION")
        print("=" * 50)
        print()
        
        # Create a mock citation network
        network = CitationNetwork(
            paper_id="PAPER_CENTRAL",
            references=[
                self.sample_citations[1],  # Wilson & Davis 2022
                self.sample_citations[2]   # Anderson et al. 2024
            ],
            citations=[
                self.sample_citations[3],  # Garcia 2023
                self.sample_citations[4]   # Lee et al. 2024
            ],
            related_papers=[],
            network_depth=2,
            total_connections=4,
            influence_score=2.0  # 2 citations / 1 reference
        )
        
        print("📄 Central Paper: Advances in Machine Learning for Scientific Discovery (2023)")
        print()
        
        print("📖 References (Papers this research builds upon):")
        for i, ref in enumerate(network.references, 1):
            print(f"   {i}. {ref.title}")
            print(f"      Authors: {', '.join(ref.authors)}")
            print(f"      Year: {ref.year}, Citations: {ref.citation_count}")
        print()
        
        print("📚 Citations (Papers that cite this research):")
        for i, cit in enumerate(network.citations, 1):
            print(f"   {i}. {cit.title}")
            print(f"      Authors: {', '.join(cit.authors)}")
            print(f"      Year: {cit.year}, Citations: {cit.citation_count}")
        print()
        
        print("📊 Network Metrics:")
        print(f"   • Total connections: {network.total_connections}")
        print(f"   • Network depth: {network.network_depth}")
        print(f"   • Influence score: {network.influence_score:.1f}")
        print(f"   • Citation-to-reference ratio: {len(network.citations)}:{len(network.references)}")
        print()
    
    def demonstrate_cited_findings(self):
        """Demonstrate cited findings with proper attribution"""
        print("🔍 CITED FINDINGS DEMONSTRATION")
        print("=" * 50)
        print()
        
        # Create cited findings
        findings = [
            {
                "text": "Machine learning models achieve 85% accuracy in drug discovery tasks",
                "citation": self.sample_citations[1],  # Wilson & Davis 2022
                "context": "Experimental validation on large drug discovery datasets",
                "methodology": "Deep learning with molecular fingerprints"
            },
            {
                "text": "Transformer architectures outperform traditional methods by 23%",
                "citation": self.sample_citations[2],  # Anderson et al. 2024
                "context": "Comparative study across multiple protein structure datasets",
                "methodology": "Attention-based neural networks"
            },
            {
                "text": "Interpretable AI models increase researcher trust by 67%",
                "citation": self.sample_citations[3],  # Garcia 2023
                "context": "Survey of biomedical researchers using AI tools",
                "methodology": "Mixed-methods study with qualitative interviews"
            }
        ]
        
        print("📝 Research Findings with Proper Citations:")
        print()
        
        for i, finding_data in enumerate(findings, 1):
            cited_finding = self.citation_manager.create_cited_finding(
                finding_text=finding_data["text"],
                citation=finding_data["citation"],
                context=finding_data["context"],
                methodology=finding_data["methodology"]
            )
            
            print(f"🔬 Finding {i}: {cited_finding.text}")
            print(f"   📚 Source: {', '.join(cited_finding.citation.authors)} ({cited_finding.citation.year})")
            print(f"   📖 Context: {cited_finding.context}")
            print(f"   🔬 Methodology: {cited_finding.methodology}")
            print(f"   🎯 Confidence: {cited_finding.confidence_score:.2f}")
            print(f"   🆔 Finding ID: {cited_finding.finding_id}")
            print()
    
    def demonstrate_academic_export(self):
        """Demonstrate academic export functionality"""
        print("📄 ACADEMIC EXPORT DEMONSTRATION")
        print("=" * 50)
        print()
        
        # Create a mock synthesis
        synthesis = {
            "common_findings": [
                {"finding": "Machine learning models achieve 85% accuracy in drug discovery tasks"},
                {"finding": "Transformer architectures outperform traditional methods by 23%"},
                {"finding": "Interpretable AI models increase researcher trust by 67%"}
            ],
            "research_gaps": [
                {"gap": "Limited research on interpretability of deep learning models"},
                {"gap": "Need for more diverse datasets in protein structure prediction"}
            ],
            "citation_analysis": {
                "cited_findings": [
                    {
                        "citation": self.sample_citations[1],
                        "text": "Machine learning models achieve 85% accuracy in drug discovery tasks"
                    },
                    {
                        "citation": self.sample_citations[2],
                        "text": "Transformer architectures outperform traditional methods by 23%"
                    },
                    {
                        "citation": self.sample_citations[3],
                        "text": "Interpretable AI models increase researcher trust by 67%"
                    }
                ],
                "formatted_citations": {
                    "apa": "\n\n".join([
                        self.citation_manager.format_citation(cit, CitationFormat.APA)
                        for cit in [self.sample_citations[1], self.sample_citations[2], self.sample_citations[3]]
                    ])
                },
                "academic_credibility_score": 8.7
            }
        }
        
        print("📋 APA Format Academic Export:")
        print("-" * 30)
        
        # Simulate academic export
        academic_report = []
        academic_report.append("# Research Synthesis Report")
        academic_report.append("")
        academic_report.append(f"*Generated on: {datetime.now().strftime('%B %d, %Y')}*")
        academic_report.append("")
        
        # Key Findings
        academic_report.append("## Key Findings")
        academic_report.append("")
        for i, finding in enumerate(synthesis["common_findings"], 1):
            academic_report.append(f"{i}. {finding['finding']}")
            if i <= len(synthesis["citation_analysis"]["cited_findings"]):
                citation = synthesis["citation_analysis"]["cited_findings"][i-1]["citation"]
                authors = citation.authors
                if len(authors) == 1:
                    author_cite = authors[0]
                elif len(authors) == 2:
                    author_cite = f"{authors[0]} and {authors[1]}"
                else:
                    author_cite = f"{authors[0]} et al."
                academic_report.append(f"   *Source: {author_cite} ({citation.year})*")
            academic_report.append("")
        
        # Research Gaps
        academic_report.append("## Research Gaps")
        academic_report.append("")
        for gap in synthesis["research_gaps"]:
            academic_report.append(f"- {gap['gap']}")
        academic_report.append("")
        
        # References
        academic_report.append("## References")
        academic_report.append("")
        citations_text = synthesis["citation_analysis"]["formatted_citations"]["apa"]
        citations_list = citations_text.split("\n\n")
        for i, citation in enumerate(citations_list, 1):
            if citation.strip():
                academic_report.append(f"{i}. {citation.strip()}")
        
        # Academic Credibility
        academic_report.append("")
        academic_report.append("## Academic Credibility")
        academic_report.append("")
        academic_report.append(f"- **Academic credibility score:** {synthesis['citation_analysis']['academic_credibility_score']:.1f}/10.0")
        academic_report.append("- **Citation quality:** High")
        academic_report.append("- **Reference completeness:** All findings properly cited")
        
        print("\n".join(academic_report))
        print()
    
    def demonstrate_citation_extraction(self):
        """Demonstrate citation extraction from different sources"""
        print("🔍 CITATION EXTRACTION DEMONSTRATION")
        print("=" * 50)
        print()
        
        # Mock paper data with different citation sources
        paper_data = {
            "title": "Comprehensive Review of AI in Drug Discovery",
            "authors": ["Researcher, A.", "Scientist, B."],
            "year": 2024,
            "references": [
                {
                    "title": "Deep Learning in Drug Discovery",
                    "authors": ["Smith, J.", "Johnson, A."],
                    "year": 2023,
                    "journal": "Nature Reviews Drug Discovery"
                },
                {
                    "title": "Machine Learning Applications",
                    "authors": ["Brown, M."],
                    "year": 2022,
                    "journal": "Science"
                }
            ],
            "content": """
            Recent advances in artificial intelligence have revolutionized drug discovery.
            Smith et al. (2023) demonstrated significant improvements in molecular screening.
            Brown (2022) showed that machine learning can predict drug efficacy with high accuracy.
            """
        }
        
        print("📄 Paper: Comprehensive Review of AI in Drug Discovery")
        print(f"   Authors: {', '.join(paper_data['authors'])}")
        print(f"   Year: {paper_data['year']}")
        print()
        
        # Extract citations manually
        citations = []
        
        # From metadata
        for ref in paper_data["references"]:
            citation = Citation(
                citation_id=self.citation_manager.generate_citation_id(
                    ref["title"], ref["authors"], ref["year"]
                ),
                title=ref["title"],
                authors=ref["authors"],
                year=ref["year"],
                journal=ref["journal"],
                confidence_score=1.0
            )
            citations.append(citation)
        
        # From text content (simplified)
        text_citations = [
            Citation(
                citation_id="TEXT_SMITH2023",
                title="Referenced work by Smith et al.",
                authors=["Smith, J.", "Johnson, A."],
                year=2023,
                confidence_score=0.7
            ),
            Citation(
                citation_id="TEXT_BROWN2022",
                title="Referenced work by Brown",
                authors=["Brown, M."],
                year=2022,
                confidence_score=0.7
            )
        ]
        citations.extend(text_citations)
        
        print("🔍 Extracted Citations:")
        for i, citation in enumerate(citations, 1):
            print(f"   {i}. {citation.title}")
            print(f"      Authors: {', '.join(citation.authors)}")
            print(f"      Year: {citation.year}")
            if citation.journal:
                print(f"      Journal: {citation.journal}")
            print(f"      Citation ID: {citation.citation_id}")
            print(f"      Confidence: {citation.confidence_score:.1f}")
            print()
        
        print(f"📊 Extraction Summary:")
        print(f"   • Total citations extracted: {len(citations)}")
        print(f"   • From metadata: {len([c for c in citations if c.confidence_score == 1.0])}")
        print(f"   • From text content: {len([c for c in citations if c.confidence_score < 1.0])}")
        print()
    
    def run_full_demonstration(self):
        """Run the complete interactive demonstration"""
        print("🎯 SIMPLE CITATION MAPPING DEMONSTRATION")
        print("=" * 60)
        print()
        
        # Run all demonstrations
        self.demonstrate_citation_formatting()
        print("\n" + "="*60 + "\n")
        
        self.demonstrate_citation_analytics()
        print("\n" + "="*60 + "\n")
        
        self.demonstrate_citation_networks()
        print("\n" + "="*60 + "\n")
        
        self.demonstrate_cited_findings()
        print("\n" + "="*60 + "\n")
        
        self.demonstrate_citation_extraction()
        print("\n" + "="*60 + "\n")
        
        self.demonstrate_academic_export()
        print("\n" + "="*60 + "\n")
        
        print("🚀 SIMPLE DEMONSTRATION COMPLETE!")
        print("The citation mapping system provides comprehensive academic credibility features.")

def main():
    """Run the simple demonstration"""
    demo = SimpleCitationDemo()
    demo.run_full_demonstration()

if __name__ == "__main__":
    main()
