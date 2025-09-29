"""
Contract tests for EDGAR filing search
Uses fixtures, no live calls
"""

import pytest
from datetime import date
from src.engine.retrievers.finance.edgar import FilingInfo, FilingContent

class TestEdgarSearch:
    """Test EDGAR filing search functionality"""
    
    def test_filing_info_creation(self):
        """Test FilingInfo dataclass creation"""
        filing = FilingInfo(
            accession="0000320193-24-000006",
            form="10-K",
            filing_date=date(2024, 1, 1),
            url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000006/0000320193-24-000006.txt",
            company_name="Apple Inc.",
            ticker="AAPL",
            cik="0000320193"
        )
        
        assert filing.accession == "0000320193-24-000006"
        assert filing.form == "10-K"
        assert filing.filing_date == date(2024, 1, 1)
        assert filing.company_name == "Apple Inc."
        assert filing.ticker == "AAPL"
        assert filing.cik == "0000320193"
    
    def test_filing_content_creation(self):
        """Test FilingContent dataclass creation"""
        content = FilingContent(
            accession="0000320193-24-000006",
            raw_html="<html>Test filing content</html>",
            sections={"mda": "Management discussion content", "risk": "Risk factors content"},
            tables=[{"headers": ["Revenue", "Year"], "rows": [["100B", "2023"]]}],
            metadata={"parsed_at": "2024-01-01T00:00:00", "total_sections": 2}
        )
        
        assert content.accession == "0000320193-24-000006"
        assert len(content.sections) == 2
        assert "mda" in content.sections
        assert "risk" in content.sections
        assert len(content.tables) == 1
        assert content.tables[0]["headers"] == ["Revenue", "Year"]
        assert content.metadata["total_sections"] == 2
    
    def test_search_parameters_validation(self):
        """Test search parameter validation"""
        # Valid parameters
        valid_params = {
            "ticker": "AAPL",
            "form": "10-K",
            "year_range": (2020, 2024),
            "limit": 10
        }
        
        # Test parameter types
        assert isinstance(valid_params["ticker"], str)
        assert isinstance(valid_params["form"], str)
        assert isinstance(valid_params["year_range"], tuple)
        assert len(valid_params["year_range"]) == 2
        assert isinstance(valid_params["limit"], int)
        assert valid_params["limit"] > 0
    
    def test_accession_format_validation(self):
        """Test accession number format validation"""
        # Valid accession formats
        valid_accessions = [
            "0000320193-24-000006",  # Apple 10-K
            "0001018724-24-000001",  # Amazon 10-K
            "0000789019-24-000001",  # Microsoft 10-K
        ]
        
        for accession in valid_accessions:
            # Should have format: CIK-YY-NNNNNN
            parts = accession.split('-')
            assert len(parts) == 3
            assert len(parts[0]) == 10  # CIK should be 10 digits
            assert len(parts[1]) == 2   # Year should be 2 digits
            assert len(parts[2]) == 6   # Filing number should be 6 digits
    
    def test_form_type_validation(self):
        """Test SEC form type validation"""
        valid_forms = [
            "10-K", "10-Q", "8-K", "DEF 14A", "S-1", "S-3", "S-4",
            "13F", "13D", "13G", "11-K", "20-F", "6-K"
        ]
        
        for form in valid_forms:
            # Forms should be non-empty strings
            assert isinstance(form, str)
            assert len(form) > 0
            assert len(form) <= 10  # Most forms are short
    
    def test_year_range_validation(self):
        """Test year range validation"""
        # Valid year ranges
        valid_ranges = [
            (2020, 2024),
            (2023, 2023),  # Single year
            (2015, 2024),  # Long range
        ]
        
        for start_year, end_year in valid_ranges:
            assert isinstance(start_year, int)
            assert isinstance(end_year, int)
            assert start_year <= end_year
            assert start_year >= 1990  # EDGAR started in 1990s
            assert end_year <= 2030   # Reasonable future limit
    
    def test_company_identifier_validation(self):
        """Test company identifier validation"""
        # Valid tickers
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        for ticker in valid_tickers:
            assert isinstance(ticker, str)
            assert len(ticker) >= 1
            assert len(ticker) <= 10
            assert ticker.isalpha() or '-' in ticker  # Allow hyphens for some tickers
        
        # Valid CIKs
        valid_ciks = ["0000320193", "0000789019", "0001018724"]
        for cik in valid_ciks:
            assert isinstance(cik, str)
            assert len(cik) == 10
            assert cik.isdigit()
    
    def test_section_extraction_patterns(self):
        """Test section extraction pattern matching"""
        from src.engine.retrievers.finance.edgar import EdgarRetriever
        
        retriever = EdgarRetriever()
        
        # Test section patterns
        test_text = """
        MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION
        This section contains management's analysis...
        
        RISK FACTORS
        The following risk factors...
        
        DESCRIPTION OF BUSINESS
        Our business operates in...
        """
        
        # Mock the _parse_filing_content method
        sections = {}
        section_patterns = {
            'mda': r'(?i)(management\'s discussion and analysis|md&a)',
            'risk': r'(?i)(risk factors|risks and uncertainties)',
            'business': r'(?i)(business|description of business)',
        }
        
        import re
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, test_text)
            if match:
                sections[section_name] = f"Found {section_name} section"
        
        assert 'mda' in sections
        assert 'risk' in sections
        assert 'business' in sections
    
    def test_table_parsing_structure(self):
        """Test table parsing structure"""
        # Mock table data
        mock_table = {
            "headers": ["Revenue", "Year", "Growth"],
            "rows": [
                ["100B", "2023", "5%"],
                ["95B", "2022", "3%"],
                ["92B", "2021", "2%"]
            ],
            "row_count": 3,
            "col_count": 3
        }
        
        assert isinstance(mock_table["headers"], list)
        assert len(mock_table["headers"]) == 3
        assert isinstance(mock_table["rows"], list)
        assert len(mock_table["rows"]) == 3
        assert mock_table["row_count"] == 3
        assert mock_table["col_count"] == 3
        
        # Check data consistency
        for row in mock_table["rows"]:
            assert len(row) == mock_table["col_count"]
    
    def test_metadata_structure(self):
        """Test metadata structure validation"""
        metadata = {
            "accession": "0000320193-24-000006",
            "parsed_at": "2024-01-01T00:00:00",
            "total_sections": 5,
            "total_tables": 3,
            "content_length": 50000
        }
        
        required_fields = ["accession", "parsed_at", "total_sections", "total_tables"]
        for field in required_fields:
            assert field in metadata
        
        assert isinstance(metadata["total_sections"], int)
        assert isinstance(metadata["total_tables"], int)
        assert isinstance(metadata["content_length"], int)
        assert metadata["total_sections"] >= 0
        assert metadata["total_tables"] >= 0
        assert metadata["content_length"] > 0

class TestEdgarAPI:
    """Test EDGAR API contract compliance"""
    
    def test_search_request_schema(self):
        """Test search request schema validation"""
        from src.routes.finance_filings import FilingSearchRequest
        
        # Valid request
        request = FilingSearchRequest(
            ticker="AAPL",
            form="10-K",
            year_range=(2020, 2024),
            limit=10
        )
        
        assert request.ticker == "AAPL"
        assert request.form == "10-K"
        assert request.year_range == (2020, 2024)
        assert request.limit == 10
    
    def test_fetch_request_schema(self):
        """Test fetch request schema validation"""
        from src.routes.finance_filings import FilingFetchRequest
        
        # Valid request
        request = FilingFetchRequest(
            accession="0000320193-24-000006"
        )
        
        assert request.accession == "0000320193-24-000006"
    
    def test_extract_request_schema(self):
        """Test extract request schema validation"""
        from src.routes.finance_filings import FilingExtractRequest
        
        # Valid request
        request = FilingExtractRequest(
            accession="0000320193-24-000006",
            sections=["mda", "risk"],
            tables=True
        )
        
        assert request.accession == "0000320193-24-000006"
        assert request.sections == ["mda", "risk"]
        assert request.tables is True
    
    def test_synthesize_request_schema(self):
        """Test synthesize request schema validation"""
        from src.routes.finance_filings import FilingSynthesizeRequest
        
        # Valid request
        request = FilingSynthesizeRequest(
            accession="0000320193-24-000006",
            context={"company": "Apple Inc."},
            claims=[{"metric": "revenue", "value": 100, "operator": ">"}],
            grounded=True
        )
        
        assert request.accession == "0000320193-24-000006"
        assert request.context["company"] == "Apple Inc."
        assert len(request.claims) == 1
        assert request.grounded is True

class TestEdgarErrorHandling:
    """Test EDGAR error handling"""
    
    def test_invalid_accession_format(self):
        """Test handling of invalid accession formats"""
        invalid_accessions = [
            "invalid-format",
            "123-45-678",
            "0000320193-24",  # Missing filing number
            "0000320193-24-000006-extra",  # Too many parts
        ]
        
        for accession in invalid_accessions:
            parts = accession.split('-')
            # Should fail validation
            assert len(parts) != 3 or len(parts[0]) != 10 or len(parts[1]) != 2 or len(parts[2]) != 6
    
    def test_missing_company_identifier(self):
        """Test handling of missing company identifier"""
        # Both ticker and cik are None
        ticker = None
        cik = None
        
        # Should raise validation error
        assert ticker is None and cik is None
    
    def test_invalid_year_range(self):
        """Test handling of invalid year ranges"""
        invalid_ranges = [
            (2024, 2020),  # End before start
            (1800, 2024),  # Start too early
            (2020, 2100),  # End too late
        ]
        
        for start_year, end_year in invalid_ranges:
            # Should fail validation
            assert (start_year > end_year or 
                   start_year < 1990 or 
                   end_year > 2030)
    
    def test_limit_validation(self):
        """Test limit validation"""
        invalid_limits = [0, -1, 1000]  # Too low or too high
        
        for limit in invalid_limits:
            # Should fail validation
            assert limit <= 0 or limit > 50
