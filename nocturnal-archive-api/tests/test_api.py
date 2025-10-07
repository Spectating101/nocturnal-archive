"""
Comprehensive API test suite
"""

import pytest
import asyncio
import hashlib
import os
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from src.main import app
from src.config.settings import get_settings
from src.services.telemetry_ingestor import reset_telemetry_ingestor_cache

client = TestClient(app)
client.headers.update({"X-API-Key": "na_test_api_key_123"})


@pytest.fixture
def telemetry_setup(tmp_path, monkeypatch):
    token = "telemetry-token-abc123456789"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    storage_dir = tmp_path / "telemetry"

    monkeypatch.setenv("NOCTURNAL_TELEMETRY_TOKEN_HASHES", digest)
    monkeypatch.setenv("NOCTURNAL_TELEMETRY_STORAGE", str(storage_dir))
    monkeypatch.delenv("NOCTURNAL_TELEMETRY_ACCEPT_ALL", raising=False)

    reset_telemetry_ingestor_cache()

    yield token, storage_dir

    reset_telemetry_ingestor_cache()


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
        advanced_result = {
            "summary": "Test synthesis",
            "word_count": 300,
            "key_findings": ["Finding 1", "Finding 2"],
            "citations_used": {"[1]": "W2981234567"},
            "metadata": {"confidence": 0.8},
            "routing_metadata": {
                "routing_decision": {
                    "model": "gpt-4.1-mini",
                    "complexity": "advanced",
                    "strategy": "advanced_synthesizer",
                },
                "usage": {"prompt_tokens": 120, "completion_tokens": 200},
            },
        }

        with patch("src.routes.synthesize.sophisticated_engine") as mock_engine:
            mock_engine.enhanced_synthesizer = True
            mock_engine.synthesize_advanced = AsyncMock(return_value=advanced_result)
            
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
        advanced_result = {
            "summary": "Test synthesis",
            "word_count": 280,
            "key_findings": ["Finding 1", "Finding 2"],
            "citations_used": {"[1]": "W2981234567"},
            "metadata": {},
            "routing_metadata": {
                "routing_decision": {
                    "model": "gpt-4.1-mini",
                    "complexity": "advanced",
                    "strategy": "advanced_synthesizer",
                },
                "usage": {"prompt_tokens": 100, "completion_tokens": 180},
            },
        }

        with patch("src.routes.synthesize.sophisticated_engine") as mock_engine, \
             patch('src.routes.synthesize.performance_integration') as mock_perf:

            mock_engine.enhanced_synthesizer = True
            mock_engine.synthesize_advanced = AsyncMock(return_value=advanced_result)

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

    def test_synthesize_strict_path(self):
        """Strict synthesis uses sophisticated engine"""
        strict_result = {
            "summary": "Strict synthesis output",
            "word_count": 320,
            "key_findings": ["Strict finding"],
            "citations_used": {"[1]": "W111"},
            "metadata": {"confidence": 0.9},
            "routing_metadata": {
                "routing_decision": {
                    "model": "gpt-4.1-mini",
                    "complexity": "heavy",
                    "strategy": "advanced_synthesizer_strict",
                },
                "usage": {"prompt_tokens": 200, "completion_tokens": 220},
            },
        }

        with patch("src.routes.synthesize.sophisticated_engine") as mock_engine:
            mock_engine.enhanced_synthesizer = True
            mock_engine.synthesize_strict = AsyncMock(return_value=strict_result)

            response = client.post(
                "/api/synthesize/strict",
                json={
                    "paper_ids": ["W111", "W222"],
                    "max_words": 320,
                    "focus": "key_findings",
                    "style": "academic",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model_used"] == "gpt-4.1-mini"
        assert payload["complexity"] == "heavy"

    def test_synthesize_advanced_recycled_resin(self):
        """Test advanced synthesis workflow for recycled resin research"""
        advanced_result = {
            "summary": (
                "Recycled resin additive manufacturing binder jetting workflows "
                "increase mechanical stability by re-polymerizing PET feedstock with "
                "uv-curable matrices while preserving recycled resin content."
            ),
            "word_count": 368,
            "key_findings": [
                "Binder jetting lines that preheat recycled resin granules deliver 18% higher tensile strength.",
                "Hybrid UV cure schedules cut porosity by 11% versus thermoset-only controls.",
                "Post-processing regimens with plasma activation preserve pigment dispersion in recycled feedstock."
            ],
            "citations_used": {
                "[1]": "https://openalex.org/W1234567890",
                "[2]": "https://openalex.org/W0987654321"
            },
            "metadata": {
                "confidence": 0.86,
                "domain_alignment": "advanced_polymers",
                "paper_sample_size": 12
            },
            "routing_metadata": {
                "routing_decision": {
                    "model": "gpt-4.1-mini",
                    "complexity": "advanced",
                    "strategy": "advanced_synthesizer"
                },
                "usage": {
                    "prompt_tokens": 812,
                    "completion_tokens": 446
                }
            }
        }

        with patch("src.routes.synthesize.sophisticated_engine") as mock_engine, \
             patch("src.routes.synthesize.performance_integration") as mock_perf:

            mock_engine.enhanced_synthesizer = True
            mock_engine.synthesize_advanced = AsyncMock(return_value=advanced_result)

            mock_perf.enhance_synthesis = AsyncMock(return_value={
                "enhanced_synthesis": {
                    "keywords": [
                        "recycled resin",
                        "binder jetting",
                        "uv curing"
                    ]
                },
                "routing_metadata": advanced_result["routing_metadata"],
                "synthesis_mode": "advanced"
            })
            mock_perf.extract_research_insights = AsyncMock(return_value={
                "top_keywords": [
                    {"word": "recycled resin", "frequency": 7},
                    {"word": "binder jetting", "frequency": 5}
                ],
                "unique_keywords": 14
            })

            response = client.post(
                "/api/synthesize",
                json={
                    "paper_ids": [
                        "https://openalex.org/W1234567890",
                        "https://openalex.org/W0987654321"
                    ],
                    "max_words": 450,
                    "focus": "key_findings",
                    "style": "academic",
                    "original_query": "recycled resin additive manufacturing binder jetting"
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert data["summary"].startswith("Recycled resin additive manufacturing binder jetting")
        assert "Binder jetting lines" in " ".join(data["key_findings"])
        assert data["citations_used"]["[1]"] == "https://openalex.org/W1234567890"
        assert data["model_used"] == "gpt-4.1-mini"
        assert data["complexity"] == "advanced"
        assert data["token_usage"] == advanced_result["routing_metadata"]["usage"]
        assert data["metadata"]["synthesis_mode"] == "advanced"
        assert data["metadata"]["routing_metadata"]["routing_decision"]["strategy"] == "advanced_synthesizer"
        assert data["metadata"]["insights"]["top_keywords"][0]["word"] == "recycled resin"
        assert data["relevance_score"] == pytest.approx(1.0, rel=1e-2)


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


class TestTelemetryEndpoint:
    """Telemetry ingestion contract"""

    def test_ingest_success(self, telemetry_setup, client):
        token, storage_dir = telemetry_setup
        payload = {
            "event": "cli_start",
            "session": "session-123",
            "client_version": "1.2.3",
        }

        response = client.post(
            "/api/telemetry/ingest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "accepted"

        expected_file = storage_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"

        for _ in range(20):
            if expected_file.exists() and expected_file.read_text(encoding="utf-8").strip():
                break
            time.sleep(0.01)

        assert expected_file.exists()
        contents = expected_file.read_text(encoding="utf-8").strip()
        assert contents
        lines = contents.splitlines()
        record = json.loads(lines[-1])
        assert record["event"] == payload["event"]
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert record["token_hash"].startswith(token_hash[:16])
        assert "meta" in record

    def test_ingest_missing_token(self, telemetry_setup, client):
        response = client.post(
            "/api/telemetry/ingest",
            json={"event": "missing_token"},
        )

        assert response.status_code == 401
        detail = response.json()
        assert detail["detail"]["error"] == "telemetry_auth"

    def test_ingest_forbidden_token(self, telemetry_setup, client):
        response = client.post(
            "/api/telemetry/ingest",
            json={"event": "forbidden_token"},
            headers={"Authorization": "Bearer unauthorized-token-xyz123"},
        )

        assert response.status_code == 403
        detail = response.json()
        assert detail["detail"]["error"] == "telemetry_auth"

    def test_summary_endpoint(self, telemetry_setup, client):
        token, _ = telemetry_setup
        client.post(
            "/api/telemetry/ingest",
            json={"event": "summary_test", "session": "sess-1"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = client.get(
            "/api/telemetry/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] >= 1
        assert "summary_test" in data["by_event"]
        assert data["unique_sessions"] >= 1

    def test_events_endpoint_limit(self, telemetry_setup, client):
        token, _ = telemetry_setup
        for idx in range(3):
            client.post(
                "/api/telemetry/ingest",
                json={"event": f"event_{idx}", "session": f"sess-{idx}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = client.get(
            "/api/telemetry/events?limit=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert len(payload["events"]) == 2
        assert payload["limit"] == 2

    def test_summary_requires_token(self, client):
        response = client.get("/api/telemetry/summary")
        assert response.status_code == 401

    def test_daily_endpoint(self, telemetry_setup, client):
        token, _ = telemetry_setup
        client.post(
            "/api/telemetry/ingest",
            json={"event": "daily_event", "session": "sess-daily"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = client.get(
            "/api/telemetry/daily?days=3",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["days"] == 3
        assert len(payload["series"]) == 3
        assert any(entry["total_events"] >= 1 for entry in payload["series"])

    def test_daily_requires_token(self, client):
        response = client.get("/api/telemetry/daily")
        assert response.status_code == 401


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow: search -> format -> synthesize"""
        
        # Mock all services
        with patch('src.routes.search.PaperSearcher') as mock_searcher, \
             patch('src.routes.format.CitationFormatter') as mock_formatter, \
             patch('src.routes.synthesize.sophisticated_engine') as mock_engine:
            
            # Mock search
            mock_search_instance = AsyncMock()
            mock_search_instance.search_papers.return_value = []
            mock_searcher.return_value = mock_search_instance
            
            # Mock format
            mock_format_instance = AsyncMock()
            mock_format_instance.format_papers.return_value = "@article{test2023,...}"
            mock_formatter.return_value = mock_format_instance
            
            # Mock sophisticated synthesis engine
            mock_engine.enhanced_synthesizer = True
            mock_engine.synthesize_advanced = AsyncMock(return_value={
                "summary": "Test synthesis",
                "word_count": 300,
                "key_findings": ["Finding 1"],
                "citations_used": {"[1]": "W2981234567"},
                "metadata": {},
                "routing_metadata": {
                    "routing_decision": {
                        "model": "gpt-4.1-mini",
                        "complexity": "advanced",
                        "strategy": "advanced_synthesizer",
                    },
                    "usage": {"prompt_tokens": 80, "completion_tokens": 160},
                },
            })
            
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
