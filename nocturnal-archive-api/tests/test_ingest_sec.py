"""
Tests for SEC filings ingestion
"""
import pytest
import pandas as pd
from pathlib import Path
from src.ingest.sec.fetch import fetch_filings, list_filings, get_filing_content
from src.ingest.sec.sections import extract_key_sections, summarize_sections
from src.ingest.sec.xbrl import check_arelle_available, summarize_facts
from src.jobs.filings_etl import run_filings_etl, get_etl_status, create_searchable_documents


def test_fetch_filings_minimal():
    """Test fetching a minimal set of filings"""
    # Test with a well-known ticker
    files = fetch_filings("AAPL", limit=1)
    
    # Should return a list (may be empty if no filings found)
    assert isinstance(files, list)
    
    # If files are returned, they should be valid paths
    for file_path in files:
        assert Path(file_path).exists()
        assert Path(file_path).suffix.lower() in {".htm", ".html", ".txt", ".xml"}


def test_list_filings():
    """Test listing available filings"""
    filings = list_filings("AAPL")
    
    assert isinstance(filings, list)
    
    # If filings exist, they should have the expected structure
    if filings:
        filing = filings[0]
        assert "ticker" in filing
        assert "form_type" in filing
        assert "filing_date" in filing
        assert "file_path" in filing
        assert "size" in filing
        
        assert filing["ticker"] == "AAPL"
        assert filing["form_type"] in {"10-K", "10-Q", "8-K"}
        assert Path(filing["file_path"]).exists()


def test_get_filing_content():
    """Test reading filing content"""
    # First get a filing if available
    filings = list_filings("AAPL")
    
    if filings:
        filing_path = filings[0]["file_path"]
        content = get_filing_content(filing_path)
        
        assert isinstance(content, str)
        assert len(content) > 0


def test_extract_sections():
    """Test section extraction from HTML"""
    # Create a mock HTML with common sections
    mock_html = """
    <html>
    <body>
    <h1>Item 1A - Risk Factors</h1>
    <p>We face various risks including market volatility, regulatory changes, and competitive pressures.</p>
    
    <h1>Item 7 - Management's Discussion and Analysis</h1>
    <p>Our financial performance has been strong with revenue growth of 15% year-over-year.</p>
    
    <h1>Item 8 - Financial Statements</h1>
    <p>The consolidated financial statements show total assets of $500 billion.</p>
    </body>
    </html>
    """
    
    sections = extract_key_sections(mock_html)
    
    assert isinstance(sections, dict)
    assert len(sections) > 0
    
    # Should find at least one of the sections
    section_titles = list(sections.keys())
    assert any("risk" in title.lower() or "item 1a" in title.lower() for title in section_titles)


def test_summarize_sections():
    """Test section summarization"""
    mock_sections = {
        "Item 1A - Risk Factors": "We face various risks including market volatility.",
        "Item 7 - Management's Discussion": "Our financial performance has been strong."
    }
    
    summary = summarize_sections(mock_sections)
    
    assert isinstance(summary, dict)
    assert "total_sections" in summary
    assert "total_characters" in summary
    assert "largest_sections" in summary
    
    assert summary["total_sections"] == 2
    assert summary["total_characters"] > 0


def test_run_filings_etl():
    """Test the complete ETL pipeline"""
    results = run_filings_etl("AAPL", limit=1, extract_xbrl=False)
    
    assert isinstance(results, dict)
    assert "ticker" in results
    assert "start_time" in results
    assert "filings_processed" in results
    assert "sections_extracted" in results
    assert "errors" in results
    
    assert results["ticker"] == "AAPL"
    assert isinstance(results["filings_processed"], int)
    assert isinstance(results["sections_extracted"], int)
    assert isinstance(results["errors"], list)


def test_get_etl_status():
    """Test ETL status checking"""
    status = get_etl_status("AAPL")
    
    assert isinstance(status, dict)
    assert "ticker" in status
    assert "has_sections" in status
    assert "has_facts" in status
    assert "sections_count" in status
    assert "facts_count" in status
    
    assert status["ticker"] == "AAPL"
    assert isinstance(status["has_sections"], bool)
    assert isinstance(status["has_facts"], bool)
    assert isinstance(status["sections_count"], int)
    assert isinstance(status["facts_count"], int)


def test_create_searchable_documents():
    """Test creating searchable documents"""
    documents = create_searchable_documents("AAPL")
    
    assert isinstance(documents, list)
    
    # If documents exist, they should have the expected structure
    if documents:
        doc = documents[0]
        assert "id" in doc
        assert "title" in doc
        assert "text" in doc
        assert "ticker" in doc
        assert "filing_file" in doc
        assert "url" in doc
        
        assert doc["ticker"] == "AAPL"
        assert len(doc["text"]) > 0


def test_arelle_availability():
    """Test Arelle availability check"""
    is_available = check_arelle_available()
    assert isinstance(is_available, bool)


@pytest.mark.skipif(not check_arelle_available(), reason="Arelle not available")
def test_xbrl_facts_extraction():
    """Test XBRL facts extraction (requires Arelle)"""
    # This test only runs if Arelle is available
    from src.ingest.sec.xbrl import extract_facts_from_filing
    
    # Try to extract facts from a known filing directory
    # Note: This is a placeholder test - would need actual XBRL files
    facts_df = extract_facts_from_filing("nonexistent_path")
    
    # Should return empty DataFrame for nonexistent path
    assert isinstance(facts_df, pd.DataFrame)


def test_data_quality():
    """Test data quality of extracted sections"""
    from src.core.paths import SEC_SECTIONS_PARQUET
    
    if not SEC_SECTIONS_PARQUET.exists():
        pytest.skip("No sections data available")
    
    sections_df = pd.read_parquet(SEC_SECTIONS_PARQUET)
    
    if sections_df.empty:
        pytest.skip("No sections data available")
    
    # Check data quality
    assert not sections_df["ticker"].isna().any()
    assert not sections_df["section_title"].isna().any()
    assert not sections_df["content"].isna().any()
    
    # Check that content is not empty
    assert not sections_df["content"].str.strip().eq("").any()
    
    # Check that tickers are uppercase
    assert sections_df["ticker"].str.isupper().all()


def test_integration_workflow():
    """Test the complete integration workflow"""
    # Step 1: Fetch filings
    files = fetch_filings("AAPL", limit=1)
    
    # Step 2: Extract sections (if files available)
    if files:
        html_files = [f for f in files if f.endswith((".htm", ".html"))]
        if html_files:
            sections = extract_key_sections(html_files[0])
            assert isinstance(sections, dict)
            
            # Step 3: Create documents
            documents = []
            for title, content in sections.items():
                doc = {
                    "id": f"AAPL:test:{title}",
                    "title": title,
                    "text": content,
                    "ticker": "AAPL"
                }
                documents.append(doc)
            
            assert len(documents) > 0
            
            # Step 4: Verify document structure
            for doc in documents:
                assert "id" in doc
                assert "title" in doc
                assert "text" in doc
                assert "ticker" in doc
                assert len(doc["text"]) > 0
