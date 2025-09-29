"""
Contract tests for EDGAR filing parser edge cases
"""

import pytest
from src.engine.retrievers.finance.edgar import EdgarRetriever


class TestEdgarParserEdgeCases:
    """Test EDGAR parser with known problematic filings"""
    
    def test_fuzzy_heading_detection(self):
        """Test detection of various heading formats"""
        retriever = EdgarRetriever()
        
        # Test cases with different heading formats
        test_cases = [
            # Standard formats
            ("Item 7. Management's Discussion and Analysis", "mda"),
            ("ITEM 7 - MANAGEMENT'S DISCUSSION AND ANALYSIS", "mda"),
            ("Item 7: Management's Discussion and Analysis", "mda"),
            
            # Variations
            ("Management's Discussion and Analysis of Financial Condition", "mda"),
            ("MD&A", "mda"),
            ("Management Discussion & Analysis", "mda"),
            
            # Risk factors
            ("Item 1A. Risk Factors", "risk"),
            ("ITEM 1A - RISK FACTORS", "risk"),
            ("Risk Factors and Uncertainties", "risk"),
            
            # Business
            ("Item 1. Business", "business"),
            ("Description of Business", "business"),
            ("Business Overview", "business"),
        ]
        
        for heading, expected_section in test_cases:
            # Create mock HTML with the heading
            mock_html = f"""
            <html>
            <body>
                <h1>{heading}</h1>
                <p>Some content here...</p>
            </body>
            </html>
            """
            
            content = retriever._parse_filing_content("test-123", mock_html)
            assert expected_section in content.sections, f"Failed to detect {expected_section} in '{heading}'"
    
    def test_nested_table_parsing(self):
        """Test parsing of nested and complex tables"""
        retriever = EdgarRetriever()
        
        # Test case with nested table
        mock_html = """
        <html>
        <body>
            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Revenue</th>
                        <th>Growth</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2023</td>
                        <td>$100M</td>
                        <td>15%</td>
                    </tr>
                    <tr>
                        <td>2022</td>
                        <td>$87M</td>
                        <td>12%</td>
                    </tr>
                </tbody>
            </table>
            
            <table>
                <tr>
                    <td colspan="2">Consolidated Results</td>
                </tr>
                <tr>
                    <td>Q1 2023</td>
                    <td>$25M</td>
                </tr>
                <tr>
                    <td>Q2 2023</td>
                    <td>$30M</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        content = retriever._parse_filing_content("test-456", mock_html)
        
        # Should extract both tables
        assert len(content.tables) == 2
        
        # First table should have proper headers
        first_table = content.tables[0]
        assert "headers" in first_table
        assert len(first_table["headers"]) == 3
        assert "Year" in first_table["headers"]
        
        # Second table should handle colspan
        second_table = content.tables[1]
        assert "rows" in second_table
        assert len(second_table["rows"]) >= 2
    
    def test_footnote_handling(self):
        """Test handling of footnotes and special characters"""
        retriever = EdgarRetriever()
        
        mock_html = """
        <html>
        <body>
            <p>Revenue increased 15% year-over-year<sup>1</sup>.</p>
            <p>This includes a one-time gain of $5M<sup>2</sup>.</p>
            
            <table>
                <tr>
                    <td>2023 Revenue</td>
                    <td>$100M<sup>1</sup></td>
                </tr>
            </table>
            
            <div class="footnotes">
                <p><sup>1</sup> Excludes discontinued operations</p>
                <p><sup>2</sup> Related to asset sale</p>
            </div>
        </body>
        </html>
        """
        
        content = retriever._parse_filing_content("test-789", mock_html)
        
        # Should extract content with footnotes
        assert len(content.sections) > 0
        
        # Tables should handle superscripts
        if content.tables:
            table = content.tables[0]
            assert "rows" in table
    
    def test_amended_filing_detection(self):
        """Test detection of amended filings"""
        retriever = EdgarRetriever()
        
        # Test amended filing detection
        amended_html = """
        <html>
        <body>
            <h1>10-K/A - Apple Inc.</h1>
            <p>This is an amended filing...</p>
        </body>
        </html>
        """
        
        content = retriever._parse_filing_content("test-10k-a", amended_html)
        
        # Should detect amended filing
        assert content.metadata.get("amends") is True
    
    def test_known_bad_fixtures(self):
        """Test with known problematic filing fixtures"""
        retriever = EdgarRetriever()
        
        # Fixture 1: Malformed HTML
        malformed_html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>Incomplete row
                </tr>
            </table>
            <p>Unclosed paragraph
        </body>
        </html>
        """
        
        content = retriever._parse_filing_content("malformed-1", malformed_html)
        # Should not crash, may have empty sections/tables
        assert content.accession == "malformed-1"
        
        # Fixture 2: Empty content
        empty_html = "<html><body></body></html>"
        content = retriever._parse_filing_content("empty-1", empty_html)
        assert content.accession == "empty-1"
        assert len(content.sections) == 0
        assert len(content.tables) == 0
        
        # Fixture 3: Very large content
        large_html = "<html><body>" + "x" * 1000000 + "</body></html>"
        content = retriever._parse_filing_content("large-1", large_html)
        assert content.accession == "large-1"
        # Should handle large content without crashing
    
    def test_section_boundary_detection(self):
        """Test detection of section boundaries"""
        retriever = EdgarRetriever()
        
        mock_html = """
        <html>
        <body>
            <h1>Item 7. Management's Discussion and Analysis</h1>
            <p>This is the MD&A section content...</p>
            <p>More MD&A content...</p>
            
            <h2>Item 8. Financial Statements</h2>
            <p>This is the financial statements section...</p>
            
            <h1>Item 1A. Risk Factors</h1>
            <p>This is the risk factors section...</p>
        </body>
        </html>
        """
        
        content = retriever._parse_filing_content("boundary-test", mock_html)
        
        # Should extract multiple sections
        assert "mda" in content.sections
        assert "financial" in content.sections
        assert "risk" in content.sections
        
        # Each section should have reasonable content length
        for section_name, section_content in content.sections.items():
            assert len(section_content) > 10, f"Section {section_name} too short"
            assert len(section_content) < 10000, f"Section {section_name} too long"

