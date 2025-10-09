"""
SEC filings download and management
"""
from pathlib import Path
from typing import List
from sec_edgar_downloader import Downloader
from src.core.paths import SEC_DIR

# SEC download configuration
USER_AGENT = "Finsight/1.0 contact@example.com"


def fetch_filings(
    ticker: str, 
    forms: tuple = ("10-K", "10-Q", "8-K"), 
    limit: int = 2
) -> List[str]:
    """
    Fetch SEC filings for a given ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        forms: Tuple of form types to download (default: 10-K, 10-Q, 8-K)
        limit: Number of filings per form type to download
        
    Returns:
        List[str]: Paths to downloaded filing files
    """
    print(f"Fetching {limit} {forms} filings for {ticker}")
    
    # Create downloader instance
    downloader = Downloader("Finsight", "contact@example.com", str(SEC_DIR))
    
    downloaded_files = []
    
    for form_type in forms:
        try:
            print(f"Downloading {form_type} for {ticker}")
            downloader.get(form_type, ticker, limit=limit)
            
            # Find the downloaded files (they go to sec-edgar-filings subdirectory)
            form_dir = SEC_DIR / "sec-edgar-filings" / ticker.upper() / form_type
            if form_dir.exists():
                for file_path in form_dir.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in {".htm", ".html", ".txt", ".xml"}:
                        downloaded_files.append(str(file_path))
                        
        except Exception as e:
            print(f"Error downloading {form_type} for {ticker}: {e}")
            continue
    
    print(f"Downloaded {len(downloaded_files)} files for {ticker}")
    return downloaded_files


def get_filing_content(file_path: str) -> str:
    """
    Read content from a filing file
    
    Args:
        file_path: Path to the filing file
        
    Returns:
        str: File content
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def list_filings(ticker: str) -> List[dict]:
    """
    List available filings for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List[dict]: Filing information
    """
    ticker_dir = SEC_DIR / "sec-edgar-filings" / ticker.upper()
    filings = []
    
    if not ticker_dir.exists():
        return filings
    
    for form_dir in ticker_dir.iterdir():
        if form_dir.is_dir():
            form_type = form_dir.name
            for filing_dir in form_dir.iterdir():
                if filing_dir.is_dir():
                    # Extract filing date from directory name
                    filing_date = filing_dir.name
                    
                    # Find the main filing file
                    main_file = None
                    for file_path in filing_dir.iterdir():
                        if file_path.suffix.lower() in {".htm", ".html"}:
                            main_file = str(file_path)
                            break
                    
                    if main_file:
                        filings.append({
                            "ticker": ticker.upper(),
                            "form_type": form_type,
                            "filing_date": filing_date,
                            "file_path": main_file,
                            "size": Path(main_file).stat().st_size
                        })
    
    # Sort by filing date (newest first)
    filings.sort(key=lambda x: x["filing_date"], reverse=True)
    return filings


def cleanup_old_filings(ticker: str, keep_days: int = 30):
    """
    Clean up old filings to save space
    
    Args:
        ticker: Stock ticker symbol
        keep_days: Number of days to keep filings
    """
    import time
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    ticker_dir = SEC_DIR / "sec-edgar-filings" / ticker.upper()
    
    if not ticker_dir.exists():
        return
    
    deleted_count = 0
    for form_dir in ticker_dir.iterdir():
        if form_dir.is_dir():
            for filing_dir in form_dir.iterdir():
                if filing_dir.is_dir():
                    # Parse filing date from directory name
                    try:
                        filing_date = datetime.strptime(filing_dir.name, "%Y-%m-%d")
                        if filing_date < cutoff_date:
                            import shutil
                            shutil.rmtree(filing_dir)
                            deleted_count += 1
                            print(f"Deleted old filing: {filing_dir}")
                    except ValueError:
                        # Skip if we can't parse the date
                        continue
    
    print(f"Cleaned up {deleted_count} old filings for {ticker}")


if __name__ == "__main__":
    # CLI usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest.sec.fetch <ticker> [limit]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    files = fetch_filings(ticker, limit=limit)
    print(f"\nDownloaded files:")
    for f in files:
        print(f"  {f}")
