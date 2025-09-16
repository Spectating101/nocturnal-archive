from typing import Dict, List, Optional
from datetime import datetime
import re
import json

from ...utils.logger import logger, log_operation

class MetadataExtractor:
    def __init__(self):
        logger.info("Initializing MetadataExtractor")

    @log_operation("extract_metadata")
    async def extract_metadata(self, content: str, filename: str) -> Dict:
        """Extract metadata from paper content."""
        logger.info(f"Extracting metadata from {filename}")
        
        try:
            metadata = {
                "filename": filename,
                "extracted_at": datetime.utcnow().isoformat(),
                "title": await self._extract_title(content),
                "authors": await self._extract_authors(content),
                "abstract": await self._extract_abstract(content),
                "references": await self._extract_references(content),
                "publication_info": await self._extract_publication_info(content)
            }
            
            logger.info(f"Successfully extracted metadata for {filename}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise

    @log_operation("extract_title")
    async def _extract_title(self, content: str) -> str:
        """Extract paper title."""
        # Look for title in first few lines
        first_lines = content.split('\n')[:10]
        
        # Common patterns for titles
        patterns = [
            r'^Title[:\s]+(.+)$',
            r'^#+\s+(.+)$',  # Markdown headers
            r'^\s*(.+)\s*\n={3,}',  # Underlined headers
        ]
        
        for line in first_lines:
            line = line.strip()
            if line:
                # Try patterns
                for pattern in patterns:
                    if match := re.match(pattern, line, re.IGNORECASE):
                        return match.group(1).strip()
                
                # If no pattern matches, first non-empty line might be title
                if len(line) > 20:  # Assume it's long enough to be a title
                    return line
        
        return "Untitled Document"

    @log_operation("extract_authors")
    async def _extract_authors(self, content: str) -> List[Dict]:
        """Extract author information."""
        authors = []
        
        # Look for author section
        author_section = self._find_section(content, ["authors", "author information"])
        if not author_section:
            return authors
            
        # Common patterns for author entries
        patterns = [
            r'([^,]+),?\s*([^,]+@[^\s,]+)',  # Name with email
            r'([^,]+),\s*([^,]+)',  # Name with affiliation
        ]
        
        lines = author_section.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                author_info = {"name": "", "email": "", "affiliation": ""}
                
                for pattern in patterns:
                    if match := re.match(pattern, line):
                        author_info["name"] = match.group(1).strip()
                        if '@' in match.group(2):
                            author_info["email"] = match.group(2).strip()
                        else:
                            author_info["affiliation"] = match.group(2).strip()
                
                if author_info["name"]:
                    authors.append(author_info)
        
        return authors

    @log_operation("extract_abstract")
    async def _extract_abstract(self, content: str) -> Optional[str]:
        """Extract paper abstract."""
        abstract_section = self._find_section(content, ["abstract"])
        if abstract_section:
            # Clean up the abstract
            lines = abstract_section.split('\n')
            clean_lines = []
            for line in lines[1:]:  # Skip the "Abstract" header
                if line.strip() and not line.lower().startswith(('keywords', 'index terms')):
                    clean_lines.append(line.strip())
            return ' '.join(clean_lines)
        return None

    @log_operation("extract_references")
    async def _extract_references(self, content: str) -> List[Dict]:
        """Extract paper references."""
        references = []
        ref_section = self._find_section(content, ["references", "bibliography"])
        
        if ref_section:
            # Split into individual references
            ref_entries = re.split(r'\[\d+\]|\d+\.', ref_section)
            
            for entry in ref_entries:
                if entry.strip():
                    ref = self._parse_reference(entry.strip())
                    if ref:
                        references.append(ref)
        
        return references

    @log_operation("extract_publication_info")
    async def _extract_publication_info(self, content: str) -> Dict:
        """Extract publication information."""
        info = {
            "journal": None,
            "year": None,
            "doi": None,
            "conference": None
        }
        
        # Look for DOI
        doi_match = re.search(r'doi:?\s*(10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+)', content)
        if doi_match:
            info["doi"] = doi_match.group(1)
        
        # Look for year
        year_match = re.search(r'\b(19|20)\d{2}\b', content)
        if year_match:
            info["year"] = int(year_match.group(0))
        
        # Look for journal/conference
        for line in content.split('\n'):
            if re.search(r'proceedings of|conference on', line, re.IGNORECASE):
                info["conference"] = line.strip()
                break
            elif re.search(r'journal|transactions on', line, re.IGNORECASE):
                info["journal"] = line.strip()
                break
        
        return info

    def _find_section(self, content: str, section_names: List[str]) -> Optional[str]:
        """Find a specific section in the content."""
        content_lower = content.lower()
        
        for name in section_names:
            # Try different section header patterns
            patterns = [
                rf'\n{name}[:\s]+(.+?)(?:\n\s*\n|\Z)',  # Regular section
                rf'\n[0-9]+\s+{name}[:\s]+(.+?)(?:\n\s*\n|\Z)',  # Numbered section
                rf'\n[A-Z]\s+{name}[:\s]+(.+?)(?:\n\s*\n|\Z)',  # Letter section
            ]
            
            for pattern in patterns:
                if match := re.search(pattern, content_lower, re.DOTALL | re.IGNORECASE):
                    return match.group(1).strip()
        
        return None

    def _parse_reference(self, ref_text: str) -> Optional[Dict]:
        """Parse individual reference entry."""
        if len(ref_text.strip()) < 10:  # Too short to be valid
            return None
            
        ref = {
            "text": ref_text.strip(),
            "authors": [],
            "title": None,
            "year": None
        }
        
        # Try to extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', ref_text)
        if year_match:
            ref["year"] = int(year_match.group(0))
        
        # Try to extract title (text between quotes or after year)
        title_match = re.search(r'"([^"]+)"', ref_text)
        if title_match:
            ref["title"] = title_match.group(1)
        elif year_match:
            # Take text after year as title
            parts = ref_text.split(str(ref["year"]))
            if len(parts) > 1:
                ref["title"] = parts[1].split('"')[0].strip()
        
        return ref