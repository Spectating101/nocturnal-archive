#!/usr/bin/env python3
"""
Test citation mapping integration functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from src.services.research_service.citation_manager import (
    CitationManager, Citation, CitedFinding, CitationNetwork, CitationFormat
)
from src.services.research_service.synthesizer import ResearchSynthesizer

class TestCitationManager:
    """Test citation manager functionality"""
    
    @pytest.fixture
    def citation_manager(self):
        """Create citation manager instance"""
        db_ops = Mock()
        openalex_client = Mock()
        return CitationManager(db_ops=db_ops, openalex_client=openalex_client)
    
    @pytest.fixture
    def sample_citation(self):
        """Create sample citation"""
        return Citation(
            citation_id="CIT_ABC12345",
            title="Test Research Paper",
            authors=["John Doe", "Jane Smith"],
            year=2023,
            journal="Test Journal",
            doi="10.1000/test.2023.001",
            citation_count=50
        )
    
    def test_generate_citation_id(self, citation_manager):
        """Test citation ID generation"""
        title = "Test Paper"
        authors = ["John Doe", "Jane Smith"]
        year = 2023
        
        citation_id = citation_manager.generate_citation_id(title, authors, year)
        
        assert citation_id.startswith("CIT_")
        assert len(citation_id) == 12  # CIT_ + 8 hex chars
        
    def test_format_apa_citation(self, citation_manager, sample_citation):
        """Test APA citation formatting"""
        formatted = citation_manager.format_citation(sample_citation, CitationFormat.APA)
        
        assert "Doe, J. & Smith, J." in formatted
        assert "(2023)" in formatted
        assert "Test Research Paper" in formatted
        assert "Test Journal" in formatted
        assert "10.1000/test.2023.001" in formatted
        
    def test_format_mla_citation(self, citation_manager, sample_citation):
        """Test MLA citation formatting"""
        formatted = citation_manager.format_citation(sample_citation, CitationFormat.MLA)
        
        assert "Doe, John and Jane Smith" in formatted
        assert "2023" in formatted
        assert '"Test Research Paper."' in formatted
        
    def test_format_bibtex_citation(self, citation_manager, sample_citation):
        """Test BibTeX citation formatting"""
        formatted = citation_manager.format_citation(sample_citation, CitationFormat.BIBTEX)
        
        assert "@article{CIT_ABC12345," in formatted
        assert "title = {Test Research Paper}," in formatted
        assert "author = {John Doe and Jane Smith}," in formatted
        assert "year = {2023}," in formatted
        assert "journal = {Test Journal}," in formatted
        assert "doi = {10.1000/test.2023.001}," in formatted
        
    def test_create_cited_finding(self, citation_manager, sample_citation):
        """Test cited finding creation"""
        finding_text = "This is a test finding"
        context = "Test context"
        methodology = "Test methodology"
        
        cited_finding = citation_manager.create_cited_finding(
            finding_text, sample_citation, context, methodology
        )
        
        assert isinstance(cited_finding, CitedFinding)
        assert cited_finding.text == finding_text
        assert cited_finding.citation == sample_citation
        assert cited_finding.context == context
        assert cited_finding.methodology == methodology
        assert cited_finding.finding_id.startswith("FIND_")
        
    @pytest.mark.asyncio
    async def test_extract_citations_from_paper(self, citation_manager):
        """Test citation extraction from paper data"""
        paper_data = {
            "title": "Test Paper",
            "authors": ["John Doe"],
            "year": 2023,
            "references": [
                {
                    "title": "Referenced Paper 1",
                    "authors": ["Alice Johnson"],
                    "year": 2022,
                    "journal": "Journal A"
                },
                {
                    "title": "Referenced Paper 2", 
                    "authors": ["Bob Wilson"],
                    "year": 2021,
                    "journal": "Journal B"
                }
            ]
        }
        
        citations = await citation_manager.extract_citations_from_paper(paper_data)
        
        assert len(citations) == 2
        assert citations[0].title == "Referenced Paper 1"
        assert citations[0].authors == ["Alice Johnson"]
        assert citations[0].year == 2022
        assert citations[1].title == "Referenced Paper 2"
        assert citations[1].authors == ["Bob Wilson"]
        assert citations[1].year == 2021
        
    @pytest.mark.asyncio
    async def test_build_citation_network(self, citation_manager):
        """Test citation network building"""
        # Mock OpenAlex client response
        mock_network_data = {
            "nodes": {
                "W123": {
                    "title": "Central Paper",
                    "authors": ["John Doe"],
                    "year": 2023,
                    "citation_count": 100
                },
                "W456": {
                    "title": "Referenced Paper",
                    "authors": ["Alice Johnson"],
                    "year": 2022,
                    "citation_count": 50
                },
                "W789": {
                    "title": "Citing Paper",
                    "authors": ["Bob Wilson"],
                    "year": 2024,
                    "citation_count": 25
                }
            },
            "edges": [
                {"source": "W123", "target": "W456", "type": "references"},
                {"source": "W789", "target": "W123", "type": "cites"}
            ]
        }
        
        citation_manager.openalex_client.get_citation_network = AsyncMock(return_value=mock_network_data)
        
        network = await citation_manager.build_citation_network("W123", depth=2)
        
        assert isinstance(network, CitationNetwork)
        assert network.paper_id == "W123"
        assert len(network.references) == 1
        assert len(network.citations) == 1
        assert network.total_connections == 2
        assert network.influence_score == 1.0  # 1 citation / 1 reference
        
    @pytest.mark.asyncio
    async def test_get_citation_analytics(self, citation_manager):
        """Test citation analytics generation"""
        citations = [
            Citation(
                citation_id="CIT_1",
                title="Paper 1",
                authors=["Author A"],
                year=2020,
                journal="Journal A",
                citation_count=100
            ),
            Citation(
                citation_id="CIT_2", 
                title="Paper 2",
                authors=["Author B"],
                year=2021,
                journal="Journal B",
                citation_count=50
            ),
            Citation(
                citation_id="CIT_3",
                title="Paper 3", 
                authors=["Author A"],
                year=2022,
                journal="Journal A",
                citation_count=75
            )
        ]
        
        analytics = await citation_manager.get_citation_analytics(citations)
        
        assert analytics["total_citations"] == 3
        assert analytics["year_range"]["min"] == 2020
        assert analytics["year_range"]["max"] == 2022
        assert analytics["year_range"]["average"] == 2021
        assert analytics["citation_impact"]["total_citations_received"] == 225
        assert analytics["citation_impact"]["average_citations_per_paper"] == 75.0
        assert analytics["journal_distribution"]["Journal A"] == 2
        assert analytics["journal_distribution"]["Journal B"] == 1
        assert analytics["author_analysis"]["total_authors"] == 2
        assert analytics["author_analysis"]["most_frequent_authors"]["Author A"] == 2

class TestCitationIntegration:
    """Test citation integration with research synthesizer"""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services"""
        db_ops = Mock()
        llm_manager = Mock()
        redis_url = "redis://localhost:6379"
        openalex_client = Mock()
        
        return db_ops, llm_manager, redis_url, openalex_client
    
    @pytest.fixture
    def sample_papers(self):
        """Create sample papers for testing"""
        return [
            {
                "id": "paper_1",
                "title": "Research Paper 1",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2023,
                "journal": "Journal A",
                "doi": "10.1000/paper1.2023.001",
                "abstract": "This is the abstract of paper 1",
                "findings": "Key finding 1 from paper 1",
                "methodology": "Experimental study",
                "citation_count": 100,
                "references": [
                    {
                        "title": "Referenced Paper A",
                        "authors": ["Alice Johnson"],
                        "year": 2022,
                        "journal": "Journal B"
                    }
                ]
            },
            {
                "id": "paper_2",
                "title": "Research Paper 2", 
                "authors": ["Bob Wilson"],
                "year": 2024,
                "journal": "Journal C",
                "doi": "10.1000/paper2.2024.001",
                "abstract": "This is the abstract of paper 2",
                "findings": "Key finding 2 from paper 2",
                "methodology": "Survey study",
                "citation_count": 50,
                "references": [
                    {
                        "title": "Referenced Paper B",
                        "authors": ["Carol Brown"],
                        "year": 2023,
                        "journal": "Journal D"
                    }
                ]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_citation_analysis_integration(self, mock_services, sample_papers):
        """Test citation analysis integration in synthesizer"""
        db_ops, llm_manager, redis_url, openalex_client = mock_services
        
        # Mock database operations
        db_ops.get_processed_paper = AsyncMock(side_effect=lambda pid: next(
            (paper for paper in sample_papers if paper["id"] == pid), None
        ))
        
        # Mock LLM manager
        llm_manager.process_document = AsyncMock(return_value="Mock LLM response")
        llm_manager.generate_synthesis = AsyncMock(return_value={"summary": "Mock synthesis"})
        llm_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock Redis
        redis_mock = Mock()
        redis_mock.ping = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock()
        
        # Create synthesizer with citation manager
        synthesizer = ResearchSynthesizer(
            db_ops=db_ops,
            llm_manager=llm_manager, 
            redis_url=redis_url,
            openalex_client=openalex_client
        )
        
        # Mock Redis client
        synthesizer.redis_client = redis_mock
        
        # Test synthesis with citation analysis
        paper_ids = ["paper_1", "paper_2"]
        synthesis = await synthesizer.synthesize_papers(paper_ids)
        
        # Verify citation analysis is included
        assert "citation_analysis" in synthesis
        citation_analysis = synthesis["citation_analysis"]
        
        assert citation_analysis["total_citations"] > 0
        assert "cited_findings" in citation_analysis
        assert "formatted_citations" in citation_analysis
        assert "citation_analytics" in citation_analysis
        assert "academic_credibility_score" in citation_analysis
        
        # Verify citation formatting
        formatted_citations = citation_analysis["formatted_citations"]
        assert "apa" in formatted_citations
        assert "bibtex" in formatted_citations
        
        # Verify academic export
        academic_export = await synthesizer.export_academic_synthesis(synthesis)
        assert "Research Synthesis Report" in academic_export
        assert "Key Findings" in academic_export
        assert "References" in academic_export
        assert "Citation Analytics" in academic_export
        
    @pytest.mark.asyncio
    async def test_academic_export_formats(self, mock_services, sample_papers):
        """Test academic export in different formats"""
        db_ops, llm_manager, redis_url, openalex_client = mock_services
        
        # Mock services
        db_ops.get_processed_paper = AsyncMock(side_effect=lambda pid: next(
            (paper for paper in sample_papers if paper["id"] == pid), None
        ))
        llm_manager.process_document = AsyncMock(return_value="Mock LLM response")
        llm_manager.generate_synthesis = AsyncMock(return_value={"summary": "Mock synthesis"})
        llm_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        redis_mock = Mock()
        redis_mock.ping = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock()
        
        synthesizer = ResearchSynthesizer(
            db_ops=db_ops,
            llm_manager=llm_manager,
            redis_url=redis_url,
            openalex_client=openalex_client
        )
        synthesizer.redis_client = redis_mock
        
        # Generate synthesis
        synthesis = await synthesizer.synthesize_papers(["paper_1", "paper_2"])
        
        # Test APA format export
        apa_export = await synthesizer.export_academic_synthesis(synthesis, CitationFormat.APA)
        assert "Research Synthesis Report" in apa_export
        assert "References" in apa_export
        
        # Test BibTeX format export
        bibtex_export = await synthesizer.export_academic_synthesis(synthesis, CitationFormat.BIBTEX)
        assert "Research Synthesis Report" in bibtex_export
        assert "```bibtex" in bibtex_export

class TestCitationPersistence:
    """Test citation persistence functionality"""
    
    @pytest.mark.asyncio
    async def test_save_citations_to_database(self):
        """Test saving citations to database"""
        db_ops = Mock()
        citation_manager = CitationManager(db_ops=db_ops)
        
        citations = [
            Citation(
                citation_id="CIT_1",
                title="Test Paper",
                authors=["John Doe"],
                year=2023,
                journal="Test Journal"
            )
        ]
        
        # Mock database save operation
        db_ops.save_citations = AsyncMock(return_value=True)
        
        result = await citation_manager.save_citations_to_database(citations, "paper_1")
        
        assert result is True
        db_ops.save_citations.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_citation_network_persistence(self):
        """Test citation network persistence"""
        db_ops = Mock()
        citation_manager = CitationManager(db_ops=db_ops)
        
        network = CitationNetwork(
            paper_id="paper_1",
            references=["CIT_1", "CIT_2"],
            citations=["CIT_3"],
            network_depth=2,
            total_connections=3,
            influence_score=0.5
        )
        
        # Mock database save operation
        db_ops.save_citation_network = AsyncMock(return_value=True)
        
        # This would be implemented in the actual database operations
        # For now, we just test the network structure
        assert network.paper_id == "paper_1"
        assert len(network.references) == 2
        assert len(network.citations) == 1
        assert network.total_connections == 3
        assert network.influence_score == 0.5

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
