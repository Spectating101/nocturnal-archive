"""
End-to-end SEC filings ETL pipeline
"""
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from src.ingest.sec.fetch import fetch_filings, list_filings, get_filing_content
from src.ingest.sec.sections import extract_key_sections, summarize_sections
from src.ingest.sec.xbrl import extract_facts_from_filing, summarize_facts
from src.core.paths import SEC_SECTIONS_PARQUET


def run_filings_etl(ticker: str, limit: int = 2, extract_xbrl: bool = False) -> Dict[str, Any]:
    """
    Run complete ETL pipeline for a ticker
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of filings per form type to process
        extract_xbrl: Whether to extract XBRL facts (requires Arelle)
        
    Returns:
        Dict[str, Any]: ETL results summary
    """
    print(f"Starting ETL for {ticker} (limit={limit})")
    
    results = {
        "ticker": ticker.upper(),
        "start_time": datetime.now(),
        "filings_processed": 0,
        "sections_extracted": 0,
        "facts_extracted": 0,
        "errors": []
    }
    
    try:
        # Step 1: Fetch filings
        print(f"Step 1: Fetching filings for {ticker}")
        filing_files = fetch_filings(ticker, limit=limit)
        
        if not filing_files:
            results["errors"].append("No filings downloaded")
            return results
        
        print(f"Downloaded {len(filing_files)} filing files")
        
        # Step 2: Extract sections from HTML files
        print("Step 2: Extracting sections from filings")
        all_sections = []
        
        for filing_file in filing_files:
            if not filing_file.endswith((".htm", ".html", ".txt")):
                continue
                
            try:
                print(f"Processing sections from {Path(filing_file).name}")
                sections = extract_key_sections(filing_file)
                
                if sections:
                    # Create section documents for indexing
                    for section_title, section_content in sections.items():
                        doc = {
                            "id": f"{ticker}:{Path(filing_file).stem}:{section_title}",
                            "ticker": ticker.upper(),
                            "filing_file": Path(filing_file).name,
                            "section_title": section_title,
                            "content": section_content,
                            "extracted_at": datetime.now(),
                            "char_count": len(section_content)
                        }
                        all_sections.append(doc)
                    
                    results["sections_extracted"] += len(sections)
                
            except Exception as e:
                error_msg = f"Error processing {filing_file}: {str(e)}"
                print(error_msg)
                results["errors"].append(error_msg)
        
        # Save sections to parquet
        if all_sections:
            sections_df = pd.DataFrame(all_sections)
            sections_df.to_parquet(SEC_SECTIONS_PARQUET, index=False)
            print(f"Saved {len(all_sections)} sections to {SEC_SECTIONS_PARQUET}")
        
        # Step 3: Extract XBRL facts (optional)
        if extract_xbrl:
            print("Step 3: Extracting XBRL facts")
            try:
                # Find XBRL files in downloaded filings
                xbrl_files = []
                for filing_file in filing_files:
                    filing_dir = Path(filing_file).parent
                    xbrl_files.extend([str(f) for f in filing_dir.rglob("*.xml") if f.is_file()])
                
                if xbrl_files:
                    facts_df = extract_facts_from_filing(xbrl_files[0])  # Process first XBRL file
                    if not facts_df.empty:
                        results["facts_extracted"] = len(facts_df)
                        print(f"Extracted {len(facts_df)} XBRL facts")
                    else:
                        results["errors"].append("No XBRL facts extracted")
                else:
                    results["errors"].append("No XBRL files found")
                    
            except Exception as e:
                error_msg = f"Error extracting XBRL facts: {str(e)}"
                print(error_msg)
                results["errors"].append(error_msg)
        
        results["filings_processed"] = len(filing_files)
        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
        
        print(f"ETL completed in {results['duration']:.2f} seconds")
        print(f"Results: {results['filings_processed']} filings, {results['sections_extracted']} sections")
        if extract_xbrl:
            print(f"XBRL facts: {results['facts_extracted']}")
        
        return results
        
    except Exception as e:
        error_msg = f"ETL failed: {str(e)}"
        print(error_msg)
        results["errors"].append(error_msg)
        results["end_time"] = datetime.now()
        return results


def create_searchable_documents(ticker: str) -> List[Dict[str, Any]]:
    """
    Create searchable documents from extracted sections
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List[Dict[str, Any]]: Documents ready for search indexing
    """
    documents = []
    
    if not SEC_SECTIONS_PARQUET.exists():
        print(f"No sections data found for {ticker}")
        return documents
    
    sections_df = pd.read_parquet(SEC_SECTIONS_PARQUET)
    ticker_sections = sections_df[sections_df["ticker"] == ticker.upper()]
    
    for _, row in ticker_sections.iterrows():
        doc = {
            "id": row["id"],
            "title": row["section_title"],
            "text": row["content"],
            "ticker": row["ticker"],
            "filing_file": row["filing_file"],
            "url": f"https://www.sec.gov/Archives/edgar/data/{row['ticker']}/{row['filing_file']}",
            "date": row["extracted_at"].date() if hasattr(row["extracted_at"], 'date') else None
        }
        documents.append(doc)
    
    print(f"Created {len(documents)} searchable documents for {ticker}")
    return documents


def get_etl_status(ticker: str) -> Dict[str, Any]:
    """
    Get ETL status for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict[str, Any]: ETL status information
    """
    status = {
        "ticker": ticker.upper(),
        "has_sections": False,
        "has_facts": False,
        "sections_count": 0,
        "facts_count": 0,
        "last_updated": None
    }
    
    # Check sections
    if SEC_SECTIONS_PARQUET.exists():
        sections_df = pd.read_parquet(SEC_SECTIONS_PARQUET)
        ticker_sections = sections_df[sections_df["ticker"] == ticker.upper()]
        if not ticker_sections.empty:
            status["has_sections"] = True
            status["sections_count"] = len(ticker_sections)
            status["last_updated"] = ticker_sections["extracted_at"].max()
    
    # Check facts (if available)
    from src.core.paths import SEC_FACTS_PARQUET
    if SEC_FACTS_PARQUET.exists():
        facts_df = pd.read_parquet(SEC_FACTS_PARQUET)
        if not facts_df.empty:
            status["has_facts"] = True
            status["facts_count"] = len(facts_df)
    
    return status


def run(ticker: str = "AAPL", limit: int = 1, extract_xbrl: bool = False) -> List[Dict[str, Any]]:
    """
    Convenience function to run ETL and return documents
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of filings per form type
        extract_xbrl: Whether to extract XBRL facts
        
    Returns:
        List[Dict[str, Any]]: Searchable documents
    """
    results = run_filings_etl(ticker, limit=limit, extract_xbrl=extract_xbrl)
    
    if results["errors"]:
        print(f"ETL completed with errors: {results['errors']}")
    
    documents = create_searchable_documents(ticker)
    return documents


if __name__ == "__main__":
    # CLI usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.jobs.filings_etl <ticker> [limit] [--xbrl]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "--xbrl" else 1
    extract_xbrl = "--xbrl" in sys.argv
    
    print(f"Running ETL for {ticker} (limit={limit}, xbrl={extract_xbrl})")
    
    documents = run(ticker, limit=limit, extract_xbrl=extract_xbrl)
    
    print(f"\nCreated {len(documents)} searchable documents:")
    for doc in documents[:5]:  # Show first 5
        print(f"  - {doc['title']} ({len(doc['text'])} chars)")
    
    if len(documents) > 5:
        print(f"  ... and {len(documents) - 5} more")
