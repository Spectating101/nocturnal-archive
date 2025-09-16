import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.paper_service.paper_manager import PaperManager
from src.services.paper_service.metadata import MetadataExtractor
from src.services.paper_service.openalex import OpenAlexManager

@pytest.fixture
def db_ops():
    # Mock database operations
    mock_db = Mock()
    mock_db.store_paper = Mock()
    mock_db.get_paper_status = Mock()
    mock_db.get_processed_paper = Mock()
    return mock_db

@pytest.fixture
def paper_manager(db_ops):
    return PaperManager(db_ops)

@pytest.fixture
def metadata_extractor():
    return MetadataExtractor()

@pytest.fixture
def openalex_manager():
    return OpenAlexManager(email="test@example.com")

class TestPaperManager:
    @pytest.mark.asyncio
    async def test_add_paper(self, paper_manager):
        content = b"Test paper content"
        filename = "test.pdf"
        content_type = "application/pdf"
        
        paper_id = await paper_manager.add_paper(content, filename, content_type)
        
        assert isinstance(paper_id, str)
        assert len(paper_id) > 0
        assert paper_manager.db.store_paper.called

    @pytest.mark.asyncio
    async def test_get_paper_status(self, paper_manager):
        paper_id = "test-123"
        paper_manager.db.get_paper_status.return_value = {"status": "processed"}
        
        status = await paper_manager.get_paper_status(paper_id)
        
        assert status is not None
        assert status["status"] == "processed"

    @pytest.mark.asyncio
    async def test_process_papers(self, paper_manager):
        # Add a paper to the queue
        content = b"Test content"
        await paper_manager.add_paper(content, "test.pdf", "application/pdf")
        
        # Process one item
        with patch.object(paper_manager, '_process_document') as mock_process:
            mock_process.return_value = {"id": "test-123", "content": "processed"}
            await paper_manager.process_papers()
            
            assert mock_process.called

class TestMetadataExtractor:
    @pytest.mark.asyncio
    async def test_extract_metadata(self, metadata_extractor):
        content = """
        Title: Test Paper
        Authors: John Doe, Jane Smith
        Abstract: This is a test paper abstract.
        References:
        1. Reference One
        2. Reference Two
        """
        
        metadata = await metadata_extractor.extract_metadata(content, "test.pdf")
        
        assert metadata["title"] == "Test Paper"
        assert len(metadata["authors"]) == 2
        assert metadata["abstract"] is not None
        assert len(metadata["references"]) == 2

    @pytest.mark.asyncio
    async def test_extract_publication_info(self, metadata_extractor):
        content = """
        Published in: Test Journal
        Year: 2023
        DOI: 10.1234/test.123
        """
        
        pub_info = await metadata_extractor._extract_publication_info(content)
        
        assert pub_info["journal"] is not None
        assert pub_info["year"] == 2023
        assert pub_info["doi"] is not None

class TestOpenAlexManager:
    @pytest.mark.asyncio
    async def test_search_papers(self, openalex_manager):
        query = "machine learning"
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value.json = Mock(
                return_value={
                    "results": [
                        {
                            "id": "test-123",
                            "title": "Test Paper",
                            "abstract": "Test abstract"
                        }
                    ]
                }
            )
            
            results = await openalex_manager.search_papers(query)
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert "title" in results[0]

    @pytest.mark.asyncio
    async def test_get_paper_details(self, openalex_manager):
        work_id = "test-123"
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value.json = Mock(
                return_value={
                    "id": work_id,
                    "title": "Test Paper",
                    "cited_by_count": 10
                }
            )
            
            details = await openalex_manager.get_paper_details(work_id)
            
            assert details["work"]["id"] == work_id
            assert "citation_count" in details

    @pytest.mark.asyncio
    async def test_get_citation_network(self, openalex_manager):
        work_id = "test-123"
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value.json = Mock(
                return_value={
                    "id": work_id,
                    "title": "Test Paper",
                    "referenced_works": [],
                    "cited_by": []
                }
            )
            
            network = await openalex_manager.get_citation_network(work_id, depth=1)
            
            assert "nodes" in network
            assert "edges" in network
            assert "stats" in network