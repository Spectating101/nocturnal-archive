"""
Data directory paths and file management
"""
from pathlib import Path

# Data directory structure
DATA_DIR = Path("./data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Symbol mapping files
SYMBOL_MAP_JSON = DATA_DIR / "company_tickers.json"
SYMBOL_MAP_PARQUET = DATA_DIR / "symbol_map.parquet"

# SEC filings directory
SEC_DIR = DATA_DIR / "sec"
SEC_DIR.mkdir(parents=True, exist_ok=True)

# SEC facts and documents
SEC_FACTS_PARQUET = SEC_DIR / "facts.parquet"
SEC_SECTIONS_PARQUET = SEC_DIR / "sections.parquet"
