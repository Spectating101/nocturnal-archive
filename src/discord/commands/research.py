from typing import Dict, Optional
import asyncio
from pathlib import Path

from ...services.paper_service.paper_manager import PaperManager
from ...services.llm_service.llm_manager import LLMManager

class ResearchCommandHandler:
    def __init__(self, paper_manager: PaperManager, llm_manager: LLMManager):
        self.paper_manager = paper_manager
        self.llm_manager = llm_manager
        self.active_sessions: Dict[str, Dict] = {}  # user_id -> research context

    async def start_research(self, user_id: str, topic: str) -> str:
        """Start a new research session."""
        self.active_sessions[user_id] = {
            "topic": topic,
            "papers": [],
            "current_context": None
        }
        return f"Research session started for topic: {topic}"

    async def process_paper(self, user_id: str, file_path: Path) -> str:
        """Process a new paper for research."""
        if user_id not in self.active_sessions:
            return "No active research session. Start one with /research topic"

        try:
            content = await self._read_file(file_path)
            paper_id = await self.paper_manager.add_paper(
                content=content,
                filename=file_path.name,
                content_type=self._get_content_type(file_path)
            )
            
            self.active_sessions[user_id]["papers"].append(paper_id)
            return f"Paper queued for processing. ID: {paper_id}"
        
        except Exception as e:
            return f"Error processing paper: {str(e)}"

    async def get_summary(self, user_id: str, paper_id: Optional[str] = None) -> str:
        """Get summary of a paper or current research."""
        if paper_id:
            return await self._get_paper_summary(paper_id)
        
        if user_id not in self.active_sessions:
            return "No active research session."
            
        # Get summary of all papers in session
        summaries = []
        for pid in self.active_sessions[user_id]["papers"]:
            summary = await self._get_paper_summary(pid)
            summaries.append(summary)
            
        return "\n\n".join(summaries)

    async def ask_question(self, user_id: str, question: str) -> str:
        """Ask a question about the research."""
        if user_id not in self.active_sessions:
            return "No active research session."

        papers = self.active_sessions[user_id]["papers"]
        if not papers:
            return "No papers in current session."

        # Query LLM for each paper and combine results
        responses = []
        for paper_id in papers:
            response = await self.llm_manager.query_document(paper_id, question)
            responses.append(response)

        # Synthesize responses
        synthesis_prompt = f"Question: {question}\n\nFindings from papers:\n" + "\n".join(responses)
        final_response = await self.llm_manager.generate_summary(synthesis_prompt)
        return final_response

    async def find_similar(self, query: str, limit: int = 5) -> str:
        """Find similar content across processed papers."""
        results = await self.llm_manager.search_similar(query, k=limit)
        if not results:
            return "No similar content found."
            
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"{i}. {result['content'][:200]}...")
            
        return "\n\n".join(formatted_results)

    async def _get_paper_summary(self, paper_id: str) -> str:
        """Get summary for a specific paper."""
        paper = await self.paper_manager.get_paper_content(paper_id)
        if not paper:
            return f"Paper {paper_id} not found or still processing."
            
        return paper.content

    @staticmethod
    async def _read_file(path: Path) -> bytes:
        """Read file content."""
        return await asyncio.to_thread(lambda: path.read_bytes())

    @staticmethod
    def _get_content_type(path: Path) -> str:
        """Determine content type from file extension."""
        ext = path.suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
        }
        return content_types.get(ext, 'application/octet-stream')