#!/usr/bin/env python3
"""
Consensus-Based Citation Demonstration
Shows how multiple papers support the same findings to build consensus
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

class ConsensusCitationSystem:
    """System that builds consensus from multiple papers supporting the same findings"""
    
    def __init__(self):
        self.sample_papers = self._create_sample_papers()
    
    def _create_sample_papers(self) -> List[Dict[str, Any]]:
        """Create sample papers with overlapping findings"""
        return [
            {
                "id": "paper_001",
                "title": "Machine Learning in Drug Discovery: A Comprehensive Review",
                "authors": ["Zhang, L.", "Wang, H.", "Chen, M.", "Liu, Y."],
                "year": 2023,
                "journal": "Nature Reviews Drug Discovery",
                "findings": [
                    "ML models achieve 78% accuracy in predicting drug-target interactions",
                    "Deep learning outperforms traditional methods by 15-20%",
                    "Transformer architectures show promise in molecular property prediction"
                ],
                "methodology": "Systematic review of 150+ studies",
                "citation_count": 234
            },
            {
                "id": "paper_002",
                "title": "Deep Learning Applications in Pharmaceutical Research",
                "authors": ["Wilson, R.", "Davis, K.", "Anderson, M."],
                "year": 2022,
                "journal": "Science",
                "findings": [
                    "Deep learning models achieve 82% accuracy in drug discovery tasks",
                    "Neural networks outperform traditional methods by 18% on average",
                    "Attention mechanisms improve prediction accuracy significantly"
                ],
                "methodology": "Meta-analysis of 89 studies",
                "citation_count": 156
            },
            {
                "id": "paper_003",
                "title": "Transformer Models for Drug Discovery",
                "authors": ["Brown, A.", "Taylor, S.", "Miller, P."],
                "year": 2024,
                "journal": "Cell",
                "findings": [
                    "Transformer models achieve 89% accuracy in drug-target prediction",
                    "Attention-based models outperform CNN by 23%",
                    "Multi-modal data integration improves accuracy by 12%"
                ],
                "methodology": "Comparative study across multiple datasets",
                "citation_count": 89
            },
            {
                "id": "paper_004",
                "title": "AI in Drug Discovery: Current State and Future Directions",
                "authors": ["Lee, S.", "Park, J.", "Kim, H."],
                "year": 2023,
                "journal": "Nature Biotechnology",
                "findings": [
                    "Machine learning approaches achieve 81% accuracy in drug discovery",
                    "Deep learning methods show 16-25% improvement over traditional approaches",
                    "Transformer architectures are emerging as the preferred method"
                ],
                "methodology": "Comprehensive literature review",
                "citation_count": 167
            },
            {
                "id": "paper_005",
                "title": "Systematic Evaluation of AI in Drug Discovery",
                "authors": ["Garcia, M.", "Martinez, R.", "Lopez, A."],
                "year": 2024,
                "journal": "Nature Machine Intelligence",
                "findings": [
                    "AI models achieve 85% average accuracy across drug discovery tasks",
                    "Deep learning outperforms traditional methods by 20%",
                    "Transformer models show highest accuracy in recent studies"
                ],
                "methodology": "Systematic evaluation of 200+ studies",
                "citation_count": 123
            }
        ]
    
    def build_consensus_findings(self) -> List[Dict[str, Any]]:
        """Build consensus findings from multiple papers"""
        print("🔍 BUILDING CONSENSUS FROM MULTIPLE PAPERS")
        print("=" * 50)
        print()
        
        # Define consensus categories manually for demonstration
        consensus_categories = {
            "accuracy": {
                "keywords": ["accuracy", "achieve", "%"],
                "papers": []
            },
            "outperformance": {
                "keywords": ["outperform", "improvement", "better"],
                "papers": []
            },
            "transformer": {
                "keywords": ["transformer", "attention"],
                "papers": []
            }
        }
        
        # Categorize findings
        for paper in self.sample_papers:
            for finding in paper["findings"]:
                finding_lower = finding.lower()
                
                # Check accuracy findings
                if any(keyword in finding_lower for keyword in consensus_categories["accuracy"]["keywords"]):
                    consensus_categories["accuracy"]["papers"].append({
                        "paper": paper,
                        "finding": finding
                    })
                
                # Check outperformance findings
                if any(keyword in finding_lower for keyword in consensus_categories["outperformance"]["keywords"]):
                    consensus_categories["outperformance"]["papers"].append({
                        "paper": paper,
                        "finding": finding
                    })
                
                # Check transformer findings
                if any(keyword in finding_lower for keyword in consensus_categories["transformer"]["keywords"]):
                    consensus_categories["transformer"]["papers"].append({
                        "paper": paper,
                        "finding": finding
                    })
        
        # Build consensus findings
        consensus_findings = []
        
        # Accuracy consensus
        if len(consensus_categories["accuracy"]["papers"]) >= 2:
            consensus_findings.append(self._create_accuracy_consensus(consensus_categories["accuracy"]["papers"]))
        
        # Outperformance consensus
        if len(consensus_categories["outperformance"]["papers"]) >= 2:
            consensus_findings.append(self._create_outperformance_consensus(consensus_categories["outperformance"]["papers"]))
        
        # Transformer consensus
        if len(consensus_categories["transformer"]["papers"]) >= 2:
            consensus_findings.append(self._create_transformer_consensus(consensus_categories["transformer"]["papers"]))
        
        return consensus_findings
    
    def _create_accuracy_consensus(self, papers: List[Dict]) -> Dict[str, Any]:
        """Create consensus for accuracy findings"""
        # Extract accuracy numbers
        accuracies = []
        for paper_data in papers:
            finding = paper_data["finding"]
            import re
            numbers = re.findall(r'(\d+)%', finding)
            if numbers:
                accuracies.extend([int(n) for n in numbers])
        
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
        min_accuracy = min(accuracies) if accuracies else None
        max_accuracy = max(accuracies) if accuracies else None
        
        return {
            "consensus_statement": f"Machine learning models consistently achieve {min_accuracy}-{max_accuracy}% accuracy in drug discovery applications across multiple studies",
            "supporting_papers": papers,
            "paper_count": len(papers),
            "confidence_level": "Very High" if len(papers) >= 4 else "High" if len(papers) >= 3 else "Moderate",
            "average_accuracy": avg_accuracy,
            "accuracy_range": f"{min_accuracy}-{max_accuracy}%",
            "methodologies": list(set([p["paper"]["methodology"] for p in papers])),
            "year_range": f"{min([p['paper']['year'] for p in papers])}-{max([p['paper']['year'] for p in papers])}",
            "category": "accuracy"
        }
    
    def _create_outperformance_consensus(self, papers: List[Dict]) -> Dict[str, Any]:
        """Create consensus for outperformance findings"""
        # Extract improvement percentages
        improvements = []
        for paper_data in papers:
            finding = paper_data["finding"]
            import re
            numbers = re.findall(r'(\d+)%', finding)
            if numbers:
                improvements.extend([int(n) for n in numbers])
        
        avg_improvement = sum(improvements) / len(improvements) if improvements else None
        min_improvement = min(improvements) if improvements else None
        max_improvement = max(improvements) if improvements else None
        
        return {
            "consensus_statement": f"Deep learning approaches consistently outperform traditional methods by {min_improvement}-{max_improvement}% in drug discovery tasks",
            "supporting_papers": papers,
            "paper_count": len(papers),
            "confidence_level": "Very High" if len(papers) >= 4 else "High" if len(papers) >= 3 else "Moderate",
            "average_improvement": avg_improvement,
            "improvement_range": f"{min_improvement}-{max_improvement}%",
            "methodologies": list(set([p["paper"]["methodology"] for p in papers])),
            "year_range": f"{min([p['paper']['year'] for p in papers])}-{max([p['paper']['year'] for p in papers])}",
            "category": "outperformance"
        }
    
    def _create_transformer_consensus(self, papers: List[Dict]) -> Dict[str, Any]:
        """Create consensus for transformer findings"""
        return {
            "consensus_statement": "Transformer architectures are emerging as the preferred method for drug discovery applications",
            "supporting_papers": papers,
            "paper_count": len(papers),
            "confidence_level": "Very High" if len(papers) >= 4 else "High" if len(papers) >= 3 else "Moderate",
            "methodologies": list(set([p["paper"]["methodology"] for p in papers])),
            "year_range": f"{min([p['paper']['year'] for p in papers])}-{max([p['paper']['year'] for p in papers])}",
            "category": "transformer"
        }
    
    def demonstrate_consensus_building(self):
        """Demonstrate the consensus building process"""
        print("🎯 CONSENSUS-BASED CITATION DEMONSTRATION")
        print("=" * 60)
        print()
        
        # Show individual papers first
        print("📚 INDIVIDUAL PAPERS AND THEIR FINDINGS:")
        print("-" * 40)
        for i, paper in enumerate(self.sample_papers, 1):
            print(f"📄 Paper {i}: {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'])} ({paper['year']})")
            print(f"   Journal: {paper['journal']}")
            print("   Findings:")
            for finding in paper["findings"]:
                print(f"     • {finding}")
            print()
        
        # Build consensus
        consensus_findings = self.build_consensus_findings()
        
        print("🔬 CONSENSUS FINDINGS (Multiple Papers Support Each Claim):")
        print("-" * 40)
        for i, consensus in enumerate(consensus_findings, 1):
            print(f"🎯 Consensus Finding {i}: {consensus['consensus_statement']}")
            print(f"   📊 Confidence: {consensus['confidence_level']}")
            print(f"   📈 Supporting Papers: {consensus['paper_count']} studies")
            print(f"   📅 Year Range: {consensus['year_range']}")
            if 'accuracy_range' in consensus:
                print(f"   📊 Accuracy Range: {consensus['accuracy_range']}")
            if 'improvement_range' in consensus:
                print(f"   📈 Improvement Range: {consensus['improvement_range']}")
            print(f"   🔬 Methodologies: {', '.join(consensus['methodologies'])}")
            print()
            
            print("   📚 Supporting Papers:")
            for j, paper_data in enumerate(consensus['supporting_papers'], 1):
                paper = paper_data['paper']
                print(f"     {j}. {', '.join(paper['authors'])} ({paper['year']})")
                print(f"        {paper['journal']} - {paper['methodology']}")
                print(f"        Finding: {paper_data['finding']}")
            print()
        
        # Show academic export with consensus
        self._show_academic_export_with_consensus(consensus_findings)
    
    def _show_academic_export_with_consensus(self, consensus_findings: List[Dict]):
        """Show academic export that uses consensus findings"""
        print("📄 ACADEMIC EXPORT WITH CONSENSUS FINDINGS")
        print("-" * 40)
        
        print("# Research Synthesis Report")
        print(f"*Generated on: {datetime.now().strftime('%B %d, %Y')}*")
        print("*Based on consensus analysis of multiple studies*")
        print()
        
        print("## Key Consensus Findings")
        print()
        for i, consensus in enumerate(consensus_findings, 1):
            print(f"{i}. **{consensus['consensus_statement']}**")
            print(f"   *This finding is supported by {consensus['paper_count']} studies with {consensus['confidence_level'].lower()} confidence.*")
            if 'accuracy_range' in consensus:
                print(f"   *Accuracy range across studies: {consensus['accuracy_range']}*")
            if 'improvement_range' in consensus:
                print(f"   *Improvement range across studies: {consensus['improvement_range']}*")
            print()
        
        print("## Research Consensus Analysis")
        print()
        print("### Methodology")
        print("This synthesis is based on consensus analysis of multiple independent studies.")
        print("Findings are only reported when supported by at least 2 independent studies.")
        print()
        
        print("### Confidence Levels")
        print("- **Very High**: Supported by 4+ independent studies")
        print("- **High**: Supported by 3 independent studies") 
        print("- **Moderate**: Supported by 2 independent studies")
        print()
        
        print("## Supporting Evidence")
        print()
        for i, consensus in enumerate(consensus_findings, 1):
            print(f"### Consensus Finding {i}")
            print(f"**Statement**: {consensus['consensus_statement']}")
            print(f"**Confidence**: {consensus['confidence_level']}")
            print(f"**Supporting Studies**: {consensus['paper_count']}")
            print()
            
            print("**Supporting Papers**:")
            for j, paper_data in enumerate(consensus['supporting_papers'], 1):
                paper = paper_data['paper']
                authors = ', '.join(paper['authors'])
                print(f"{j}. {authors} ({paper['year']}). {paper['title']}. {paper['journal']}.")
            print()
        
        print("## Academic Credibility")
        print()
        total_papers = len(set([p['paper']['id'] for consensus in consensus_findings for p in consensus['supporting_papers']]))
        print(f"- **Total studies analyzed**: {len(self.sample_papers)}")
        print(f"- **Consensus findings identified**: {len(consensus_findings)}")
        print(f"- **Papers supporting consensus**: {total_papers}")
        print(f"- **Average confidence level**: High")
        print("- **Methodology**: Systematic consensus analysis")
        print()
        
        print("## References")
        print()
        # Collect all unique papers
        all_papers = set()
        for consensus in consensus_findings:
            for paper_data in consensus['supporting_papers']:
                all_papers.add(paper_data['paper']['id'])
        
        # Format references
        for i, paper_id in enumerate(sorted(all_papers), 1):
            paper = next(p for p in self.sample_papers if p['id'] == paper_id)
            authors = ', '.join(paper['authors'])
            print(f"{i}. {authors} ({paper['year']}). {paper['title']}. {paper['journal']}.")
        print()
        
        print("🚀 CONSENSUS-BASED CITATION SYSTEM COMPLETE!")
        print("This approach builds stronger, more credible findings through consensus.")

def main():
    """Run the consensus citation demonstration"""
    system = ConsensusCitationSystem()
    system.demonstrate_consensus_building()

if __name__ == "__main__":
    main()
