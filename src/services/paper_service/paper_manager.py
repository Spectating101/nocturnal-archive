import asyncio
from datetime import datetime
import uuid
from typing import Dict, List, Optional

from ...utils.logger import logger, log_operation
from ...storage.db.operations import DatabaseOperations
from ...storage.db.models import Paper, ProcessedPaper, TextChunk
from ..search_service.vector_search import VectorSearchEngine
from ..llm_service.embeddings import EmbeddingManager

class PaperManager:
    def __init__(self, db_ops: DatabaseOperations):
        logger.info("Initializing PaperManager")
        self.db = db_ops
        self.processing_queue = asyncio.Queue()
        self.vector_search = VectorSearchEngine()
        self.embedder = EmbeddingManager()
        logger.info("PaperManager initialized successfully")

    @log_operation("add_paper")
    async def add_paper(self, content: bytes, filename: str, content_type: str) -> str:
        """Add a new paper to the system."""
        paper_id = str(uuid.uuid4())
        logger.info(f"Adding new paper: {filename} (ID: {paper_id})")
        
        # Create paper metadata
        paper = Paper(
            id=paper_id,
            filename=filename,
            content_type=content_type,
            size=len(content),
            created_at=datetime.utcnow(),
            status="pending"
        )
        
        # Store paper in database
        logger.debug(f"Storing paper metadata in database: {paper_id}")
        await self.db.store_paper(paper)
        
        # Queue for processing
        logger.debug(f"Queueing paper for processing: {paper_id}")
        await self.processing_queue.put({
            "id": paper_id,
            "content": content,
            "metadata": paper.dict()
        })
        
        logger.info(f"Successfully added paper: {paper_id}")
        return paper_id

    @log_operation("get_paper_status")
    async def get_paper_status(self, paper_id: str) -> Optional[Dict]:
        """Get the current status of a paper."""
        logger.debug(f"Fetching status for paper: {paper_id}")
        return await self.db.get_paper_status(paper_id)

    @log_operation("get_paper_content")
    async def get_paper_content(self, paper_id: str) -> Optional[ProcessedPaper]:
        """Get the processed content of a paper."""
        logger.debug(f"Fetching content for paper: {paper_id}")
        return await self.db.get_processed_paper(paper_id)

    @log_operation("process_papers")
    async def process_papers(self):
        """Process papers in the queue."""
        logger.info("Starting paper processing loop")
        while True:
            paper_data = await self.processing_queue.get()
            logger.info(f"Processing paper: {paper_data['id']}")
            try:
                # Send to Rust document processor
                logger.debug("Sending to document processor")
                processed_doc = await self._process_document(paper_data)
                
                # Update database with processed content
                logger.debug("Updating database with processed content")
                await self.db.update_processed_paper(processed_doc)
                
                # Update paper status
                logger.debug("Updating paper status to 'processed'")
                await self.db.update_paper_status(
                    paper_data["id"],
                    "processed"
                )
                logger.info(f"Successfully processed paper: {paper_data['id']}")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper_data['id']}: {str(e)}")
                await self.db.update_paper_status(
                    paper_data["id"],
                    "error"
                )
            finally:
                self.processing_queue.task_done()

    async def _process_document(self, paper_data: Dict) -> ProcessedPaper:
        """Interface with Rust document processor."""
        logger.debug(f"Processing document through Rust service: {paper_data['id']}")
        # Placeholder: simple chunking & vector indexing
        content: bytes = paper_data["content"]
        text = content.decode(errors="ignore")
        raw_chunks = [t.strip() for t in text.split('\n\n') if t.strip()]
        chunks: List[TextChunk] = []
        for idx, ch in enumerate(raw_chunks[:50]):
            meta = {"chunk": idx, **paper_data["metadata"]}
            try:
                await self.vector_search.index_text(paper_data["id"], ch, meta)
            except Exception:
                pass
            chunks.append(TextChunk(content=ch[:2000], index=idx, metadata=meta))
        return ProcessedPaper(
            id=paper_data["id"],
            content=text[:20000],
            chunks=chunks,
            metadata=paper_data["metadata"]
        )
    # Add to src/services/paper_service/paper_manager.py

    async def fetch_web_content(self, url):
        """Fetch and extract content from a web URL"""
        import aiohttp
        from bs4 import BeautifulSoup
        import trafilatura
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return {"error": f"Failed to fetch URL: {response.status}"}
                    
                    html = await response.text()
            
            # Extract main content using trafilatura (best for article extraction)
            content = trafilatura.extract(html)
            
            # Fallback to BeautifulSoup if trafilatura fails
            if not content:
                soup = BeautifulSoup(html, 'html.parser')
                # Remove scripts, styles, etc.
                for tag in soup(["script", "style", "footer", "nav"]):
                    tag.decompose()
                content = soup.get_text(separator='\n')
            
            # Clean up content
            content = self._clean_content(content)
            
            # Extract title
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.string if soup.title else url
            
            return {
                "title": title.strip(),
                "content": content,
                "url": url
            }
        
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return {"error": str(e), "url": url}
        
    def _clean_content(self, content):
        """Clean up extracted content"""
        if not content:
            return ""
        
        # Basic cleaning
        import re
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove very short lines
        content = '\n'.join([line for line in content.split('\n') if len(line.strip()) > 30])
        # Limit length
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        return content