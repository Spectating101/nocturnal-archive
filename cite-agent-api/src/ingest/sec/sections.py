"""
SEC filing sections extraction and parsing
"""
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from pathlib import Path


# Common SEC filing sections to extract
STANDARD_ITEMS = [
    "item 1a",
    "item 1b", 
    "item 2",
    "item 3",
    "item 4",
    "item 5",
    "item 6",
    "item 7",
    "item 7a",
    "item 8",
    "item 9",
    "item 10",
    "item 11",
    "item 12",
    "item 13",
    "item 14",
    "item 15",
    "risk factors",
    "management's discussion",
    "business",
    "properties",
    "legal proceedings",
    "market risk",
    "controls and procedures"
]


def html_to_sections(html: str) -> Dict[str, str]:
    """
    Extract structured sections from SEC filing HTML
    
    Args:
        html: HTML content of SEC filing
        
    Returns:
        Dict[str, str]: Mapping of section titles to content
    """
    soup = BeautifulSoup(html, "lxml")
    
    # Remove scripts, styles, and other non-content elements
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    
    # Get clean text
    text = soup.get_text("\n")
    
    # Clean up whitespace
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines()]
    lines = [x for x in lines if x]  # Remove empty lines
    
    blob = "\n".join(lines)
    
    # Find sections
    sections = {}
    current_section = None
    
    for line in blob.split("\n"):
        line_lower = line.lower()
        
        # Check if this line starts a new section
        section_found = None
        for item in STANDARD_ITEMS:
            if item in line_lower:
                # More specific check to avoid false positives
                if re.search(rf"\b{item}\b", line_lower):
                    section_found = line.strip()
                    break
        
        if section_found:
            current_section = section_found
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    
    # Clean up sections
    result = {}
    for title, content_lines in sections.items():
        if content_lines:
            content = "\n".join(content_lines).strip()
            # Remove very short sections (likely false positives)
            if len(content) > 100:
                result[title] = content
    
    return result


def extract_key_sections(filing_path: str) -> Dict[str, str]:
    """
    Extract key sections from a filing file
    
    Args:
        filing_path: Path to the filing file
        
    Returns:
        Dict[str, str]: Key sections with their content
    """
    try:
        content = Path(filing_path).read_text(encoding='utf-8', errors='ignore')
        
        # Extract HTML content from SEC document wrapper
        if "<SEC-DOCUMENT>" in content and "<TEXT>" in content:
            # Extract the HTML content between <TEXT> and </TEXT>
            start = content.find("<TEXT>")
            end = content.find("</TEXT>", start)
            if start != -1 and end != -1:
                html_content = content[start + 6:end]  # Remove <TEXT> tag
                return html_to_sections(html_content)
            else:
                # Fallback: try to extract HTML from the entire content
                return html_to_sections(content)
        else:
            # Regular HTML file
            return html_to_sections(content)
            
    except Exception as e:
        print(f"Error processing {filing_path}: {e}")
        return {}


def get_business_description(sections: Dict[str, str]) -> str:
    """
    Extract business description from sections
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        str: Business description text
    """
    # Try different section names for business description
    business_keys = [
        "item 1",
        "business",
        "business overview",
        "description of business"
    ]
    
    for key in business_keys:
        for section_title, content in sections.items():
            if key in section_title.lower():
                return content
    
    return ""


def get_risk_factors(sections: Dict[str, str]) -> str:
    """
    Extract risk factors from sections
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        str: Risk factors text
    """
    risk_keys = [
        "item 1a",
        "risk factors",
        "risk factor"
    ]
    
    for key in risk_keys:
        for section_title, content in sections.items():
            if key in section_title.lower():
                return content
    
    return ""


def get_md_and_a(sections: Dict[str, str]) -> str:
    """
    Extract Management's Discussion and Analysis from sections
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        str: MD&A text
    """
    md_a_keys = [
        "item 7",
        "management's discussion",
        "management discussion",
        "md&a"
    ]
    
    for key in md_a_keys:
        for section_title, content in sections.items():
            if key in section_title.lower():
                return content
    
    return ""


def get_financial_statements(sections: Dict[str, str]) -> str:
    """
    Extract financial statements discussion from sections
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        str: Financial statements text
    """
    financial_keys = [
        "item 8",
        "financial statements",
        "consolidated statements",
        "financial condition"
    ]
    
    for key in financial_keys:
        for section_title, content in sections.items():
            if key in section_title.lower():
                return content
    
    return ""


def summarize_sections(sections: Dict[str, str]) -> Dict[str, any]:
    """
    Create a summary of extracted sections
    
    Args:
        sections: Parsed sections dictionary
        
    Returns:
        Dict[str, any]: Section summary with counts and key info
    """
    total_sections = len(sections)
    total_chars = sum(len(content) for content in sections.values())
    
    # Find the largest sections
    section_sizes = [(title, len(content)) for title, content in sections.items()]
    section_sizes.sort(key=lambda x: x[1], reverse=True)
    
    largest_sections = section_sizes[:5]
    
    # Extract key content
    business_desc = get_business_description(sections)
    risk_factors = get_risk_factors(sections)
    md_a = get_md_and_a(sections)
    financials = get_financial_statements(sections)
    
    return {
        "total_sections": total_sections,
        "total_characters": total_chars,
        "largest_sections": largest_sections,
        "has_business_description": len(business_desc) > 0,
        "has_risk_factors": len(risk_factors) > 0,
        "has_md_a": len(md_a) > 0,
        "has_financials": len(financials) > 0,
        "section_titles": list(sections.keys())
    }


if __name__ == "__main__":
    # CLI usage for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest.sec.sections <filing_path>")
        sys.exit(1)
    
    filing_path = sys.argv[1]
    sections = extract_key_sections(filing_path)
    
    print(f"Extracted {len(sections)} sections from {filing_path}")
    print("\nSections found:")
    for title in sections.keys():
        print(f"  - {title}")
    
    summary = summarize_sections(sections)
    print(f"\nSummary: {summary['total_sections']} sections, {summary['total_characters']} characters")
