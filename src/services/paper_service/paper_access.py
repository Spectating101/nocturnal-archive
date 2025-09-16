"""
Enhanced paper access module with updated sources and better error handling
"""
import aiohttp
import asyncio
import re
import json
from typing import Dict, Optional, List, Union, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
import random
from urllib.parse import urlparse, urljoin
from ...utils.logger import logger, log_operation
import os

class PaperAccessManager:
    """Manages access to scientific papers through multiple sources"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.own_session = session is None
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        # Updated Sci-Hub mirrors (as of 2025)
        self.scihub_mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st", 
            "https://sci-hub.ru",
            "https://sci-hub.ren",
            "https://sci-hub.cat",
            "https://sci-hub.tw",
            "https://sci-hub.ee",
            "https://sci-hub.wf"
        ]
        
        # LibGen mirrors
        self.libgen_mirrors = [
            "https://libgen.is",
            "https://libgen.rs", 
            "https://libgen.st",
            "https://libgen.li"
        ]
        
        self.semantic_scholar_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        
        self.rate_limits = {
            "semantic_scholar": {"delay": 0.1, "last_request": datetime.min},
            "core": {"delay": 0.5, "last_request": datetime.min},
            "unpaywall": {"delay": 0.1, "last_request": datetime.min}
        }
    
    async def _handle_rate_limit(self, source: str):
        """Handle rate limiting for different sources"""
        if source not in self.rate_limits:
            return
            
        now = datetime.now()
        time_since_last = (now - self.rate_limits[source]["last_request"]).total_seconds()
        if time_since_last < self.rate_limits[source]["delay"]:
            await asyncio.sleep(self.rate_limits[source]["delay"] - time_since_last)
        self.rate_limits[source]["last_request"] = now
        
    def _get_headers(self, referer: str = "https://scholar.google.com/") -> Dict:
        """Get randomized headers to avoid detection"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Referer": referer,
            "Upgrade-Insecure-Requests": "1"
        }
        
    async def __aenter__(self):
        if self.own_session:
            timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.own_session and self.session:
            await self.session.close()
            self.session = None
    
    @log_operation("get_paper")
    async def get_paper(self, doi: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Main method to retrieve a paper given its DOI
        """
        logger.info(f"Attempting to retrieve paper with DOI: {doi}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.own_session = True
        
        # Methods to try in order
        methods = [
            ("open_access", self._try_open_access),
            ("unpaywall", self._try_unpaywall),
            ("semantic_scholar", self._try_semantic_scholar),  # NEW
            ("core", self._try_core),  # NEW
            ("arxiv", self._try_arxiv),
            ("pmc", self._try_pmc),
            ("preprints", self._try_preprint_servers),  # NEW
            ("direct_doi", self._try_direct_doi),
            ("scihub", self._try_scihub),
            ("libgen", self._try_libgen)
        ]
        
        errors = {}
        
        for method_name, method in methods:
            try:
                logger.info(f"Trying {method_name} for DOI: {doi}")
                content, format_type = await method(doi, metadata)
                
                if content and len(content) > 1000:  # Basic validation
                    logger.info(f"Successfully retrieved paper with {method_name}")
                    return {
                        "content": content,
                        "doi": doi,
                        "source": method_name,
                        "format": format_type,
                        "size": len(content)
                    }
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.warning(f"Error using {method_name}: {error_msg}")
                errors[method_name] = error_msg
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 3))
        
        logger.error(f"Failed to retrieve paper with DOI: {doi}")
        return {
            "content": None,
            "doi": doi,
            "source": None,
            "error": "All retrieval methods failed",
            "errors": errors
        }
    
    async def _try_open_access(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try to get paper from open access sources in metadata"""
        if not metadata:
            return None, "unknown"
            
        # Try open_access field
        if oa := metadata.get("open_access"):
            if url := oa.get("pdf_url") or oa.get("oa_url"):
                try:
                    headers = self._get_headers()
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            if content.startswith(b'%PDF'):
                                return content, "pdf"
                except Exception as e:
                    logger.debug(f"Open access URL failed: {e}")
        
        # Try primary location
        if location := metadata.get("primary_location"):
            if url := location.get("pdf_url"):
                try:
                    headers = self._get_headers()
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            if content.startswith(b'%PDF'):
                                return content, "pdf"
                except Exception as e:
                    logger.debug(f"Primary location failed: {e}")
        
        return None, "unknown"
    
    async def _try_unpaywall(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try Unpaywall API for open access papers"""
        await self._handle_rate_limit("unpaywall")
        email = os.getenv("OPENALEX_EMAIL", "test@example.com")
        url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
        
        try:
            headers = self._get_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for OA status
                    if data.get("is_oa"):
                        # Try best OA location
                        if best_oa := data.get("best_oa_location"):
                            if pdf_url := best_oa.get("url_for_pdf"):
                                logger.info(f"Found OA PDF via Unpaywall: {pdf_url}")
                                
                                async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                    if pdf_response.status == 200:
                                        content = await pdf_response.read()
                                        if content.startswith(b'%PDF'):
                                            return content, "pdf"
                        
                        # Try other OA locations
                        for location in data.get("oa_locations", []):
                            if pdf_url := location.get("url_for_pdf"):
                                try:
                                    async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                        if pdf_response.status == 200:
                                            content = await pdf_response.read()
                                            if content.startswith(b'%PDF'):
                                                return content, "pdf"
                                except:
                                    continue
                                    
        except Exception as e:
            logger.debug(f"Unpaywall failed: {e}")
        
        return None, "unknown"
    
    async def _try_arxiv(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try arXiv if the DOI indicates it's an arXiv paper"""
        # Check if DOI is from arXiv
        if "arxiv" in doi.lower():
            # Extract arXiv ID from DOI
            arxiv_match = re.search(r'(\d{4}\.\d{4,5})', doi)
            if arxiv_match:
                arxiv_id = arxiv_match.group(1)
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                try:
                    headers = self._get_headers("https://arxiv.org/")
                    async with self.session.get(pdf_url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            if content.startswith(b'%PDF'):
                                return content, "pdf"
                except Exception as e:
                    logger.debug(f"arXiv failed: {e}")
                    
        return None, "unknown"
    
    async def _try_pmc(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try PubMed Central for biomedical papers"""
        # Search PMC using DOI
        search_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={doi}&format=json"
        
        try:
            headers = self._get_headers("https://pubmed.ncbi.nlm.nih.gov/")
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if PMC ID exists
                    if records := data.get("records", []):
                        for record in records:
                            if pmcid := record.get("pmcid"):
                                # Try to get PDF from PMC
                                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                                
                                async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                    if pdf_response.status == 200:
                                        content = await pdf_response.read()
                                        if content.startswith(b'%PDF'):
                                            return content, "pdf"
        except Exception as e:
            logger.debug(f"PMC failed: {e}")
            
        return None, "unknown"
    
    async def _try_direct_doi(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try accessing the paper directly through the DOI resolution"""
        url = f"https://doi.org/{doi}"
        headers = self._get_headers()
        
        try:
            async with self.session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    return None, "unknown"
                
                # Check if direct download
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type:
                    content = await response.read()
                    if content.startswith(b'%PDF'):
                        return content, "pdf"
                
                # Parse HTML for PDF links
                if "text/html" in content_type:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Common PDF link patterns
                    pdf_patterns = [
                        lambda tag: tag.name == 'a' and tag.get('href', '').endswith('.pdf'),
                        lambda tag: tag.name == 'a' and '/pdf/' in tag.get('href', ''),
                        lambda tag: tag.name == 'a' and 'download' in tag.get('class', []),
                        lambda tag: tag.name == 'a' and 'pdf' in tag.text.lower()
                    ]
                    
                    for pattern in pdf_patterns:
                        for link in soup.find_all(pattern):
                            pdf_url = urljoin(str(response.url), link['href'])
                            
                            try:
                                async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                    if pdf_response.status == 200:
                                        content = await pdf_response.read()
                                        if content.startswith(b'%PDF'):
                                            return content, "pdf"
                            except:
                                continue
                                
        except Exception as e:
            logger.debug(f"Direct DOI failed: {e}")
        
        return None, "unknown"
    
    async def _try_scihub(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try Sci-Hub mirrors with improved detection avoidance"""
        # Randomize mirror order
        mirrors = random.sample(self.scihub_mirrors, len(self.scihub_mirrors))
        
        for mirror in mirrors:
            try:
                # Add delay between attempts
                await asyncio.sleep(random.uniform(2, 4))
                
                url = f"{mirror}/{doi}"
                headers = self._get_headers(mirror)
                
                # First request to get the page
                async with self.session.get(url, headers=headers, ssl=False) as response:
                    if response.status != 200:
                        continue
                    
                    # Read raw bytes once, check for PDF
                    raw = await response.read()
                    ct = response.headers.get("Content-Type", "")
                    if raw.startswith(b'%PDF') or "application/pdf" in ct.lower():
                        return raw, "pdf"
                    # Otherwise decode as HTML and parse
                    html = raw.decode("utf-8", errors="ignore")
                    
                    # Parse HTML for PDF URL
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try multiple patterns
                    pdf_url = None
                    
                    # Pattern 1: iframe
                    iframe = soup.find('iframe', {'id': 'pdf'})
                    if iframe and iframe.get('src'):
                        pdf_url = iframe['src']
                    
                    # Pattern 2: embed
                    if not pdf_url:
                        embed = soup.find('embed', {'type': 'application/pdf'})
                        if embed and embed.get('src'):
                            pdf_url = embed['src']
                    
                    # Pattern 3: button with onclick
                    if not pdf_url:
                        button = soup.find('button', {'onclick': re.compile(r'location\.href')})
                        if button:
                            onclick = button.get('onclick', '')
                            match = re.search(r"location\.href='([^']+)'", onclick)
                            if match:
                                pdf_url = match.group(1)
                    
                    if pdf_url:
                        # Handle relative URLs
                        if pdf_url.startswith('//'):
                            pdf_url = 'https:' + pdf_url
                        elif pdf_url.startswith('/'):
                            pdf_url = mirror + pdf_url
                        
                        # Download PDF
                        await asyncio.sleep(1)  # Small delay
                        async with self.session.get(pdf_url, headers=headers, ssl=False) as pdf_response:
                            if pdf_response.status == 200:
                                content = await pdf_response.read()
                                if content.startswith(b'%PDF'):
                                    return content, "pdf"
                                    
            except Exception as e:
                logger.debug(f"Sci-Hub mirror {mirror} failed: {e}")
                continue
        
        return None, "unknown"
    
    async def _try_libgen(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try Library Genesis with updated patterns"""
        mirrors = random.sample(self.libgen_mirrors, len(self.libgen_mirrors))
        
        for mirror in mirrors:
            try:
                timeout = aiohttp.ClientTimeout(total=30) 
                
                search_url = f"{mirror}/scimag/"
                headers = self._get_headers(mirror)
                data = {"doi": doi, "doiresolver": "Search"}
                async with self.session.post(search_url, data=data, headers=headers, ssl=False) as response:
                        if response.status != 200:
                            continue
                        
                        html = await response.text()
                        
                        # Check if found
                        if "not found" in html.lower():
                            continue
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find download links - LibGen structure
                        download_links = []
                        
                        # Look for links in the results table
                        for row in soup.find_all('tr'):
                            for link in row.find_all('a', href=True):
                                href = link['href']
                                if any(x in href for x in ['ads.php', 'get.php', 'doi=']):
                                    download_links.append(href)
                        
                        # Try each download link
                        for dl_link in download_links[:3]:  # Try first 3 links
                            try:
                                if not dl_link.startswith('http'):
                                    dl_link = urljoin(mirror, dl_link)
                                
                                # Get download page
                                await asyncio.sleep(random.uniform(1, 2))
                                async with self.session.get(dl_link, headers=headers, ssl=False) as dl_response:
                                    if dl_response.status != 200:
                                        continue
                                    
                                    dl_html = await dl_response.text()
                                    dl_soup = BeautifulSoup(dl_html, 'html.parser')
                                    
                                    # Find actual download link
                                    for link in dl_soup.find_all('a', href=True):
                                        href = link['href']
                                        if any(x in href.lower() for x in ['.pdf', 'download', 'get']):
                                            final_url = urljoin(str(dl_response.url), href)
                                            
                                            # Download file
                                            async with self.session.get(final_url, headers=headers, ssl=False) as pdf_response:
                                                if pdf_response.status == 200:
                                                    content = await pdf_response.read()
                                                    if len(content) > 1000:
                                                        return content, "pdf"
                            except:
                                continue
                                
            except Exception as e:
                logger.debug(f"LibGen mirror {mirror} failed: {e}")
                continue
        
        return None, "unknown"
    
    async def _try_semantic_scholar(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        await self._handle_rate_limit("semantic_scholar")  # Add this!
        """Try Semantic Scholar API for open access papers"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        params = {
            "fields": "title,abstract,authors,year,openAccessPdf,externalIds"
        }
        
        try:
            headers = self._get_headers()
            if self.semantic_scholar_key:
                headers["x-api-key"] = self.semantic_scholar_key
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for open access PDF
                    if oa_pdf := data.get("openAccessPdf"):
                        if pdf_url := oa_pdf.get("url"):
                            logger.info(f"Found OA PDF via Semantic Scholar: {pdf_url}")
                            
                            async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                if pdf_response.status == 200:
                                    content = await pdf_response.read()
                                    if content.startswith(b'%PDF'):
                                        return content, "pdf"
                                        
        except Exception as e:
            logger.debug(f"Semantic Scholar failed: {e}")
        
        return None, "unknown"

    async def _try_core(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try CORE.ac.uk API v3 for open access papers"""
        await self._handle_rate_limit("core")
        
        api_key = os.getenv("CORE_API_KEY")
        if not api_key:
            return None, "unknown"
        
        try:
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {api_key}"
            
            # Use CORE v3 API
            url = f"https://api.core.ac.uk/v3/search/works"
            params = {
                "q": f'doi:"{doi}"',
                "limit": 10
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we found results
                    if data.get("totalHits", 0) > 0:
                        for result in data.get("results", []):
                            # Look for download URL
                            if download_url := result.get("downloadUrl"):
                                logger.info(f"Found PDF via CORE v3: {download_url}")
                                
                                async with self.session.get(download_url, headers=self._get_headers()) as pdf_response:
                                    if pdf_response.status == 200:
                                        content = await pdf_response.read()
                                        if content.startswith(b'%PDF'):
                                            return content, "pdf"
                                            
        except Exception as e:
            logger.debug(f"CORE v3 failed: {e}")
        
        return None, "unknown"

    async def _try_preprint_servers(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try various preprint servers"""
        # Check if DOI suggests a preprint server
        doi_lower = doi.lower()
        
        # bioRxiv/medRxiv
        if "biorxiv" in doi_lower or "medrxiv" in doi_lower:
            # Extract ID from DOI
            match = re.search(r'(\d{4}\.\d{2}\.\d{2}\.\d+)', doi)
            if match:
                paper_id = match.group(1)
                pdf_url = f"https://www.biorxiv.org/content/{paper_id}v1.full.pdf"
                
                try:
                    headers = self._get_headers("https://www.biorxiv.org/")
                    async with self.session.get(pdf_url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            if content.startswith(b'%PDF'):
                                return content, "pdf"
                except Exception as e:
                    logger.debug(f"bioRxiv failed: {e}")
        
        # Add other preprint servers as needed
        return None, "unknown"