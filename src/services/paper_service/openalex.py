from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import asyncio
from datetime import datetime
import urllib.parse
import uuid
import aiofiles
from pathlib import Path
import re
from bs4 import BeautifulSoup
from ...utils.logger import logger, log_operation

class PaperRetrievalError(Exception):
    """Custom exception for paper retrieval errors."""
    pass

class OpenAlexClient:
    def __init__(self, email: Optional[str] = None, cache_dir: Optional[str] = None):
        logger.info("Initializing OpenAlexClient")
        self.base_url = "https://api.openalex.org"
        self.email = email
        self.session = None
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.rate_limits = {
            "openalex": {"delay": 1.0, "last_request": datetime.min},
            "scihub": {"delay": 3.0, "last_request": datetime.min},
            "unpaywall": {"delay": 0.1, "last_request": datetime.min},  # NEW
            "semantic_scholar": {"delay": 0.1, "last_request": datetime.min},  # NEW
            "core": {"delay": 0.5, "last_request": datetime.min},  # NEW
            "arxiv": {"delay": 3.0, "last_request": datetime.min},  # NEW
            "general": {"delay": 1.0, "last_request": datetime.min}
        }
        self.scihub_mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru"
        ]
        # Add the new rate limits
        logger.info("OpenAlexClient initialized")

    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()

    def _build_headers(self) -> Dict:
        """Build request headers."""
        headers = {
            "Accept": "application/json",
            "User-Agent": f"NocturnalArchive/0.1 ({self.email})" if self.email else "NocturnalArchive/0.1"
        }
        return headers

    async def _handle_rate_limit(self, source: str):
        """Handle rate limiting for different sources."""
        now = datetime.now()
        time_since_last = (now - self.rate_limits[source]["last_request"]).total_seconds()
        if time_since_last < self.rate_limits[source]["delay"]:
            await asyncio.sleep(self.rate_limits[source]["delay"] - time_since_last)
        self.rate_limits[source]["last_request"] = now

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict:
        """Make HTTP request with retries."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = self._build_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"API request failed after {max_retries} attempts: {str(e)}")
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Request failed, retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)

    def _build_filter_string(self, filters: Dict[str, Any]) -> str:
        """Build filter string for API request."""
        if not filters:
            return ""
            
        filter_parts = []
        for key, value in filters.items():
            if isinstance(value, list):
                value = '|'.join(str(v) for v in value)
            filter_parts.append(f"{key}:{value}")
        return ','.join(filter_parts)

    @log_operation("search_works")
    async def search_works(self, query: str, filters: Dict = None, page: int = 1, per_page: int = 25) -> Dict:
        """Search for academic works."""
        logger.info(f"Searching works with query: {query}")
        await self._handle_rate_limit("openalex")
        
        params = {
            "search": query,
            "page": page,
            "per-page": per_page,
        }
        
        # Only add filter if it's not None
        if filters:
            params["filter"] = self._build_filter_string(filters)
        
        url = f"{self.base_url}/works"
        results = await self._make_request("GET", url, params=params)
        
        # Enrich results with availability information
        if results.get("results"):
            for paper in results["results"]:
                paper["availability"] = await self._check_availability(paper)
        
        return results

    @log_operation("get_work")
    async def get_work(self, work_id: str) -> Dict:
        """Get details of a specific work."""
        logger.info(f"Fetching work details: {work_id}")
        await self._handle_rate_limit("openalex")
        url = f"{self.base_url}/works/{work_id}"
        return await self._make_request("GET", url)

    @log_operation("get_authors")
    async def get_authors(self, work_id: str) -> List[Dict]:
        """Get authors of a specific work."""
        logger.info(f"Fetching authors for work: {work_id}")
        work = await self.get_work(work_id)
        return work.get("authorships", [])

    @log_operation("get_references")
    async def get_references(self, work_id: str, page: int = 1, per_page: int = 25) -> Dict:
        """Get references of a specific work."""
        logger.info(f"Fetching references for work: {work_id}")
        await self._handle_rate_limit("openalex")
        url = f"{self.base_url}/works/{work_id}/referenced_works"
        params = {"page": page, "per-page": per_page}
        return await self._make_request("GET", url, params=params)

    @log_operation("get_citing_works")
    async def get_citing_works(self, work_id: str, page: int = 1, per_page: int = 25) -> Dict:
        """Get works citing a specific work."""
        logger.info(f"Fetching citing works for: {work_id}")
        await self._handle_rate_limit("openalex")
        url = f"{self.base_url}/works/{work_id}/citing_works"
        params = {"page": page, "per-page": per_page}
        return await self._make_request("GET", url, params=params)

    @log_operation("get_related_works")
    async def get_related_works(self, work_id: str, page: int = 1, per_page: int = 25) -> Dict:
        """Get works related to a specific work."""
        logger.info(f"Fetching related works for: {work_id}")
        await self._handle_rate_limit("openalex")
        url = f"{self.base_url}/works/{work_id}/related_works"
        params = {"page": page, "per-page": per_page}
        return await self._make_request("GET", url, params=params)

    @log_operation("get_full_text")
    async def get_full_text(self, work_id: str, prefer_source: str = "any") -> Optional[Dict]:
        """Try to get full text of paper from various sources."""
        logger.info(f"Attempting to retrieve full text for: {work_id}")
        
        work = await self.get_work(work_id)
        doi = work.get("doi")
        
        if not doi:
            logger.warning(f"No DOI found for work {work_id}")
            return None
            
        # Use the PaperAccessManager for retrieval
        from .paper_access import PaperAccessManager
        
        async with PaperAccessManager(self.session) as manager:
            result = await manager.get_paper(doi, work)
            
            if result.get("content"):
                return {
                    "content": result["content"],
                    "source": result["source"],
                    "format": result.get("format", "unknown"),
                    "work_id": work_id,
                    "doi": doi
                }
        
        return None

    async def _try_open_access(self, work: Dict, doi: Optional[str]) -> Optional[bytes]:
        """Try to get paper from open access sources."""
        await self._handle_rate_limit("general")
        
        if oa := work.get("open_access"):
            if url := oa.get("pdf_url"):
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.read()
                except Exception as e:
                    logger.error(f"Error accessing open access URL: {str(e)}")
        return None

    async def _try_repository(self, work: Dict, doi: Optional[str]) -> Optional[bytes]:
        """Try to get paper from institutional repositories."""
        await self._handle_rate_limit("general")
        
        if location := work.get("primary_location"):
            if url := location.get("pdf_url"):
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.read()
                except Exception as e:
                    logger.error(f"Error accessing repository: {str(e)}")
        return None

    async def _try_direct_doi(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try accessing the paper directly through the DOI resolution"""
        logger.info(f"Trying direct DOI resolution for: {doi}")
        
        url = f"https://doi.org/{doi}"
        headers = {
            "User-Agent": "NocturnalArchive/0.1", 
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://google.com/"
        }
        
        try:
            async with self.session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    logger.warning(f"DOI resolution failed with status: {response.status}")
                    return None, "unknown"
                
                # Try to get the content directly
                content = await response.read()
                content_type = response.headers.get("Content-Type", "")
                
                # If it's a PDF, return it
                if content_type.lower() == "application/pdf" or content.startswith(b'%PDF'):
                    return content, "pdf"
                
                # If it's HTML, check for PDF links
                if "text/html" in content_type.lower():
                    html_content = content.decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Look for PDF links
                    pdf_links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href'].lower()
                        if href.endswith('.pdf') or '/pdf/' in href:
                            pdf_links.append(a['href'])
                    
                    # Try each PDF link
                    for pdf_url in pdf_links:
                        # Handle relative URLs
                        if not pdf_url.startswith(('http://', 'https://')):
                            pdf_url = urllib.parse.urljoin(str(response.url), pdf_url)
                        
                        try:
                            logger.info(f"Trying PDF link: {pdf_url}")
                            async with self.session.get(pdf_url, headers=headers) as pdf_response:
                                if pdf_response.status == 200:
                                    pdf_content = await pdf_response.read()
                                    if len(pdf_content) > 1000 and (pdf_response.headers.get("Content-Type", "").lower() == "application/pdf" or pdf_content.startswith(b'%PDF')):
                                        return pdf_content, "pdf"
                        except Exception as e:
                            logger.warning(f"Error accessing PDF link {pdf_url}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error with direct DOI resolution: {str(e)}")
        
        return None, "unknown"

    async def _try_scihub(self, work: Dict, doi: Optional[str]) -> Optional[bytes]:
        """Try to get paper from Sci-Hub."""
        if not doi:
            return None
            
        await self._handle_rate_limit("scihub")
        
        # Update mirrors list
        self.scihub_mirrors = [
            "https://sci-hub.ru",
            "https://sci-hub.st", 
            "https://sci-hub.wf",
            "https://sci-hub.se",
            "https://sci-hub.ee",
            "https://sci-hub.ren",
            "https://sci-hub.cat",
            "https://sci-hub.yt"
        ]
        
        # Add better headers to avoid blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://google.com/"
        }
        
        for mirror in self.scihub_mirrors:
            try:
                url = f"{mirror}/{doi}"
                async with self.session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Check if it's a PDF directly
                        if content.startswith(b'%PDF'):
                            return content
                            
                        # Try to parse HTML for PDF iframe or link
                        try:
                            html_content = content.decode('utf-8', errors='ignore')
                            
                            # Use regex to find PDF iframe
                            pdf_match = re.search(r'<iframe[^>]*src="([^"]+\.pdf[^"]*)"', html_content)
                            if pdf_match:
                                pdf_url = pdf_match.group(1)
                                # Fix relative URLs
                                if not pdf_url.startswith(('http://', 'https://')):
                                    if pdf_url.startswith('//'):
                                        pdf_url = 'https:' + pdf_url
                                    else:
                                        pdf_url = f"{mirror}/{pdf_url.lstrip('/')}"
                                
                                # Download the actual PDF
                                async with self.session.get(pdf_url, timeout=30) as pdf_response:
                                    if pdf_response.status == 200:
                                        return await pdf_response.read()
                        except Exception as e:
                            logger.warning(f"Error parsing Sci-Hub HTML: {str(e)}")
                        
                        # Return the HTML content if it's substantial
                        if len(content) > 50000:
                            return content
            except Exception as e:
                logger.warning(f"Sci-Hub mirror {mirror} failed: {str(e)}")
                continue
        
        # If Sci-Hub fails, try LibGen
        return await self._try_libgen(doi)

    async def _try_core(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try CORE.ac.uk academic repository"""
        logger.info(f"Trying CORE for DOI: {doi}")
        try:
            # Search CORE by DOI
            search_url = f"https://core.ac.uk/search?q={doi}"
            params = {"q": doi}
            async with self.session.get(search_url, headers=self._build_headers(), params=params) as response:
                if response.status != 200:
                    return None, "unknown"
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for download links
                for a in soup.find_all('a', href=True):
                    if 'download/pdf' in a['href'].lower():
                        pdf_url = a['href']
                        if not pdf_url.startswith('http'):
                            pdf_url = 'https://core.ac.uk' + pdf_url
                            
                        async with self.session.get(pdf_url, headers=self._build_headers()) as pdf_response:
                            if pdf_response.status == 200:
                                content = await pdf_response.read()
                                if len(content) > 1000:
                                    return content, "pdf"
        except Exception as e:
            logger.error(f"Error with CORE: {str(e)}")
            
        return None, "unknown"

    async def _get_fallback_content(self, doi: str) -> Dict:
        """Get metadata when full text isn't available"""
        try:
            # Try CrossRef API
            url = f"https://api.crossref.org/works/{doi}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("message"):
                        msg = data["message"]
                        return {
                            "title": msg.get("title", ["Unknown"])[0],
                            "abstract": msg.get("abstract", "No abstract available"),
                            "authors": [a.get("family", "") + ", " + a.get("given", "") 
                                    for a in msg.get("author", [])],
                            "doi": doi,
                            "year": msg.get("published-print", {}).get("date-parts", [[0]])[0][0],
                            "source": "crossref_metadata"
                        }
        except Exception as e:
            logger.error(f"Error getting fallback content: {str(e)}")
        
        return {"error": "No content available", "doi": doi}


    async def _try_libgen(self, doi: str, metadata: Optional[Dict] = None) -> Tuple[Optional[bytes], str]:
        """Try Library Genesis for the paper with improved pattern matching"""
        logger.info(f"Trying LibGen for DOI: {doi}")
        
        # LibGen uses different domains - try multiple
        libgen_domains = [
            "https://libgen.is",
            "https://libgen.rs",
            "https://libgen.st",
            "https://libgen.li"
        ]
        
        # Enhanced headers to avoid blocking
        headers = {
            "User-Agent": "NocturnalArchive/0.1", 
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://google.com/"
        }
        
        for domain in libgen_domains:
            search_url = f"{domain}/scimag/"
            
            # Prepare POST data
            data = {
                "doi": doi,
                "doiresolver": "Search"
            }
            
            try:
                # Step 1: Search for the DOI
                async with self.session.post(search_url, data=data, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"LibGen domain {domain} returned status {response.status}")
                        continue
                    
                    content = await response.text()
                    
                    # Check if paper is found
                    if "DOI not found" in content or "not found" in content.lower():
                        logger.info(f"Paper not found in LibGen at {domain}: {doi}")
                        continue
                    
                    # Save HTML for debugging
                    with open(f"libgen_response_{doi.replace('/', '_')}.html", "w") as f:
                        f.write(content)
                        
                    logger.info(f"Found paper in LibGen at {domain}")
                    
                    # Try multiple pattern matching approaches
                    # Approach 1: Use BeautifulSoup for more robust parsing
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for common LibGen patterns
                    download_links = []
                    
                    # Find links with 'doi' in href
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if 'doi=' in href or '/scimag/' in href:
                            download_links.append(href)
                    
                    if not download_links:
                        # Try regex as fallback
                        pattern_candidates = [
                            r'href="(\/scimag\/ads\.php\?doi=[^"]+)"',
                            r'href="(\/scimag\/[^"]+doi=[^"]+)"',
                            r'href="([^"]*\?doi=[^"]+)"'
                        ]
                        
                        for pattern in pattern_candidates:
                            matches = re.findall(pattern, content)
                            if matches:
                                download_links.extend(matches)
                                break
                    
                    if not download_links:
                        logger.warning(f"No download links found in LibGen response")
                        continue
                    
                    # Try each download link
                    for download_path in download_links:
                        # Fix relative URLs
                        if not download_path.startswith(('http://', 'https://')):
                            download_url = f"{domain}{download_path}" if download_path.startswith('/') else f"{domain}/{download_path}"
                        else:
                            download_url = download_path
                        
                        logger.info(f"Trying download URL: {download_url}")
                        
                        try:
                            async with self.session.get(download_url, headers=headers, allow_redirects=True) as download_response:
                                if download_response.status != 200:
                                    logger.warning(f"Failed to access download page: {download_response.status}")
                                    continue
                                
                                download_page = await download_response.text()
                                
                                # Save for debugging
                                with open(f"libgen_download_{doi.replace('/', '_')}.html", "w") as f:
                                    f.write(download_page)
                                
                                # Step 4: Extract all possible download links
                                soup = BeautifulSoup(download_page, 'html.parser')
                                final_links = []
                                
                                # Look for download buttons or links
                                for a in soup.find_all('a', href=True):
                                    href = a['href']
                                    if any(ext in href.lower() for ext in ['.pdf', '.epub', '.djvu']):
                                        final_links.append(href)
                                
                                # If no links found with BeautifulSoup, try regex
                                if not final_links:
                                    patterns = [
                                        r'href="(https?:\/\/[^"]+\.pdf[^"]*)"',
                                        r'href="(https?:\/\/[^"]+\/[^"]+\/[^"]+)"',
                                        r'href="(https?:\/\/[^"]+download[^"]*)"'
                                    ]
                                    
                                    for pattern in patterns:
                                        matches = re.findall(pattern, download_page)
                                        if matches:
                                            final_links.extend(matches)
                                
                                # Try each final link
                                for final_url in final_links:
                                    logger.info(f"Attempting to download from: {final_url}")
                                    
                                    try:
                                        async with self.session.get(final_url, headers=headers, timeout=60) as pdf_response:
                                            if pdf_response.status != 200:
                                                logger.warning(f"Failed to download from {final_url}: {pdf_response.status}")
                                                continue
                                            
                                            content = await pdf_response.read()
                                            
                                            if len(content) < 1000:
                                                logger.warning(f"Downloaded content too small: {len(content)} bytes")
                                                continue
                                            
                                            # Check if it's a PDF
                                            is_pdf = content.startswith(b'%PDF')
                                            format_type = "pdf" if is_pdf else "unknown"
                                            
                                            logger.info(f"Successfully downloaded from LibGen: {len(content)} bytes, format: {format_type}")
                                            return content, format_type
                                    
                                    except Exception as e:
                                        logger.error(f"Error downloading from {final_url}: {str(e)}")
                                        continue
                        
                        except Exception as e:
                            logger.error(f"Error with download page {download_url}: {str(e)}")
                            continue
            
            except Exception as e:
                logger.error(f"Error with LibGen domain {domain}: {str(e)}")
                continue
        
        logger.warning("All LibGen attempts failed")
        return None, "unknown"

    async def _check_availability(self, paper: Dict) -> Dict:
        """Check paper availability through different sources."""
        doi = paper.get("doi")
        availability = {
            "open_access": paper.get("open_access", {}).get("is_oa", False),
            "repository": bool(paper.get("primary_location", {}).get("pdf_url")),
            "scihub": await self._check_scihub_availability(doi) if doi else False,
            "corresponding_author": self._get_corresponding_author(paper)
        }
        return availability

    async def _check_scihub_availability(self, doi: str) -> bool:
        """Check if paper is available on Sci-Hub without downloading."""
        if not doi:
            return False
            
        await self._handle_rate_limit("scihub")
        
        for mirror in self.scihub_mirrors:
            try:
                url = f"{mirror}/{doi}"
                async with self.session.head(url) as response:
                    return response.status == 200
            except:
                continue
        return False

    def _get_corresponding_author(self, paper: Dict) -> Optional[Dict]:
        """Extract corresponding author information."""
        for author in paper.get("authorships", []):
            if author.get("is_corresponding"):
                return {
                    "name": author.get("author", {}).get("display_name"),
                    "email": author.get("raw_author_string", "").split("email:")[-1].strip()
                    if "email:" in author.get("raw_author_string", "") else None
                }
        return None


class OpenAlexManager:
    def __init__(self, email: Optional[str] = None, cache_dir: Optional[str] = None):
        logger.info("Initializing OpenAlexManager")
        self.client = OpenAlexClient(email, cache_dir)
        self.active_searches: Dict[str, Dict] = {}
        logger.info("OpenAlexManager initialized")

    @log_operation("search_papers")
    async def search_papers(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search for papers and format results."""
        logger.info(f"Searching papers: {query}")
        async with self.client:
            results = await self.client.search_works(query, filters)
            return await self._format_results(results)

    @log_operation("get_paper_details")
    async def get_paper_details(self, work_id: str) -> Dict:
        """Get comprehensive paper details."""
        logger.info(f"Fetching paper details: {work_id}")
        async with self.client:
            # Fetch basic work details
            work = await self.client.get_work(work_id)
            
            # Fetch additional information
            references = await self.client.get_references(work_id)
            citing_works = await self.client.get_citing_works(work_id)
            
            # Try to get full text
            full_text = await self.client.get_full_text(work_id)
            
            # Combine all information
            details = {
                "work": work,
                "references": references.get("results", []),
                "citations": citing_works.get("results", []),
                "citation_count": work.get("cited_by_count", 0),
                "fields_of_study": work.get("concepts", []),
                "full_text": full_text
            }
            
            return details

    @log_operation("get_citation_network")
    async def get_citation_network(self, work_id: str, depth: int = 1) -> Dict:
        """Get citation network for a paper."""
        logger.info(f"Building citation network for {work_id} with depth {depth}")
        
        network = {
            "nodes": {},
            "edges": [],
            "stats": {
                "total_papers": 0,
                "total_citations": 0,
                "max_depth": depth
            }
        }
        
        async with self.client:
            await self._build_network(work_id, network, current_depth=0, max_depth=depth)
            
        network["stats"]["total_papers"] = len(network["nodes"])
        network["stats"]["total_citations"] = len(network["edges"])
        
        logger.info(f"Completed citation network with {len(network['nodes'])} nodes")
        return network

    @log_operation("start_thorough_search")
    async def start_thorough_search(self, query: str, depth: int = 2) -> str:
        """Start a thorough, long-running search process."""
        search_id = str(uuid.uuid4())
        self.active_searches[search_id] = {
            "status": "running",
            "query": query,
            "depth": depth,
            "start_time": datetime.now(),
            "results": []
        }
        
        # Start background task
        asyncio.create_task(self._conduct_thorough_search(search_id))
        return search_id

    @log_operation("get_search_status")
    async def get_search_status(self, search_id: str) -> Dict:
        """Get status of a long-running search."""
        if search_id not in self.active_searches:
            return {"status": "not_found"}
            
        search = self.active_searches[search_id]
        return {
            "status": search["status"],
            "query": search["query"],
            "found_papers": len(search["results"]),
            "runtime": (datetime.now() - search["start_time"]).total_seconds(),
            "depth": search["depth"]
        }

    async def _conduct_thorough_search(self, search_id: str):
        """Perform thorough search with retries and citation following."""
        search = self.active_searches[search_id]
        logger.info(f"Starting thorough search {search_id} for: {search['query']}")
        
        discovered = set()
        to_process = []

        try:
            async with self.client:
                # Initial search
                initial_results = await self.search_papers(search["query"])
                to_process.extend((paper["id"], 0) for paper in initial_results)
                
                while to_process:
                    paper_id, current_depth = to_process.pop(0)
                    
                    if paper_id in discovered or current_depth >= search["depth"]:
                        continue
                        
                    discovered.add(paper_id)
                    
                    # Get details with retries
                    details = await self._get_with_retry(
                        self.get_paper_details, paper_id, max_retries=3
                    )
                    
                    if details:
                        self.active_searches[search_id]["results"].append(details)
                        
                        if current_depth < search["depth"]:
                            # Add references and citations
                            new_papers = [
                                (p["id"], current_depth + 1)
                                for p in (details.get("references", []) + details.get("citations", []))
                                if p["id"] not in discovered
                            ]
                            to_process.extend(new_papers)
                    
                    await asyncio.sleep(1)  # Rate limiting
                
            self.active_searches[search_id]["status"] = "completed"
            logger.info(f"Completed thorough search {search_id}, found {len(discovered)} papers")
            
        except Exception as e:
            logger.error(f"Error in thorough search {search_id}: {str(e)}")
            self.active_searches[search_id]["status"] = "error"
            self.active_searches[search_id]["error"] = str(e)

    async def _build_network(self, work_id: str, network: Dict, current_depth: int, max_depth: int):
        """Recursively build citation network."""
        if current_depth > max_depth or work_id in network["nodes"]:
            return

        try:
            # Get work details
            work = await self.client.get_work(work_id)
            
            # Add node
            network["nodes"][work_id] = {
                "title": work.get("title"),
                "year": work.get("publication_year"),
                "authors": [author["author"]["display_name"] for author in work.get("authorships", [])],
                "citation_count": work.get("cited_by_count", 0),
                "depth": current_depth
            }
            
            if current_depth < max_depth:
                # Get references and citations
                references = await self.client.get_references(work_id)
                citing_works = await self.client.get_citing_works(work_id)
                
                # Process references
                for ref in references.get("results", []):
                    ref_id = ref.get("id")
                    if ref_id:
                        network["edges"].append({
                            "source": work_id,
                            "target": ref_id,
                            "type": "references"
                        })
                        await self._build_network(ref_id, network, current_depth + 1, max_depth)
                
                # Process citing works
                for citing in citing_works.get("results", []):
                    citing_id = citing.get("id")
                    if citing_id:
                        network["edges"].append({
                            "source": citing_id,
                            "target": work_id,
                            "type": "cites"
                        })
                        await self._build_network(citing_id, network, current_depth + 1, max_depth)
                
        except Exception as e:
            logger.error(f"Error building network for {work_id}: {str(e)}")

    async def _get_with_retry(self, func, *args, max_retries=3, **kwargs):
        """Execute function with retries."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {func.__name__}: {str(e)}")
                    return None
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed, waiting {wait_time}s")
                await asyncio.sleep(wait_time)

    async def _format_results(self, results: Dict) -> List[Dict]:
        """Format search results."""
        formatted = []
        for work in results.get("results", []):
            formatted.append({
                "id": work.get("id"),
                "title": work.get("title"),
                "abstract": work.get("abstract"),
                "authors": [author["author"]["display_name"] for author in work.get("authorships", [])],
                "year": work.get("publication_year"),
                "journal": work.get("primary_location", {}).get("source", {}).get("display_name"),
                "doi": work.get("doi"),
                "citation_count": work.get("cited_by_count", 0),
                "type": work.get("type"),
                "open_access": work.get("open_access", {}).get("is_oa", False)
            })
        return formatted