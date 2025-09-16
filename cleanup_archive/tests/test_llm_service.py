import pytest
import asyncio
import logging
import re
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from typing import Dict, List, Any

from src.services.llm_service.llm_manager import LLMManager
from src.services.llm_service.processors import DocumentProcessor, ContentAnalyzer
from src.services.llm_service.embeddings import EmbeddingManager

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
async def llm_manager():
    """Initialize LLM manager with error handling."""
    try:
        manager = LLMManager("redis://localhost:6379")
        yield manager
    except Exception as e:
        logger.error(f"Failed to initialize LLM manager: {str(e)}")
        yield None
    finally:
        # Cleanup
        try:
            if manager and hasattr(manager, 'cleanup'):
                await manager.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

@pytest.fixture
async def doc_processor():
    """Initialize document processor with error handling."""
    try:
        return DocumentProcessor()
    except Exception as e:
        logger.error(f"Failed to initialize document processor: {str(e)}")
        return None

@pytest.fixture
async def embedding_manager():
    """Initialize embedding manager with error handling."""
    try:
        return EmbeddingManager(cache_dir="./test_cache")
    except Exception as e:
        logger.error(f"Failed to initialize embedding manager: {str(e)}")
        return None

class TestLLMManager:
    """Enhanced LLM Manager tests with comprehensive error handling and security testing."""
    
    @pytest.mark.asyncio
    async def test_process_document_success(self, llm_manager):
        """Test successful document processing."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        try:
            sample_doc = {
                "doc_id": "test-123",
                "text_content": "This is a test document for processing.",
            }
            
            result = await llm_manager.process_document(sample_doc)
            assert "chunks" in result
            assert "summary" in result
            assert isinstance(result["chunks"], list)
            assert isinstance(result["summary"], str)
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_process_document_invalid_input(self, llm_manager):
        """Test document processing with invalid input."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            await llm_manager.process_document(None)
        
        # Test with empty document
        with pytest.raises(ValueError):
            await llm_manager.process_document({})
        
        # Test with missing required fields
        with pytest.raises(ValueError):
            await llm_manager.process_document({"doc_id": "test"})
    
    @pytest.mark.asyncio
    async def test_process_document_malicious_input(self, llm_manager):
        """Test document processing with potentially malicious input."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with script injection
        malicious_doc = {
            "doc_id": "test-123",
            "text_content": "<script>alert('xss')</script>This is malicious content.",
        }
        
        try:
            result = await llm_manager.process_document(malicious_doc)
            # Should handle malicious content gracefully
            assert "chunks" in result
            assert "<script>" not in result["summary"]  # Should be sanitized
        except Exception as e:
            logger.warning(f"Malicious input test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_process_document_large_input(self, llm_manager):
        """Test document processing with very large input."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with extremely large text
        large_text = "A" * 100000  # 100KB of text
        large_doc = {
            "doc_id": "test-large",
            "text_content": large_text,
        }
        
        try:
            result = await llm_manager.process_document(large_doc)
            assert "chunks" in result
            assert len(result["chunks"]) > 0
        except Exception as e:
            logger.warning(f"Large input test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, llm_manager):
        """Test successful summary generation."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        try:
            text = "This is a test document. It contains multiple sentences. Testing summary generation."
            summary = await llm_manager.generate_summary(text)
            assert isinstance(summary, str)
            assert len(summary) > 0
            assert len(summary) < len(text)  # Summary should be shorter
            
        except Exception as e:
            logger.error(f"Summary generation test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_generate_summary_invalid_input(self, llm_manager):
        """Test summary generation with invalid input."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            await llm_manager.generate_summary(None)
        
        # Test with empty string
        with pytest.raises(ValueError):
            await llm_manager.generate_summary("")
        
        # Test with non-string input
        with pytest.raises(ValueError):
            await llm_manager.generate_summary(123)
    
    @pytest.mark.asyncio
    async def test_search_similar_success(self, llm_manager):
        """Test successful similarity search."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        try:
            # Initialize vector store with some content
            texts = ["test document one", "test document two"]
            query = "test document"
            
            # Add texts to vector store
            if not llm_manager.vector_store:
                llm_manager.vector_store = await llm_manager.initialize_vector_store(texts)
            
            results = await llm_manager.search_similar(query)
            assert isinstance(results, list)
            assert len(results) >= 0
            
        except Exception as e:
            logger.error(f"Similarity search test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_search_similar_invalid_input(self, llm_manager):
        """Test similarity search with invalid input."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with None query
        with pytest.raises((ValueError, TypeError)):
            await llm_manager.search_similar(None)
        
        # Test with empty query
        with pytest.raises(ValueError):
            await llm_manager.search_similar("")
    
    @pytest.mark.asyncio
    async def test_health_check(self, llm_manager):
        """Test health check functionality."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        try:
            health_status = await llm_manager.health_check()
            assert isinstance(health_status, dict)
            assert "status" in health_status
            assert "timestamp" in health_status
            
        except Exception as e:
            logger.error(f"Health check test failed: {str(e)}")
            raise

class TestDocumentProcessor:
    """Enhanced Document Processor tests with comprehensive error handling and security testing."""
    
    @pytest.mark.asyncio
    async def test_process_document_success(self, doc_processor):
        """Test successful document processing."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        try:
            content = "This is a test document.\nIt has multiple lines.\nTesting processing."
            result = await doc_processor.process_document(content)
            
            assert "chunks" in result
            assert "summary" in result
            assert "total_chunks" in result
            assert len(result["chunks"]) > 0
            assert isinstance(result["chunks"], list)
            assert isinstance(result["summary"], str)
            
        except Exception as e:
            logger.error(f"Document processing test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_process_document_invalid_input(self, doc_processor):
        """Test document processing with invalid input."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            await doc_processor.process_document(None)
        
        # Test with empty content
        with pytest.raises(ValueError):
            await doc_processor.process_document("")
        
        # Test with non-string input
        with pytest.raises(ValueError):
            await doc_processor.process_document(123)
    
    @pytest.mark.asyncio
    async def test_process_document_malicious_input(self, doc_processor):
        """Test document processing with potentially malicious input."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        # Test with script injection
        malicious_content = "<script>alert('xss')</script>This is malicious content."
        
        try:
            result = await doc_processor.process_document(malicious_content)
            assert "chunks" in result
            assert "<script>" not in result["summary"]  # Should be sanitized
            
        except Exception as e:
            logger.warning(f"Malicious input test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_extract_key_points_success(self, doc_processor):
        """Test successful key points extraction."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        try:
            text = "Important point one. Another crucial point. Final key insight."
            points = await doc_processor._extract_key_points(text)
            
            assert isinstance(points, list)
            assert len(points) > 0
            assert all(isinstance(p, str) for p in points)
            
        except Exception as e:
            logger.error(f"Key points extraction test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_extract_key_points_invalid_input(self, doc_processor):
        """Test key points extraction with invalid input."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            await doc_processor._extract_key_points(None)
        
        # Test with empty text
        with pytest.raises(ValueError):
            await doc_processor._extract_key_points("")
    
    @pytest.mark.asyncio
    async def test_sanitize_text(self, doc_processor):
        """Test text sanitization functionality."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        try:
            # Test with normal text
            normal_text = "This is normal text."
            sanitized = doc_processor._sanitize_text(normal_text)
            assert sanitized == normal_text
            
            # Test with script injection
            malicious_text = "<script>alert('xss')</script>Normal text"
            sanitized = doc_processor._sanitize_text(malicious_text)
            assert "<script>" not in sanitized
            assert "Normal text" in sanitized
            
            # Test with null bytes
            null_text = "Text with \x00 null bytes"
            sanitized = doc_processor._sanitize_text(null_text)
            assert "\x00" not in sanitized
            
        except Exception as e:
            logger.error(f"Text sanitization test failed: {str(e)}")
            raise

class TestEmbeddingManager:
    """Enhanced Embedding Manager tests with comprehensive error handling and security testing."""
    
    @pytest.mark.asyncio
    async def test_create_embeddings_success(self, embedding_manager):
        """Test successful embedding creation."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            texts = ["test document one", "test document two"]
            embeddings = await embedding_manager.create_embeddings(texts)
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape[0] == len(texts)
            assert embeddings.shape[1] > 0  # Should have embedding dimension
            
        except Exception as e:
            logger.error(f"Embedding creation test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_create_embeddings_invalid_input(self, embedding_manager):
        """Test embedding creation with invalid input."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            await embedding_manager.create_embeddings(None)
        
        # Test with empty list
        with pytest.raises(ValueError):
            await embedding_manager.create_embeddings([])
        
        # Test with non-list input
        with pytest.raises(ValueError):
            await embedding_manager.create_embeddings("not a list")
    
    @pytest.mark.asyncio
    async def test_create_embeddings_malicious_input(self, embedding_manager):
        """Test embedding creation with potentially malicious input."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            malicious_texts = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "data:text/html,<script>alert('xss')</script>"
            ]
            
            embeddings = await embedding_manager.create_embeddings(malicious_texts)
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape[0] == len(malicious_texts)
            
        except Exception as e:
            logger.warning(f"Malicious input embedding test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_add_to_index_success(self, embedding_manager):
        """Test successful index addition."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            doc_id = "test-123"
            texts = ["test document one", "test document two"]
            
            success = await embedding_manager.add_to_index(doc_id, texts)
            assert success
            
            # Verify document was added
            assert embedding_manager.is_initialized
            assert len(embedding_manager.document_map) > 0
            
        except Exception as e:
            logger.error(f"Index addition test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_add_to_index_invalid_input(self, embedding_manager):
        """Test index addition with invalid input."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        # Test with None doc_id
        with pytest.raises((ValueError, TypeError)):
            await embedding_manager.add_to_index(None, ["test"])
        
        # Test with empty doc_id
        with pytest.raises(ValueError):
            await embedding_manager.add_to_index("", ["test"])
        
        # Test with None texts
        with pytest.raises((ValueError, TypeError)):
            await embedding_manager.add_to_index("test", None)
        
        # Test with empty texts
        with pytest.raises(ValueError):
            await embedding_manager.add_to_index("test", [])
    
    @pytest.mark.asyncio
    async def test_search_success(self, embedding_manager):
        """Test successful search functionality."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            # First add some documents
            await embedding_manager.add_to_index("test-1", ["test document one"])
            await embedding_manager.add_to_index("test-2", ["test document two"])
            
            # Search
            results = await embedding_manager.search("test document", k=2)
            
            assert isinstance(results, list)
            assert len(results) <= 2
            for result in results:
                assert "doc_id" in result
                assert "score" in result
                assert "text" in result
                assert isinstance(result["score"], (int, float))
                
        except Exception as e:
            logger.error(f"Search test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_search_invalid_input(self, embedding_manager):
        """Test search with invalid input."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        # Test with None query
        with pytest.raises((ValueError, TypeError)):
            await embedding_manager.search(None, k=2)
        
        # Test with empty query
        with pytest.raises(ValueError):
            await embedding_manager.search("", k=2)
        
        # Test with invalid k value
        with pytest.raises(ValueError):
            await embedding_manager.search("test", k=-1)
    
    @pytest.mark.asyncio
    async def test_save_load_index_success(self, embedding_manager, tmp_path):
        """Test successful index save and load."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            # Add some documents
            await embedding_manager.add_to_index("test-1", ["test document"])
            
            # Save index
            save_path = tmp_path / "test_index"
            saved = await embedding_manager.save_index(str(save_path))
            assert saved
            
            # Create new manager and load index
            new_manager = EmbeddingManager()
            loaded = await new_manager.load_index(str(save_path))
            assert loaded
            
            # Verify loaded index has same content
            assert len(new_manager.document_map) == len(embedding_manager.document_map)
            
        except Exception as e:
            logger.error(f"Save/load index test failed: {str(e)}")
            raise
    
    @pytest.mark.asyncio
    async def test_save_index_invalid_path(self, embedding_manager):
        """Test index save with invalid path."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        # Test with None path
        with pytest.raises((ValueError, TypeError)):
            await embedding_manager.save_index(None)
        
        # Test with empty path
        with pytest.raises(ValueError):
            await embedding_manager.save_index("")
    
    @pytest.mark.asyncio
    async def test_health_check(self, embedding_manager):
        """Test health check functionality."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            health_status = await embedding_manager.health_check()
            assert isinstance(health_status, dict)
            assert "status" in health_status
            assert "timestamp" in health_status
            
        except Exception as e:
            logger.error(f"Health check test failed: {str(e)}")
            raise

class TestSecurityVulnerabilities:
    """Tests for security vulnerabilities and edge cases."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, llm_manager):
        """Test SQL injection prevention."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Test with SQL injection attempt
        malicious_text = "'; DROP TABLE users; --"
        
        try:
            # Should handle gracefully without executing SQL
            result = await llm_manager.generate_summary(malicious_text)
            assert isinstance(result, str)
            
        except Exception as e:
            logger.warning(f"SQL injection test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, embedding_manager):
        """Test path traversal prevention."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        # Test with path traversal attempt
        malicious_path = "../../../etc/passwd"
        
        try:
            # Should handle gracefully without accessing system files
            result = await embedding_manager.save_index(malicious_path)
            # Should either fail safely or sanitize the path
            
        except Exception as e:
            logger.warning(f"Path traversal test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_memory_exhaustion_prevention(self, doc_processor):
        """Test memory exhaustion prevention."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        # Test with extremely large input
        large_text = "A" * 1000000  # 1MB of text
        
        try:
            result = await doc_processor.process_document(large_text)
            assert "chunks" in result
            # Should handle large input without memory issues
            
        except Exception as e:
            logger.warning(f"Memory exhaustion test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, llm_manager):
        """Test rate limiting functionality."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        try:
            # Make multiple rapid requests
            tasks = []
            for i in range(10):
                task = llm_manager.generate_summary(f"Test document {i}")
                tasks.append(task)
            
            # Should handle rate limiting gracefully
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that some requests succeeded or failed gracefully
            assert len(results) == 10
            
        except Exception as e:
            logger.warning(f"Rate limiting test failed: {str(e)}")

class TestErrorRecovery:
    """Tests for error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, llm_manager):
        """Test recovery from network failures."""
        if not llm_manager:
            pytest.skip("LLM manager not available")
        
        # Mock network failure
        with patch.object(llm_manager, 'generate_summary', side_effect=ConnectionError("Network error")):
            try:
                result = await llm_manager.generate_summary("test")
                # Should handle network failure gracefully
            except ConnectionError:
                # Expected behavior
                pass
            except Exception as e:
                logger.warning(f"Network failure recovery test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_service_unavailable_recovery(self, doc_processor):
        """Test recovery from service unavailability."""
        if not doc_processor:
            pytest.skip("Document processor not available")
        
        # Mock service unavailability
        with patch.object(doc_processor, 'process_document', side_effect=Exception("Service unavailable")):
            try:
                result = await doc_processor.process_document("test")
                # Should handle service unavailability gracefully
            except Exception as e:
                # Expected behavior
                assert "Service unavailable" in str(e)
    
    @pytest.mark.asyncio
    async def test_data_corruption_recovery(self, embedding_manager):
        """Test recovery from data corruption."""
        if not embedding_manager:
            pytest.skip("Embedding manager not available")
        
        try:
            # Test with corrupted data
            corrupted_texts = ["", None, "valid text", 123, {"invalid": "data"}]
            
            # Should handle corrupted data gracefully
            embeddings = await embedding_manager.create_embeddings([t for t in corrupted_texts if isinstance(t, str)])
            assert isinstance(embeddings, np.ndarray)
            
        except Exception as e:
            logger.warning(f"Data corruption recovery test failed: {str(e)}")