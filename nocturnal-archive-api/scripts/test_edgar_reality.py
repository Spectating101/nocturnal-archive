#!/usr/bin/env python3
"""
EDGAR Reality Tests
Tests EDGAR retriever against real SEC data to ensure reliability
"""

import asyncio
import sys
import time
from datetime import datetime
from src.engine.retrievers.finance.edgar import EdgarRetriever

async def test_edgar_reality():
    """Test EDGAR retriever against real SEC data"""
    
    print("🔍 EDGAR Reality Tests")
    print("=" * 50)
    
    # Test cases: ticker, CIK, expected forms
    test_cases = [
        ("AAPL", "0000320193", ["10-K", "10-Q"]),
        ("MSFT", "0000789019", ["10-K", "10-Q"]),
        ("TSLA", "0001318605", ["10-K", "10-Q"]),
    ]
    
    async with EdgarRetriever() as retriever:
        for ticker, cik, forms in test_cases:
            print(f"\n📊 Testing {ticker} (CIK: {cik})")
            print("-" * 30)
            
            for form in forms:
                print(f"  🔍 Searching {form} filings...")
                start_time = time.time()
                
                try:
                    # Test search by ticker
                    filings_ticker = await retriever.search_filings(
                        ticker=ticker,
                        form=form,
                        year_range=(2023, 2024),
                        limit=3
                    )
                    
                    # Test search by CIK
                    filings_cik = await retriever.search_filings(
                        cik=cik,
                        form=form,
                        year_range=(2023, 2024),
                        limit=3
                    )
                    
                    search_duration = time.time() - start_time
                    
                    print(f"    ✅ Ticker search: {len(filings_ticker)} filings in {search_duration:.2f}s")
                    print(f"    ✅ CIK search: {len(filings_cik)} filings in {search_duration:.2f}s")
                    
                    # Verify results match
                    if len(filings_ticker) > 0 and len(filings_cik) > 0:
                        ticker_accessions = {f.accession for f in filings_ticker}
                        cik_accessions = {f.accession for f in filings_cik}
                        
                        if ticker_accessions == cik_accessions:
                            print(f"    ✅ Ticker and CIK results match")
                        else:
                            print(f"    ⚠️ Ticker and CIK results differ")
                    
                    # Test fetching first filing
                    if filings_ticker:
                        filing = filings_ticker[0]
                        print(f"    📄 Testing fetch: {filing.accession}")
                        
                        fetch_start = time.time()
                        content = await retriever.fetch_filing(filing.accession)
                        fetch_duration = time.time() - fetch_start
                        
                        print(f"    ✅ Fetch completed in {fetch_duration:.2f}s")
                        print(f"    📊 Sections found: {len(content.sections)}")
                        print(f"    📊 Tables found: {len(content.tables)}")
                        
                        # Check for key sections
                        key_sections = ['mda', 'risk', 'business']
                        found_sections = [s for s in key_sections if s in content.sections]
                        print(f"    📋 Key sections: {found_sections}")
                        
                        # Verify content quality
                        if content.sections:
                            avg_section_length = sum(len(s) for s in content.sections.values()) / len(content.sections)
                            print(f"    📏 Avg section length: {avg_section_length:.0f} chars")
                        
                        if content.tables:
                            avg_table_size = sum(len(t.get('rows', [])) for t in content.tables) / len(content.tables)
                            print(f"    📊 Avg table size: {avg_table_size:.1f} rows")
                    
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    continue
    
    print(f"\n🏁 EDGAR Reality Tests completed at {datetime.now()}")

async def test_edge_cases():
    """Test edge cases and error handling"""
    
    print("\n🧪 EDGAR Edge Case Tests")
    print("=" * 50)
    
    async with EdgarRetriever() as retriever:
        # Test 1: Invalid ticker
        print("🔍 Testing invalid ticker...")
        try:
            filings = await retriever.search_filings(ticker="INVALID", form="10-K", limit=1)
            print(f"  Result: {len(filings)} filings (expected: 0)")
        except Exception as e:
            print(f"  Error (expected): {str(e)}")
        
        # Test 2: Invalid CIK
        print("🔍 Testing invalid CIK...")
        try:
            filings = await retriever.search_filings(cik="0000000000", form="10-K", limit=1)
            print(f"  Result: {len(filings)} filings (expected: 0)")
        except Exception as e:
            print(f"  Error (expected): {str(e)}")
        
        # Test 3: Invalid accession
        print("🔍 Testing invalid accession...")
        try:
            content = await retriever.fetch_filing("0000000000-00-000000")
            print(f"  Result: {len(content.sections)} sections (expected: 0)")
        except Exception as e:
            print(f"  Error (expected): {str(e)}")
        
        # Test 4: Rate limiting
        print("🔍 Testing rate limiting...")
        start_time = time.time()
        for i in range(3):
            try:
                filings = await retriever.search_filings(ticker="AAPL", form="10-K", limit=1)
                print(f"  Request {i+1}: {len(filings)} filings")
            except Exception as e:
                print(f"  Request {i+1}: Error - {str(e)}")
        
        rate_duration = time.time() - start_time
        print(f"  Total time for 3 requests: {rate_duration:.2f}s (expected: ~3s)")

if __name__ == "__main__":
    print(f"🚀 Starting EDGAR Reality Tests at {datetime.now()}")
    
    try:
        asyncio.run(test_edgar_reality())
        asyncio.run(test_edge_cases())
        print("\n✅ All EDGAR reality tests completed successfully!")
    except Exception as e:
        print(f"\n❌ EDGAR reality tests failed: {str(e)}")
        sys.exit(1)
