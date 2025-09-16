import pytest
import numpy as np
from unittest.mock import Mock, patch
import asyncio
from src.services.search_service.search_engine import SearchEngine
from src.services.search_service.vector_search import VectorSearchEngine
from src.services.search_service.indexer import DocumentIndexer

@pytest.fixture
def db_ops():
    mock_db = Mock()
    mock_db.search_papers = Mock()
    mock_db.get_processed_paper = Mock()
    return mock_db

@pytest.fixture
def vector_search():
    return VectorSearchEngine()

@pytest.fixture
def search_engine(db_ops):
    return SearchEngine(db_ops)

@pytest.fixture
def indexer(db_ops, vector_search):
    return DocumentIndexer(db_ops, vector_search)

class TestSearchEngine:
    @pytest.mark.asyncio
    async def test_semantic_search(self, search_engine):
        query = "machine learning"
        await search_engine.initialize_vector_store()
        
        results = await search_engine.semantic_search(query)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_keyword_search(self, search_engine):
        query = "neural networks"
        search_engine.db.search_papers.return_value = [
            {"id": "test-1", "title": "Neural Networks Paper"}
        ]
        
        results = await search_engine.keyword_search(query)
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_combined_search(self, search_engine):
        query = "deep learning"
        with patch.object(search_engine, 'semantic_search') as mock_semantic:
            with patch.object(search_engine, 'keyword_search') as mock_keyword:
                mock_semantic.return_value = [{"paper_id": "test-1", "score": 0.9}]
                mock_keyword.return_value = [{"id": "test-2"}]
                
                results = await search_engine.combined_search(query)
                assert isinstance(results, list)
                assert len(results) > 0

class TestVectorSearch:
    @pytest.mark.asyncio
    async def test_add_document(self, vector_search):
        doc_id = "test-123"
        text = "Test document content for vector search"
        
        success = await vector_search.add_document(doc_id, text)
        assert success
        assert doc_id in [v for v in vector_search.doc_map.values()]

    @pytest.mark.asyncio
    async def test_search(self, vector_search):
        # Add test document
        await vector_search.add_document("test-1", "machine learning document")
        
        results = await vector_search.search("machine learning", k=1)
        assert isinstance(results, list)
        assert len(results) <= 1
        if results:
            assert "score" in results[0]

    @pytest.mark.asyncio
    async def test_batch_add_documents(self, vector_search):
        documents = [
            {"id": "test-1", "text": "first document"},
            {"id": "test-2", "text": "second document"}
        ]
        
        success = await vector_search.batch_add_documents(documents)
        assert success
        assert len(vector_search.doc_map) == 2

class TestDocumentIndexer:
    @pytest.mark.asyncio
    async def test_queue_document(self, indexer):
        doc_id = "test-123"
        await indexer.queue_document(doc_id)
        
        size = indexer.indexing_queue.qsize()
        assert size == 1

    @pytest.mark.asyncio
    async def test_process_queue(self, indexer):
        # Add document to queue
        doc_id = "test-123"
        await indexer.queue_document(doc_id)
        
        # Mock processed document
        indexer.db.get_processed_paper.return_value = {
            "id": doc_id,
            "content": "Test document content"
        }
        
        # Start processing
        indexer._running = True
        process_task = asyncio.create_task(indexer._process_queue())
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        # Stop processing
        indexer._running = False
        await process_task
        
        # Verify document was processed
        assert indexer.indexing_queue.empty()
        assert indexer.db.update_paper_status.called

    @pytest.mark.asyncio
    async def test_batch_indexing(self, indexer):
        doc_ids = ["test-1", "test-2", "test-3"]
        
        # Mock document retrieval
        indexer.db.get_processed_paper.return_value = {
            "content": "Test content"
        }
        
        results = await indexer.batch_index(doc_ids)
        
        assert isinstance(results, dict)
        assert len(results) == len(doc_ids)
        assert all(results.values())

    @pytest.mark.asyncio
    async def test_reindex_all(self, indexer):
        # Mock database search
        indexer.db.search_papers.return_value = [
            {"id": "test-1"},
            {"id": "test-2"}
        ]
        
        # Mock document retrieval
        indexer.db.get_processed_paper.return_value = {
            "content": "Test content"
        }
        
        await indexer.reindex_all()
        
        # Verify all documents were processed
        assert indexer.db.update_paper_status.call_count >= 2    
    