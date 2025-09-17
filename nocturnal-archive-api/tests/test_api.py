"""
Comprehensive API test suite
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from src.main import app
from src.config.settings import get_settings

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert "version" in data


class TestSearchEndpoint:
    """Test search endpoint"""
    
    def test_search_basic(self):
        """Test basic search functionality"""
        with patch('src.routes.search.PaperSearcher') as mock_searcher:
            mock_instance = AsyncMock()
            mock_instance.search_papers.return_value = []
            mock_searcher.return_value = mock_instance
            
            response = client.post(
                "/api/search",
                json={
                    "query": "test query",
                    "limit": 10,
                    "sources": ["openalex"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "papers" in data
            assert "count" in data
            assert "query_id" in data
            assert "trace_id" in data
    
    def test_search_with_enhancements(self):
        """Test search with performance enhancements"""
        with patch('src.routes.search.PaperSearcher') as mock_searcher, \
             patch('src.routes.search.performance_integration') as mock_perf:
            
            mock_instance = AsyncMock()
            mock_instance.search_papers.return_value = []
            mock_searcher.return_value = mock_instance
            
            mock_perf.enhance_paper_search.return_value = []
            mock_perf.extract_research_insights.return_value = {}
            
            response = client.post(
                "/api/search?enhance=true&extract_insights=true",
                json={
                    "query": "test query",
                    "limit": 10,
                    "sources": ["openalex"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "papers" in data
            assert "count" in data
    
    def test_search_validation(self):
        """Test search input validation"""
        response = client.post(
            "/api/search",
            json={
                "query": "",  # Empty query should fail
                "limit": 10,
                "sources": ["openalex"]
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_search_invalid_sources(self):
        """Test search with invalid sources"""
        response = client.post(
            "/api/search",
            json={
                "query": "test query",
                "limit": 10,
                "sources": ["invalid_source"]
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestFormatEndpoint:
    """Test format endpoint"""
    
    def test_format_bibtex(self):
        """Test BibTeX formatting"""
        with patch('src.routes.format.CitationFormatter') as mock_formatter:
            mock_instance = AsyncMock()
            mock_instance.format_papers.return_value = "@article{test2023,...}"
            mock_formatter.return_value = mock_instance
            
            response = client.post(
                "/api/format",
                json={
                    "paper_ids": ["W2981234567"],
                    "style": "bibtex"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "formatted" in data
            assert "format" in data
            assert "count" in data
            assert "trace_id" in data
    
    def test_format_multiple_styles(self):
        """Test multiple citation styles"""
        styles = ["bibtex", "apa", "mla", "chicago", "harvard"]
        
        with patch('src.routes.format.CitationFormatter') as mock_formatter:
            mock_instance = AsyncMock()
            mock_instance.format_papers.return_value = "formatted citation"
            mock_formatter.return_value = mock_instance
            
            for style in styles:
                response = client.post(
                    "/api/format",
                    json={
                        "paper_ids": ["W2981234567"],
                        "style": style
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["format"] == style
    
    def test_format_validation(self):
        """Test format input validation"""
        response = client.post(
            "/api/format",
            json={
                "paper_ids": [],  # Empty list should fail
                "style": "bibtex"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestSynthesizeEndpoint:
    """Test synthesis endpoint"""
    
    def test_synthesize_basic(self):
        """Test basic synthesis functionality"""
        with patch('src.routes.synthesize.Synthesizer') as mock_synthesizer:
            mock_instance = AsyncMock()
            mock_result = AsyncMock()
            mock_result.trace_id = "test-trace-id"
            mock_result.word_count = 300
            mock_result.summary = "Test synthesis"
            mock_result.key_findings = ["Finding 1", "Finding 2"]
            mock_result.citations_used = {"[1]": "W2981234567"}
            mock_instance.synthesize_papers.return_value = mock_result
            mock_synthesizer.return_value = mock_instance
            
            response = client.post(
                "/api/synthesize",
                json={
                    "paper_ids": ["W2981234567", "W2981234568"],
                    "max_words": 300,
                    "focus": "key_findings",
                    "style": "academic"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "key_findings" in data
            assert "citations_used" in data
            assert "word_count" in data
            assert "trace_id" in data
    
    def test_synthesize_with_enhancements(self):
        """Test synthesis with performance enhancements"""
        with patch('src.routes.synthesize.Synthesizer') as mock_synthesizer, \
             patch('src.routes.synthesize.performance_integration') as mock_perf:
            
            mock_instance = AsyncMock()
            mock_result = AsyncMock()
            mock_result.trace_id = "test-trace-id"
            mock_result.word_count = 300
            mock_result.summary = "Test synthesis"
            mock_result.key_findings = ["Finding 1", "Finding 2"]
            mock_result.citations_used = {"[1]": "W2981234567"}
            mock_result.metadata = {}
            mock_instance.synthesize_papers.return_value = mock_result
            mock_synthesizer.return_value = mock_instance
            
            mock_perf.enhance_synthesis.return_value = {"enhanced": True}
            mock_perf.extract_research_insights.return_value = {"insights": True}
            
            response = client.post(
                "/api/synthesize?enhance=true&extract_insights=true",
                json={
                    "paper_ids": ["W2981234567", "W2981234568"],
                    "max_words": 300,
                    "focus": "key_findings",
                    "style": "academic"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "metadata" in data
    
    def test_synthesize_validation(self):
        """Test synthesis input validation"""
        response = client.post(
            "/api/synthesize",
            json={
                "paper_ids": [],  # Empty list should fail
                "max_words": 300
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestAnalyticsEndpoint:
    """Test analytics endpoint"""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/api/analytics/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "response_times" in data
        assert "error_rates" in data
    
    def test_real_time_metrics(self):
        """Test real-time metrics"""
        response = client.get("/api/analytics/real-time")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "requests_per_minute" in data
    
    def test_performance_metrics(self):
        """Test performance metrics"""
        response = client.get("/api/analytics/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert "performance" in data
    
    def test_error_metrics(self):
        """Test error metrics"""
        response = client.get("/api/analytics/errors")
        assert response.status_code == 200
        
        data = response.json()
        assert "errors" in data


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow: search -> format -> synthesize"""
        
        # Mock all services
        with patch('src.routes.search.PaperSearcher') as mock_searcher, \
             patch('src.routes.format.CitationFormatter') as mock_formatter, \
             patch('src.routes.synthesize.Synthesizer') as mock_synthesizer:
            
            # Mock search
            mock_search_instance = AsyncMock()
            mock_search_instance.search_papers.return_value = []
            mock_searcher.return_value = mock_search_instance
            
            # Mock format
            mock_format_instance = AsyncMock()
            mock_format_instance.format_papers.return_value = "@article{test2023,...}"
            mock_formatter.return_value = mock_format_instance
            
            # Mock synthesis
            mock_synth_instance = AsyncMock()
            mock_result = AsyncMock()
            mock_result.trace_id = "test-trace-id"
            mock_result.word_count = 300
            mock_result.summary = "Test synthesis"
            mock_result.key_findings = ["Finding 1"]
            mock_result.citations_used = {"[1]": "W2981234567"}
            mock_synth_instance.synthesize_papers.return_value = mock_result
            mock_synthesizer.return_value = mock_synth_instance
            
            # Test search
            search_response = client.post(
                "/api/search",
                json={
                    "query": "test query",
                    "limit": 10,
                    "sources": ["openalex"]
                }
            )
            assert search_response.status_code == 200
            
            # Test format
            format_response = client.post(
                "/api/format",
                json={
                    "paper_ids": ["W2981234567"],
                    "style": "bibtex"
                }
            )
            assert format_response.status_code == 200
            
            # Test synthesis
            synth_response = client.post(
                "/api/synthesize",
                json={
                    "paper_ids": ["W2981234567"],
                    "max_words": 300
                }
            )
            assert synth_response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self):
        """Test invalid JSON handling"""
        response = client.post(
            "/api/search",
            data="invalid json"
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        response = client.post(
            "/api/search",
            json={}
        )
        assert response.status_code == 422
    
    def test_server_error_handling(self):
        """Test server error handling"""
        with patch('src.routes.search.PaperSearcher') as mock_searcher:
            mock_instance = AsyncMock()
            mock_instance.search_papers.side_effect = Exception("Test error")
            mock_searcher.return_value = mock_instance
            
            response = client.post(
                "/api/search",
                json={
                    "query": "test query",
                    "limit": 10,
                    "sources": ["openalex"]
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "message" in data
            assert "trace_id" in data


if __name__ == "__main__":
    pytest.main([__file__])
