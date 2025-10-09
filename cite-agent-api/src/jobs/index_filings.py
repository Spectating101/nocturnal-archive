"""
Index SEC filings into the RAG vector database
"""
from typing import List, Dict, Any
from datetime import datetime
from src.jobs.filings_etl import run
from src.rag.index import upsert_docs
from src.jobs.symbol_map import cik_for_ticker


def index_ticker(ticker: str, limit: int = 1) -> Dict[str, Any]:
    """
    Index SEC filings for a ticker into the RAG database
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of filings per form type to process
        
    Returns:
        Dict: Indexing results summary
    """
    print(f"Starting indexing for {ticker} (limit={limit})")
    
    start_time = datetime.now()
    
    try:
        # Run ETL to get documents
        print(f"Step 1: Running ETL for {ticker}")
        documents = run(ticker, limit=limit)
        
        if not documents:
            return {
                "ticker": ticker.upper(),
                "status": "failed",
                "error": "No documents generated from ETL",
                "documents_indexed": 0,
                "duration": 0
            }
        
        # Add CIK information to documents
        print(f"Step 2: Adding CIK information")
        cik = cik_for_ticker(ticker)
        
        for doc in documents:
            doc["cik"] = cik or ""
            # Ensure we have required fields
            if "url" not in doc:
                doc["url"] = ""
            if "date" not in doc:
                doc["date"] = datetime.now().date()
        
        # Index documents into vector database
        print(f"Step 3: Indexing {len(documents)} documents")
        chunks_indexed = upsert_docs(documents)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Indexing completed in {duration:.2f} seconds")
        
        return {
            "ticker": ticker.upper(),
            "status": "success",
            "documents_indexed": len(documents),
            "chunks_indexed": chunks_indexed,
            "duration": duration,
            "cik": cik,
            "sections": [doc.get("section", "") for doc in documents]
        }
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Indexing failed: {str(e)}")
        
        return {
            "ticker": ticker.upper(),
            "status": "failed",
            "error": str(e),
            "documents_indexed": 0,
            "duration": duration
        }


def index_multiple_tickers(tickers: List[str], limit: int = 1) -> List[Dict[str, Any]]:
    """
    Index multiple tickers
    
    Args:
        tickers: List of ticker symbols
        limit: Number of filings per form type per ticker
        
    Returns:
        List[Dict]: Results for each ticker
    """
    results = []
    
    for ticker in tickers:
        print(f"\n{'='*50}")
        print(f"Indexing {ticker}")
        print(f"{'='*50}")
        
        result = index_ticker(ticker, limit=limit)
        results.append(result)
        
        # Print summary
        if result["status"] == "success":
            print(f"✅ {ticker}: {result['documents_indexed']} docs, {result['chunks_indexed']} chunks")
        else:
            print(f"❌ {ticker}: {result['error']}")
    
    # Print overall summary
    print(f"\n{'='*50}")
    print("INDEXING SUMMARY")
    print(f"{'='*50}")
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_docs = sum(r["documents_indexed"] for r in successful)
        total_chunks = sum(r["chunks_indexed"] for r in successful)
        total_duration = sum(r["duration"] for r in results)
        
        print(f"Total documents: {total_docs}")
        print(f"Total chunks: {total_chunks}")
        print(f"Total duration: {total_duration:.2f}s")
    
    return results


def get_indexing_status(ticker: str) -> Dict[str, Any]:
    """
    Get indexing status for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict: Status information
    """
    from src.rag.index import get_doc_stats
    
    try:
        stats = get_doc_stats()
        
        # Find ticker-specific stats
        ticker_stats = None
        for ticker_stat in stats.get("ticker_counts", []):
            if ticker_stat["ticker"] == ticker.upper():
                ticker_stats = ticker_stat
                break
        
        return {
            "ticker": ticker.upper(),
            "indexed": ticker_stats is not None,
            "document_count": ticker_stats["count"] if ticker_stats else 0,
            "total_documents": stats.get("total_documents", 0),
            "date_range": stats.get("date_range", {}),
            "sections": [s["section"] for s in stats.get("section_counts", [])]
        }
        
    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "indexed": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # CLI usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.jobs.index_filings <ticker> [limit]")
        print("  python -m src.jobs.index_filings --multiple <ticker1,ticker2,...> [limit]")
        print("  python -m src.jobs.index_filings --status <ticker>")
        sys.exit(1)
    
    if sys.argv[1] == "--multiple":
        if len(sys.argv) < 3:
            print("Error: --multiple requires ticker list")
            sys.exit(1)
        
        tickers = [t.strip().upper() for t in sys.argv[2].split(",")]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        results = index_multiple_tickers(tickers, limit=limit)
        
    elif sys.argv[1] == "--status":
        if len(sys.argv) < 3:
            print("Error: --status requires ticker")
            sys.exit(1)
        
        ticker = sys.argv[2].upper()
        status = get_indexing_status(ticker)
        print(f"Status for {ticker}:")
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    else:
        ticker = sys.argv[1].upper()
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        
        result = index_ticker(ticker, limit=limit)
        
        print(f"\nIndexing result for {ticker}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
