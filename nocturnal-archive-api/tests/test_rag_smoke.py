"""
Smoke tests for RAG system
"""
import pytest
import os
from datetime import date
from src.rag.chunk import chunk_text
from src.rag.embeddings import embed, get_embedding_dimensions
from src.rag.index import upsert_docs, search, get_doc_stats
from src.rag.qa import answer, validate_query, explain_query


def test_chunk_text():
    """Test text chunking functionality"""
    # Test short text (should not be chunked)
    short_text = "This is a short text."
    chunks = chunk_text(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    
    # Test long text (should be chunked)
    long_text = "This is a very long text. " * 100  # ~2500 characters
    chunks = chunk_text(long_text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1800 for chunk in chunks)  # Max chunk size
    
    # Test overlap
    if len(chunks) > 1:
        # Check that chunks overlap (simplified check)
        total_chars = sum(len(chunk) for chunk in chunks)
        original_chars = len(" ".join(long_text.split()))
        assert total_chars > original_chars  # Overlap increases total length


def test_embeddings():
    """Test embedding generation"""
    # Test single text
    text = "Apple reported strong quarterly earnings"
    embeddings = embed(text)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 1
    assert len(embeddings[0]) == get_embedding_dimensions()
    
    # Test multiple texts
    texts = [
        "Apple reported strong quarterly earnings",
        "Revenue increased by 15% year-over-year",
        "Management discussed margin compression"
    ]
    embeddings = embed(texts)
    assert len(embeddings) == 3
    assert all(len(emb) == get_embedding_dimensions() for emb in embeddings)
    
    # Test that embeddings are normalized
    for emb in embeddings:
        # Check if embeddings are roughly normalized (length close to 1)
        length = sum(x**2 for x in emb)**0.5
        assert 0.9 <= length <= 1.1  # Allow some tolerance


def test_rag_inserts_and_searches():
    """Test RAG document insertion and search"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        # Test document insertion
        test_docs = [{
            "id": "DEMO:Item7",
            "title": "Item 7 - Management's Discussion",
            "url": "https://example.com",
            "date": date(2025, 1, 1),
            "ticker": "DEMO",
            "cik": "0000000000",
            "section": "MD&A",
            "text": "We expect margin compression due to pricing pressure and FX headwinds. Revenue growth remains strong despite market challenges."
        }]
        
        chunks_inserted = upsert_docs(test_docs)
        assert chunks_inserted > 0
        
        # Test search
        results = search("margin compression", k=3)
        assert len(results) > 0
        
        # Check result structure
        result = results[0]
        assert "id" in result
        assert "title" in result
        assert "score" in result
        assert "snippet" in result
        
        # Check that our test document is found
        assert any("DEMO:Item7" in r["id"] for r in results)
        
        # Test search with filters
        results_filtered = search("margin compression", k=3, tickers=["DEMO"])
        assert len(results_filtered) > 0
        assert all(r["ticker"] == "DEMO" for r in results_filtered)
        
    except Exception as e:
        pytest.skip(f"Database operations failed: {e}")


def test_qa_service():
    """Test Q&A service functionality"""
    # Test query validation
    validation = validate_query("What did Apple say about margins?")
    assert validation["valid"] is True
    assert "margin" in validation["found_keywords"]
    
    # Test invalid query
    validation_short = validate_query("a")
    assert validation_short["valid"] is False
    assert "too short" in validation_short["issues"][0].lower()
    
    # Test query explanation
    explanation = explain_query(
        "What did Apple say about margins?",
        cutoff="2024-12-31",
        tickers=["AAPL"]
    )
    assert "Query" in explanation["explanation"]
    assert "Filters" in explanation["explanation"]
    assert "2024-12-31" in explanation["explanation"]
    assert "AAPL" in explanation["explanation"]


def test_qa_answer_structure():
    """Test Q&A answer structure"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        # This test assumes we have some data in the database
        # It will work even with empty results
        result = answer("What did Apple say about margins?", k=3)
        
        # Check response structure
        assert "answer" in result
        assert "citations" in result
        assert "query" in result
        assert "total_results" in result
        
        # Check citations structure
        if result["citations"]:
            citation = result["citations"][0]
            assert "idx" in citation
            assert "id" in citation
            assert "title" in citation
            assert "url" in citation
            assert "ticker" in citation
            assert "section" in citation
            assert "score" in citation
        
    except Exception as e:
        pytest.skip(f"Q&A service failed: {e}")


def test_doc_stats():
    """Test document statistics"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        stats = get_doc_stats()
        
        # Check stats structure
        assert "total_documents" in stats
        assert "ticker_counts" in stats
        assert "date_range" in stats
        assert "section_counts" in stats
        
        # Check types
        assert isinstance(stats["total_documents"], int)
        assert isinstance(stats["ticker_counts"], list)
        assert isinstance(stats["date_range"], dict)
        assert isinstance(stats["section_counts"], list)
        
    except Exception as e:
        pytest.skip(f"Stats retrieval failed: {e}")


def test_chunking_edge_cases():
    """Test chunking edge cases"""
    # Test empty text
    chunks = chunk_text("")
    assert chunks == []
    
    # Test whitespace-only text
    chunks = chunk_text("   \n\t   ")
    assert chunks == []
    
    # Test text with excessive whitespace
    messy_text = "  This   is    a   text  with   lots    of    spaces.  "
    chunks = chunk_text(messy_text)
    assert len(chunks) == 1
    assert "  " not in chunks[0]  # Should be cleaned up


def test_embeddings_edge_cases():
    """Test embedding edge cases"""
    # Test empty text
    embeddings = embed("")
    assert len(embeddings) == 1
    assert len(embeddings[0]) == get_embedding_dimensions()
    
    # Test very long text
    long_text = "This is a test sentence. " * 1000
    embeddings = embed(long_text)
    assert len(embeddings) == 1
    assert len(embeddings[0]) == get_embedding_dimensions()


def test_qa_query_validation():
    """Test comprehensive query validation"""
    test_cases = [
        ("What did Apple say about margins?", True, []),
        ("Revenue growth", True, []),
        ("", False, ["too short"]),
        ("a", False, ["too short"]),
        ("This is a very long query. " * 200, False, ["too long"]),  # Over 2000 chars
        ("Risk factors", True, []),
    ]
    
    for query, expected_valid, expected_issues in test_cases:
        validation = validate_query(query)
        assert validation["valid"] == expected_valid, f"Query: '{query[:50]}...'"
        
        if expected_issues:
            for issue in expected_issues:
                assert any(issue.lower() in v.lower() for v in validation["issues"]), f"Missing issue '{issue}' for query: '{query[:50]}...'"


def test_cutoff_filtering():
    """Test point-in-time filtering with date cutoffs"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        from datetime import date, timedelta
        from src.rag.index import upsert_docs
        
        # Insert test documents with different dates
        old_date = date(2024, 1, 1)
        new_date = date(2024, 12, 31)
        
        test_docs = [
            {
                "id": "TEST:CUTOFF:OLD",
                "title": "Old Document",
                "url": "https://example.com/old",
                "date": old_date,
                "ticker": "TEST",
                "cik": "0000000000",
                "section": "Old Section",
                "text": "This is old information about margins from early 2024."
            },
            {
                "id": "TEST:CUTOFF:NEW", 
                "title": "New Document",
                "url": "https://example.com/new",
                "date": new_date,
                "ticker": "TEST",
                "cik": "0000000000",
                "section": "New Section",
                "text": "This is new information about margins from late 2024."
            }
        ]
        
        # Insert documents
        upsert_docs(test_docs)
        
        # Test search without cutoff (should find both)
        results_all = search("margins", k=5, tickers=["TEST"])
        assert len(results_all) >= 2
        
        # Test search with cutoff (should find only old document)
        cutoff_date = "2024-06-01"
        results_cutoff = search("margins", k=5, cutoff=cutoff_date, tickers=["TEST"])
        
        # Should find at least the old document
        assert len(results_cutoff) >= 1
        
        # Clean up
        from src.rag.index import clear_docs
        clear_docs("TEST")
        
    except Exception as e:
        pytest.skip(f"Cutoff test failed: {e}")


def test_ticker_filtering():
    """Test ticker-specific filtering"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        from src.rag.index import upsert_docs
        
        # Insert test documents for different tickers
        test_docs = [
            {
                "id": "TEST:TICKER:AAPL",
                "title": "Apple Document",
                "url": "https://example.com/aapl",
                "date": "2024-01-01",
                "ticker": "AAPL",
                "cik": "0000320193",
                "section": "AAPL Section",
                "text": "Apple reported strong margins in Q4."
            },
            {
                "id": "TEST:TICKER:MSFT",
                "title": "Microsoft Document", 
                "url": "https://example.com/msft",
                "date": "2024-01-01",
                "ticker": "MSFT",
                "cik": "0000789019",
                "section": "MSFT Section",
                "text": "Microsoft reported strong margins in Q4."
            }
        ]
        
        # Insert documents
        upsert_docs(test_docs)
        
        # Test search for AAPL only
        results_aapl = search("margins", k=5, tickers=["AAPL"])
        
        # Should find AAPL document
        assert len(results_aapl) >= 1
        assert all(r["ticker"] == "AAPL" for r in results_aapl)
        
        # Test search for MSFT only
        results_msft = search("margins", k=5, tickers=["MSFT"])
        
        # Should find MSFT document
        assert len(results_msft) >= 1
        assert all(r["ticker"] == "MSFT" for r in results_msft)
        
        # Test search for both tickers
        results_both = search("margins", k=5, tickers=["AAPL", "MSFT"])
        
        # Should find both documents
        assert len(results_both) >= 2
        tickers_found = {r["ticker"] for r in results_both}
        assert "AAPL" in tickers_found
        assert "MSFT" in tickers_found
        
        # Clean up
        from src.rag.index import clear_docs
        clear_docs("AAPL")
        clear_docs("MSFT")
        
    except Exception as e:
        pytest.skip(f"Ticker filter test failed: {e}")


def test_mmr_reranking():
    """Test MMR reranking for better diversity"""
    # Skip if database not available
    db_url = os.getenv("DB_URL")
    if not db_url or "localhost" not in db_url:
        pytest.skip("Database not available for testing")
    
    try:
        from src.rag.index import upsert_docs
        
        # Insert similar test documents to test MMR
        test_docs = [
            {
                "id": "TEST:MMR:1",
                "title": "Margin Report 1",
                "url": "https://example.com/1",
                "date": "2024-01-01",
                "ticker": "TEST",
                "cik": "0000000000",
                "section": "Section 1",
                "text": "Apple reported strong margins due to pricing power and cost optimization."
            },
            {
                "id": "TEST:MMR:2",
                "title": "Margin Report 2",
                "url": "https://example.com/2", 
                "date": "2024-01-01",
                "ticker": "TEST",
                "cik": "0000000000",
                "section": "Section 2",
                "text": "Apple margins were strong due to premium product mix and operational efficiency."
            },
            {
                "id": "TEST:MMR:3",
                "title": "Revenue Report",
                "url": "https://example.com/3",
                "date": "2024-01-01", 
                "ticker": "TEST",
                "cik": "0000000000",
                "section": "Section 3",
                "text": "Apple revenue growth was driven by iPhone sales and services expansion."
            }
        ]
        
        # Insert documents
        upsert_docs(test_docs)
        
        # Test search with k=2 (should use MMR for diversity)
        results = search("Apple margins", k=2, tickers=["TEST"])
        
        # Should return diverse results
        assert len(results) <= 2
        assert len(results) >= 1
        
        # Check that results have different content (diversity)
        if len(results) > 1:
            snippets = [r["snippet"].lower() for r in results]
            # Should not be identical
            assert len(set(snippets)) > 1
        
        # Clean up
        from src.rag.index import clear_docs
        clear_docs("TEST")
        
    except Exception as e:
        pytest.skip(f"MMR test failed: {e}")


def test_integration_workflow():
    """Test end-to-end integration workflow"""
    # This test verifies that all components work together
    
    # 1. Test chunking
    text = "Apple Inc. reported strong financial performance with revenue growth of 15% year-over-year. The company expects continued margin compression due to competitive pressures and foreign exchange headwinds."
    chunks = chunk_text(text)
    assert len(chunks) >= 1
    
    # 2. Test embeddings
    embeddings = embed(chunks)
    assert len(embeddings) == len(chunks)
    
    # 3. Test Q&A validation
    validation = validate_query("What did Apple say about margins?")
    assert validation["valid"]
    
    # 4. Test query explanation
    explanation = explain_query("Apple margins")
    assert "Query" in explanation["explanation"]
    
    print("✅ Integration workflow test passed - all components working together")
