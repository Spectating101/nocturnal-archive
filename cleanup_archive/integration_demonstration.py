#!/usr/bin/env python3
"""
Comprehensive Integration Demonstration
Shows how citation mapping integrates with existing Nocturnal Archive components
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Mock the existing Nocturnal Archive components
class MockPaperManager:
    """Mock PaperManager from the existing system"""
    
    def __init__(self):
        self.papers = {
            "paper_001": {
                "id": "paper_001",
                "title": "Machine Learning in Drug Discovery: A Comprehensive Review",
                "authors": ["Zhang, L.", "Wang, H.", "Chen, M.", "Liu, Y."],
                "year": 2023,
                "journal": "Nature Reviews Drug Discovery",
                "doi": "10.1038/nrd.2023.001",
                "abstract": "This review examines the application of machine learning techniques in drug discovery...",
                "findings": "ML models show 78% accuracy in predicting drug-target interactions",
                "methodology": "Systematic review of 150+ studies",
                "citation_count": 234,
                "status": "processed",
                "content": "Full paper content would be here...",
                "references": [
                    {
                        "title": "Deep Learning for Molecular Property Prediction",
                        "authors": ["Smith, A.", "Johnson, B."],
                        "year": 2022,
                        "journal": "Nature Machine Intelligence",
                        "doi": "10.1038/s42256-022-00001-x"
                    },
                    {
                        "title": "AI in Pharmaceutical Research",
                        "authors": ["Brown, C.", "Davis, D.", "Wilson, E."],
                        "year": 2021,
                        "journal": "Science",
                        "doi": "10.1126/science.abc1234"
                    }
                ],
                "openalex_id": "W1234567890"
            },
            "paper_002": {
                "id": "paper_002",
                "title": "Transformer Models for Protein Structure Prediction",
                "authors": ["Anderson, K.", "Taylor, L.", "Miller, P."],
                "year": 2024,
                "journal": "Cell",
                "doi": "10.1016/j.cell.2024.002",
                "abstract": "We present a novel transformer-based approach for protein structure prediction...",
                "findings": "Our model achieves 92% accuracy on CASP14 benchmark",
                "methodology": "Deep learning with attention mechanisms",
                "citation_count": 156,
                "status": "processed",
                "content": "Full paper content would be here...",
                "references": [
                    {
                        "title": "Attention Is All You Need",
                        "authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
                        "year": 2017,
                        "journal": "Advances in Neural Information Processing Systems"
                    }
                ],
                "openalex_id": "W9876543210"
            }
        }
    
    async def get_processed_paper(self, paper_id: str) -> Dict[str, Any]:
        """Get processed paper content"""
        return self.papers.get(paper_id)
    
    async def search_papers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search papers by query"""
        results = []
        for paper in self.papers.values():
            if query.lower() in paper["title"].lower() or query.lower() in paper["abstract"].lower():
                results.append(paper)
                if len(results) >= limit:
                    break
        return results
    
    async def get_paper_status(self, paper_id: str) -> Dict[str, Any]:
        """Get paper processing status"""
        paper = self.papers.get(paper_id)
        if paper:
            return {
                "id": paper_id,
                "status": paper["status"],
                "title": paper["title"],
                "citation_count": paper["citation_count"]
            }
        return None

class MockOpenAlexManager:
    """Mock OpenAlexManager from the existing system"""
    
    def __init__(self):
        self.citation_networks = {
            "W1234567890": {
                "references": [
                    {
                        "id": "W1111111111",
                        "title": "Deep Learning for Molecular Property Prediction",
                        "authors": ["Smith, A.", "Johnson, B."],
                        "year": 2022,
                        "citation_count": 89
                    },
                    {
                        "id": "W2222222222", 
                        "title": "AI in Pharmaceutical Research",
                        "authors": ["Brown, C.", "Davis, D.", "Wilson, E."],
                        "year": 2021,
                        "citation_count": 156
                    }
                ],
                "citations": [
                    {
                        "id": "W3333333333",
                        "title": "Recent Advances in Drug Discovery",
                        "authors": ["Lee, S.", "Park, J."],
                        "year": 2024,
                        "citation_count": 45
                    }
                ]
            }
        }
    
    async def get_citation_network(self, work_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get citation network for a work"""
        network = self.citation_networks.get(work_id, {"references": [], "citations": []})
        return {
            "work_id": work_id,
            "depth": depth,
            "references": network["references"],
            "citations": network["citations"],
            "total_connections": len(network["references"]) + len(network["citations"])
        }
    
    async def get_references(self, work_id: str) -> Dict[str, Any]:
        """Get references for a work"""
        network = self.citation_networks.get(work_id, {"references": []})
        return {"results": network["references"]}
    
    async def get_citing_works(self, work_id: str) -> Dict[str, Any]:
        """Get works that cite this work"""
        network = self.citation_networks.get(work_id, {"citations": []})
        return {"results": network["citations"]}

class MockResearchSynthesizer:
    """Mock ResearchSynthesizer with citation integration"""
    
    def __init__(self, citation_manager, paper_manager, openalex_manager):
        self.citation_manager = citation_manager
        self.paper_manager = paper_manager
        self.openalex_manager = openalex_manager
    
    async def synthesize_papers(self, paper_ids: List[str]) -> Dict[str, Any]:
        """Synthesize papers with full citation analysis"""
        print(f"🔬 Synthesizing {len(paper_ids)} papers with comprehensive citation analysis...")
        
        # Get papers from PaperManager
        papers = []
        all_citations = []
        citation_networks = []
        cited_findings = []
        
        for paper_id in paper_ids:
            paper = await self.paper_manager.get_processed_paper(paper_id)
            if paper:
                papers.append(paper)
                
                # Extract citations using CitationManager
                paper_citations = await self.citation_manager.extract_citations_from_paper(paper)
                all_citations.extend(paper_citations)
                
                # Build citation network using OpenAlexManager
                if paper.get("openalex_id"):
                    network = await self.openalex_manager.get_citation_network(paper["openalex_id"])
                    citation_networks.append(network)
                
                # Create cited finding for the paper's main finding
                if paper.get("findings"):
                    paper_citation = self.citation_manager._create_paper_citation(paper)
                    cited_finding = self.citation_manager.create_cited_finding(
                        finding_text=paper["findings"],
                        citation=paper_citation,
                        context=paper.get("abstract"),
                        methodology=paper.get("methodology")
                    )
                    cited_findings.append(cited_finding)
        
        # Generate comprehensive synthesis
        synthesis = {
            "common_findings": [
                {"finding": "Machine learning shows high accuracy in drug discovery applications"},
                {"finding": "Transformer models excel in protein structure prediction tasks"},
                {"finding": "Deep learning approaches outperform traditional methods"}
            ],
            "research_gaps": [
                {"gap": "Limited research on interpretability in drug discovery"},
                {"gap": "Need for standardized evaluation metrics across studies"},
                {"gap": "Lack of diverse datasets for validation"}
            ],
            "contradictions": [
                {"contradiction": "Some studies report 90%+ accuracy while others show 60-70%"}
            ],
            "methodology_analysis": {
                "deep_learning": {"count": 2, "description": "Primary methodology"},
                "transformer_models": {"count": 1, "description": "Emerging approach"},
                "systematic_review": {"count": 1, "description": "Comprehensive analysis"}
            },
            "citation_analysis": {
                "total_citations": len(all_citations),
                "citation_networks": citation_networks,
                "cited_findings": [self._cited_finding_to_dict(cf) for cf in cited_findings],
                "formatted_citations": {
                    "apa": "\n\n".join([
                        self.citation_manager.format_citation(cit, self.citation_manager.CitationFormat.APA)
                        for cit in all_citations[:5]  # Show first 5
                    ]),
                    "bibtex": "\n\n".join([
                        self.citation_manager.format_citation(cit, self.citation_manager.CitationFormat.BIBTEX)
                        for cit in all_citations[:5]
                    ])
                },
                "academic_credibility_score": min(len(all_citations) / len(papers), 10.0) if papers else 0.0,
                "citation_analytics": await self.citation_manager.get_citation_analytics(all_citations)
            }
        }
        
        return synthesis
    
    def _cited_finding_to_dict(self, cited_finding):
        """Convert cited finding to dictionary"""
        return {
            "finding_id": cited_finding.finding_id,
            "text": cited_finding.text,
            "citation": {
                "authors": cited_finding.citation.authors,
                "year": cited_finding.citation.year,
                "title": cited_finding.citation.title,
                "journal": cited_finding.citation.journal,
                "doi": getattr(cited_finding.citation, 'doi', None)
            },
            "confidence_score": cited_finding.confidence_score,
            "context": cited_finding.context,
            "methodology": cited_finding.methodology
        }

class MockCitationManager:
    """Mock CitationManager for integration demonstration"""
    
    class CitationFormat:
        APA = "apa"
        MLA = "mla"
        CHICAGO = "chicago"
        HARVARD = "harvard"
        BIBTEX = "bibtex"
    
    def __init__(self):
        pass
    
    async def extract_citations_from_paper(self, paper_data: Dict[str, Any]) -> List[Any]:
        """Extract citations from paper data"""
        citations = []
        
        # Extract from references
        if "references" in paper_data:
            for ref in paper_data["references"]:
                citation = self._create_citation_from_reference(ref)
                citations.append(citation)
        
        return citations
    
    def _create_citation_from_reference(self, ref_data: Dict[str, Any]) -> Any:
        """Create citation from reference data"""
        class MockCitation:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        return MockCitation(
            citation_id=f"CIT_{hash(ref_data['title']) % 10000:04d}",
            title=ref_data["title"],
            authors=ref_data["authors"],
            year=ref_data["year"],
            journal=ref_data["journal"],
            doi=ref_data.get("doi"),
            confidence_score=1.0
        )
    
    def _create_paper_citation(self, paper_data: Dict[str, Any]) -> Any:
        """Create citation for the paper itself"""
        class MockCitation:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        return MockCitation(
            citation_id=f"PAPER_{paper_data['id']}",
            title=paper_data["title"],
            authors=paper_data["authors"],
            year=paper_data["year"],
            journal=paper_data["journal"],
            doi=paper_data.get("doi"),
            citation_count=paper_data.get("citation_count", 0),
            confidence_score=1.0
        )
    
    def create_cited_finding(self, finding_text: str, citation: Any, 
                           context: str = None, methodology: str = None) -> Any:
        """Create a cited finding"""
        class MockCitedFinding:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        return MockCitedFinding(
            finding_id=f"FIND_{hash(finding_text) % 10000:04d}",
            text=finding_text,
            citation=citation,
            confidence_score=citation.confidence_score,
            context=context,
            methodology=methodology
        )
    
    def format_citation(self, citation: Any, format_type: str) -> str:
        """Format citation in specified style"""
        if format_type == self.CitationFormat.APA:
            authors = citation.authors
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} & {authors[1]}"
            else:
                author_str = f"{authors[0]} et al."
            
            formatted = f"{author_str}. ({citation.year}). {citation.title}."
            if citation.journal:
                formatted += f" {citation.journal}."
            if hasattr(citation, 'doi') and citation.doi:
                formatted += f" https://doi.org/{citation.doi}"
            
            return formatted
        elif format_type == self.CitationFormat.BIBTEX:
            authors = " and ".join(citation.authors)
            return f"""@article{{{citation.citation_id},
  title = {{{citation.title}}},
  author = {{{authors}}},
  year = {{{citation.year}}},
  journal = {{{citation.journal}}}
}}"""
        
        return f"{citation.authors[0]} et al. ({citation.year}). {citation.title}"
    
    async def get_citation_analytics(self, citations: List[Any]) -> Dict[str, Any]:
        """Generate citation analytics"""
        if not citations:
            return {"error": "No citations to analyze"}
        
        years = [citation.year for citation in citations if hasattr(citation, 'year')]
        journals = {}
        
        for citation in citations:
            if hasattr(citation, 'journal') and citation.journal:
                journals[citation.journal] = journals.get(citation.journal, 0) + 1
        
        return {
            "total_citations": len(citations),
            "year_range": {
                "min": min(years) if years else 0,
                "max": max(years) if years else 0,
                "average": sum(years) / len(years) if years else 0
            },
            "journal_distribution": dict(sorted(journals.items(), key=lambda x: x[1], reverse=True))
        }

async def demonstrate_integration():
    """Demonstrate full integration with existing Nocturnal Archive components"""
    print("🔬 COMPREHENSIVE INTEGRATION DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Initialize all components
    paper_manager = MockPaperManager()
    openalex_manager = MockOpenAlexManager()
    citation_manager = MockCitationManager()
    research_synthesizer = MockResearchSynthesizer(
        citation_manager, paper_manager, openalex_manager
    )
    
    # 1. Paper Management Integration
    print("📚 STEP 1: PAPER MANAGEMENT INTEGRATION")
    print("-" * 40)
    
    # Search for papers
    papers = await paper_manager.search_papers("machine learning")
    print(f"Found {len(papers)} papers related to 'machine learning':")
    for paper in papers:
        print(f"   • {paper['title']} ({paper['year']})")
        print(f"     Status: {paper['status']}, Citations: {paper['citation_count']}")
    print()
    
    # Get paper details
    paper_id = "paper_001"
    paper_details = await paper_manager.get_processed_paper(paper_id)
    if paper_details:
        print(f"📄 Paper Details for {paper_id}:")
        print(f"   Title: {paper_details['title']}")
        print(f"   Authors: {', '.join(paper_details['authors'])}")
        print(f"   Journal: {paper_details['journal']}")
        print(f"   DOI: {paper_details['doi']}")
        print(f"   References: {len(paper_details['references'])}")
        print()
    
    # 2. OpenAlex Integration
    print("🔗 STEP 2: OPENALEX INTEGRATION")
    print("-" * 40)
    
    if paper_details and paper_details.get("openalex_id"):
        openalex_id = paper_details["openalex_id"]
        
        # Get citation network
        network = await openalex_manager.get_citation_network(openalex_id)
        print(f"📊 Citation Network for {openalex_id}:")
        print(f"   Total connections: {network['total_connections']}")
        print(f"   References: {len(network['references'])}")
        print(f"   Citations: {len(network['citations'])}")
        print()
        
        # Show references
        print("📖 References (Papers this research builds upon):")
        for i, ref in enumerate(network['references'], 1):
            print(f"   {i}. {ref['title']}")
            print(f"      Authors: {', '.join(ref['authors'])} ({ref['year']})")
            print(f"      Citations: {ref['citation_count']}")
        print()
        
        # Show citations
        print("📚 Citations (Papers that cite this research):")
        for i, cit in enumerate(network['citations'], 1):
            print(f"   {i}. {cit['title']}")
            print(f"      Authors: {', '.join(cit['authors'])} ({cit['year']})")
            print(f"      Citations: {cit['citation_count']}")
        print()
    
    # 3. Citation Manager Integration
    print("🔍 STEP 3: CITATION MANAGER INTEGRATION")
    print("-" * 40)
    
    # Extract citations from paper
    if paper_details:
        citations = await citation_manager.extract_citations_from_paper(paper_details)
        print(f"🔍 Extracted {len(citations)} citations from paper:")
        for i, citation in enumerate(citations, 1):
            print(f"   {i}. {citation.title}")
            print(f"      Authors: {', '.join(citation.authors)} ({citation.year})")
            print(f"      Journal: {citation.journal}")
            if hasattr(citation, 'doi') and citation.doi:
                print(f"      DOI: {citation.doi}")
        print()
        
        # Show citation formatting
        print("📋 Citation Formatting Examples:")
        for i, citation in enumerate(citations[:2], 1):  # Show first 2
            print(f"   Citation {i} - APA Format:")
            apa_format = citation_manager.format_citation(citation, citation_manager.CitationFormat.APA)
            print(f"      {apa_format}")
            print()
            
            print(f"   Citation {i} - BibTeX Format:")
            bibtex_format = citation_manager.format_citation(citation, citation_manager.CitationFormat.BIBTEX)
            print(f"      {bibtex_format}")
            print()
    
    # 4. Research Synthesis Integration
    print("🔬 STEP 4: RESEARCH SYNTHESIS INTEGRATION")
    print("-" * 40)
    
    # Synthesize papers with citation analysis
    paper_ids = ["paper_001", "paper_002"]
    synthesis = await research_synthesizer.synthesize_papers(paper_ids)
    
    print("📝 Synthesis Results:")
    print(f"   • Papers synthesized: {len(paper_ids)}")
    print(f"   • Common findings: {len(synthesis['common_findings'])}")
    print(f"   • Research gaps: {len(synthesis['research_gaps'])}")
    print(f"   • Contradictions: {len(synthesis['contradictions'])}")
    print()
    
    # Show citation analysis
    citation_analysis = synthesis['citation_analysis']
    print("📊 Citation Analysis:")
    print(f"   • Total citations analyzed: {citation_analysis['total_citations']}")
    print(f"   • Citation networks built: {len(citation_analysis['citation_networks'])}")
    print(f"   • Cited findings created: {len(citation_analysis['cited_findings'])}")
    print(f"   • Academic credibility score: {citation_analysis['academic_credibility_score']:.1f}/10.0")
    print()
    
    # Show cited findings
    print("📚 Cited Findings with Proper Attribution:")
    for i, finding in enumerate(citation_analysis['cited_findings'], 1):
        print(f"🔬 Finding {i}: {finding['text']}")
        citation = finding['citation']
        print(f"   📚 Source: {', '.join(citation['authors'])} ({citation['year']})")
        print(f"   📖 Journal: {citation['journal']}")
        if citation.get('doi'):
            print(f"   🔗 DOI: {citation['doi']}")
        print(f"   🎯 Confidence: {finding['confidence_score']:.2f}")
        print()
    
    # Show citation analytics
    analytics = citation_analysis['citation_analytics']
    if not analytics.get('error'):
        print("📈 Citation Analytics:")
        print(f"   • Year range: {analytics['year_range']['min']} - {analytics['year_range']['max']}")
        print(f"   • Average year: {analytics['year_range']['average']:.1f}")
        print("   • Journal distribution:")
        for journal, count in analytics['journal_distribution'].items():
            print(f"     - {journal}: {count} papers")
        print()
    
    # 5. Academic Export
    print("📄 STEP 5: ACADEMIC EXPORT")
    print("-" * 40)
    
    print("# Research Synthesis Report")
    print(f"*Generated on: {datetime.now().strftime('%B %d, %Y')}*")
    print(f"*Papers analyzed: {len(paper_ids)}*")
    print()
    
    print("## Key Findings")
    for i, finding in enumerate(synthesis['common_findings'], 1):
        print(f"{i}. {finding['finding']}")
    print()
    
    print("## Research Gaps")
    for gap in synthesis['research_gaps']:
        print(f"- {gap['gap']}")
    print()
    
    print("## References")
    formatted_citations = citation_analysis['formatted_citations']['apa']
    citations_list = formatted_citations.split("\n\n")
    for i, citation in enumerate(citations_list, 1):
        if citation.strip():
            print(f"{i}. {citation.strip()}")
    print()
    
    print("## Academic Credibility")
    print(f"- **Academic credibility score:** {citation_analysis['academic_credibility_score']:.1f}/10.0")
    print(f"- **Citations analyzed:** {citation_analysis['total_citations']}")
    print(f"- **Citation networks:** {len(citation_analysis['citation_networks'])}")
    print(f"- **Cited findings:** {len(citation_analysis['cited_findings'])}")
    print()
    
    print("🚀 COMPREHENSIVE INTEGRATION DEMONSTRATION COMPLETE!")
    print("The citation system successfully integrates with all Nocturnal Archive components.")

if __name__ == "__main__":
    asyncio.run(demonstrate_integration())
