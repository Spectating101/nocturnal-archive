"""
XBRL facts extraction from SEC filings
"""
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from src.core.paths import SEC_FACTS_PARQUET


def arelle_facts_from_xbrl(xbrl_paths: List[str]) -> pd.DataFrame:
    """
    Extract XBRL facts using Arelle command line tool
    
    Args:
        xbrl_paths: List of paths to XBRL files
        
    Returns:
        pd.DataFrame: Extracted facts with normalized columns
    """
    rows = []
    
    for xbrl_path in xbrl_paths:
        if not xbrl_path.endswith((".xml", ".xbrl")):
            continue
            
        print(f"Processing XBRL file: {xbrl_path}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = Path(temp_dir) / "facts.csv"
            
            # Arelle command to extract facts
            cmd = [
                "arelleCmdLine",
                "--file", xbrl_path,
                "--facts", str(output_csv),
                "--format", "csv"
            ]
            
            try:
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if output_csv.exists():
                    df = pd.read_csv(output_csv)
                    
                    # Normalize column names
                    column_mapping = {
                        "qname": "concept",
                        "value": "value", 
                        "unitID": "unit",
                        "entityIdentifier": "entity",
                        "periodStart": "period_start",
                        "periodEnd": "period_end",
                        "contextRef": "context",
                        "decimals": "decimals",
                        "scale": "scale"
                    }
                    
                    # Keep only columns we care about
                    available_cols = [col for col in column_mapping.keys() if col in df.columns]
                    df_filtered = df[available_cols].copy()
                    
                    # Rename columns
                    df_filtered = df_filtered.rename(columns=column_mapping)
                    
                    # Add source file info
                    df_filtered["source_file"] = Path(xbrl_path).name
                    df_filtered["source_path"] = xbrl_path
                    
                    rows.append(df_filtered)
                    print(f"Extracted {len(df_filtered)} facts from {xbrl_path}")
                    
            except subprocess.TimeoutExpired:
                print(f"Timeout processing {xbrl_path}")
                continue
            except subprocess.CalledProcessError as e:
                print(f"Error processing {xbrl_path}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error processing {xbrl_path}: {e}")
                continue
    
    if not rows:
        print("No XBRL facts extracted")
        return pd.DataFrame()
    
    # Combine all facts
    all_facts = pd.concat(rows, ignore_index=True)
    
    # Save to parquet
    all_facts.to_parquet(SEC_FACTS_PARQUET, index=False)
    print(f"Saved {len(all_facts)} total facts to {SEC_FACTS_PARQUET}")
    
    return all_facts


def find_xbrl_files(filing_dir: str) -> List[str]:
    """
    Find XBRL files in a filing directory
    
    Args:
        filing_dir: Path to filing directory
        
    Returns:
        List[str]: Paths to XBRL files
    """
    xbrl_files = []
    filing_path = Path(filing_dir)
    
    if not filing_path.exists():
        return xbrl_files
    
    # Look for XBRL files
    for file_path in filing_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in {".xml", ".xbrl"}:
            # Check if it's likely an XBRL file by looking for common tags
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if any(tag in content for tag in ["<xbrl", "<us-gaap:", "<ifrs:", "<dei:", "<link:"]):
                    xbrl_files.append(str(file_path))
            except Exception:
                continue
    
    return xbrl_files


def extract_facts_from_filing(filing_path: str) -> pd.DataFrame:
    """
    Extract facts from a single filing
    
    Args:
        filing_path: Path to filing directory or file
        
    Returns:
        pd.DataFrame: Extracted facts
    """
    filing_path = Path(filing_path)
    
    if filing_path.is_file():
        # Single file
        xbrl_files = [str(filing_path)]
    else:
        # Directory - find XBRL files
        xbrl_files = find_xbrl_files(str(filing_path))
    
    if not xbrl_files:
        print(f"No XBRL files found in {filing_path}")
        return pd.DataFrame()
    
    return arelle_facts_from_xbrl(xbrl_files)


def filter_facts_by_concept(facts_df: pd.DataFrame, concepts: List[str]) -> pd.DataFrame:
    """
    Filter facts by concept names
    
    Args:
        facts_df: DataFrame of facts
        concepts: List of concept names to filter by
        
    Returns:
        pd.DataFrame: Filtered facts
    """
    if facts_df.empty or "concept" not in facts_df.columns:
        return pd.DataFrame()
    
    # Create pattern for matching concepts
    concept_pattern = "|".join(concepts)
    mask = facts_df["concept"].str.contains(concept_pattern, case=False, na=False)
    
    return facts_df[mask].copy()


def get_financial_facts(facts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract common financial facts
    
    Args:
        facts_df: DataFrame of facts
        
    Returns:
        pd.DataFrame: Financial facts
    """
    financial_concepts = [
        "revenue",
        "sales",
        "income",
        "profit",
        "loss",
        "assets",
        "liabilities",
        "equity",
        "cash",
        "debt",
        "expense",
        "cost",
        "margin",
        "ratio",
        "earnings",
        "eps",
        "dividend"
    ]
    
    return filter_facts_by_concept(facts_df, financial_concepts)


def summarize_facts(facts_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create a summary of extracted facts
    
    Args:
        facts_df: DataFrame of facts
        
    Returns:
        Dict[str, Any]: Facts summary
    """
    if facts_df.empty:
        return {"total_facts": 0, "concepts": [], "entities": [], "sources": []}
    
    summary = {
        "total_facts": len(facts_df),
        "unique_concepts": facts_df["concept"].nunique() if "concept" in facts_df.columns else 0,
        "unique_entities": facts_df["entity"].nunique() if "entity" in facts_df.columns else 0,
        "unique_sources": facts_df["source_file"].nunique() if "source_file" in facts_df.columns else 0,
        "date_range": None
    }
    
    # Get unique concepts
    if "concept" in facts_df.columns:
        summary["top_concepts"] = facts_df["concept"].value_counts().head(10).to_dict()
    
    # Get unique entities
    if "entity" in facts_df.columns:
        summary["entities"] = facts_df["entity"].unique().tolist()
    
    # Get source files
    if "source_file" in facts_df.columns:
        summary["sources"] = facts_df["source_file"].unique().tolist()
    
    # Get date range if available
    if "period_end" in facts_df.columns:
        try:
            dates = pd.to_datetime(facts_df["period_end"], errors='coerce').dropna()
            if not dates.empty:
                summary["date_range"] = {
                    "earliest": dates.min().strftime("%Y-%m-%d"),
                    "latest": dates.max().strftime("%Y-%m-%d")
                }
        except Exception:
            pass
    
    return summary


def check_arelle_available() -> bool:
    """
    Check if Arelle command line tool is available
    
    Returns:
        bool: True if Arelle is available
    """
    try:
        result = subprocess.run(
            ["arelleCmdLine", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    # CLI usage for testing
    import sys
    
    if not check_arelle_available():
        print("Arelle command line tool not available. Install from: https://arelle.org/")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest.sec.xbrl <filing_path>")
        sys.exit(1)
    
    filing_path = sys.argv[1]
    facts = extract_facts_from_filing(filing_path)
    
    if not facts.empty:
        print(f"Extracted {len(facts)} facts")
        summary = summarize_facts(facts)
        print(f"Summary: {summary}")
        
        # Show some sample facts
        print("\nSample facts:")
        print(facts.head())
    else:
        print("No facts extracted")
