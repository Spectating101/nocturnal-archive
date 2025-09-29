"""
Vertikal Unified - Terminal assistant connected to unified platform
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

class VertikalUnified:
    """
    Vertikal terminal assistant connected to the unified platform
    Provides access to FinSight, Archive, and enhanced R/SQL assistance
    """
    
    def __init__(self, project_root: str = ".", platform_url: str = "http://localhost:8000", api_key: str = None):
        """Initialize Vertikal with unified platform connection"""
        self.project_root = Path(project_root).resolve()
        self.platform_url = platform_url.rstrip('/')
        self.api_key = api_key or os.getenv("UNIFIED_API_KEY")
        self.session = None
        
        # Validate project root
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")
        
        console.print(f"🤖 [bold blue]Vertikal Unified[/bold blue] - Connected to platform at {self.platform_url}")
        console.print(f"📁 Project root: {self.project_root}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to unified platform"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.platform_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        try:
            if data:
                async with self.session.post(url, json=data, headers=headers) as response:
                    result = await response.json()
                    if response.status != 200:
                        return {"success": False, "error": result.get("detail", "Unknown error")}
                    return result
            else:
                async with self.session.get(url, headers=headers) as response:
                    result = await response.json()
                    if response.status != 200:
                        return {"success": False, "error": result.get("detail", "Unknown error")}
                    return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # === FILE OPERATIONS ===
    
    def list_files(self, directory: str = ".") -> str:
        """List files in directory"""
        try:
            target_path = self._validate_path(directory)
            if not target_path.exists():
                return f"❌ Directory not found: {directory}"
            
            if not target_path.is_dir():
                return f"❌ Not a directory: {directory}"
            
            files = []
            for item in target_path.iterdir():
                if item.is_file():
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({size:,} bytes)")
                elif item.is_dir():
                    files.append(f"📁 {item.name}/")
            
            if not files:
                return f"📁 Directory is empty: {directory}"
            
            return f"📁 Contents of {directory}:\n" + "\n".join(sorted(files))
            
        except Exception as e:
            return f"❌ Error listing files: {e}"
    
    def read_file(self, filepath: str, lines: int = 50) -> str:
        """Read file with preview"""
        try:
            target_path = self._validate_path(filepath)
            if not target_path.exists():
                return f"❌ File not found: {filepath}"
            
            if not target_path.is_file():
                return f"❌ Not a file: {filepath}"
            
            # File size limit (5MB)
            file_size = target_path.stat().st_size
            if file_size > 5 * 1024 * 1024:  # 5MB
                return f"❌ File too large: {file_size / (1024*1024):.1f}MB (max 5MB)"
            
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Show preview if file is large
            if len(content.split('\n')) > lines:
                lines_list = content.split('\n')
                preview = '\n'.join(lines_list[:lines])
                return f"📄 {filepath} (showing first {lines} lines):\n\n{preview}\n\n... ({len(lines_list) - lines} more lines)"
            else:
                return f"📄 {filepath}:\n\n{content}"
                
        except Exception as e:
            return f"❌ Error reading file: {e}"
    
    def search_files(self, query: str, directory: str = ".") -> str:
        """Search for files containing query"""
        try:
            target_path = self._validate_path(directory)
            if not target_path.exists():
                return f"❌ Directory not found: {directory}"
            
            matches = []
            for file_path in target_path.rglob("*"):
                if file_path.is_file() and query.lower() in file_path.name.lower():
                    matches.append(f"📄 {file_path.relative_to(self.project_root)}")
            
            if not matches:
                return f"🔍 No files found matching '{query}' in {directory}"
            
            return f"🔍 Files matching '{query}':\n" + "\n".join(matches[:20])  # Limit to 20 results
            
        except Exception as e:
            return f"❌ Error searching files: {e}"
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path"""
        if os.path.isabs(path):
            raise ValueError("Absolute paths not allowed")
        
        target_path = (self.project_root / path).resolve()
        
        # Security check: ensure path is within project root
        if not str(target_path).startswith(str(self.project_root)):
            raise ValueError("Path traversal not allowed")
        
        return target_path
    
    # === UNIFIED PLATFORM INTEGRATION ===
    
    async def finsight_analysis(self, ticker: str, period: str = "2024-Q4") -> str:
        """Perform financial analysis using FinSight"""
        try:
            data = {
                "ticker": ticker,
                "period": period,
                "data": {}  # TODO: Add actual financial data
            }
            
            result = await self._make_request("/api/v1/finsight/analyze", data)
            
            if result.get("success"):
                return f"📊 Financial Analysis for {ticker} ({period}):\n\n{result.get('analysis', 'No analysis available')}"
            else:
                return f"❌ FinSight analysis failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error with FinSight analysis: {e}"
    
    async def research_synthesis(self, papers: List[str], focus: str = "key_findings") -> str:
        """Perform research synthesis using Archive"""
        try:
            # Convert paper IDs to paper objects (simplified)
            paper_objects = []
            for paper_id in papers:
                paper_objects.append({
                    "id": paper_id,
                    "title": f"Research Paper {paper_id}",
                    "authors": ["Author 1", "Author 2"],
                    "abstract": f"Abstract for paper {paper_id}",
                    "content": f"Content for paper {paper_id}"
                })
            
            data = {
                "papers": paper_objects,
                "focus": focus
            }
            
            result = await self._make_request("/api/v1/archive/synthesize", data)
            
            if result.get("success"):
                return f"📚 Research Synthesis (focus: {focus}):\n\n{result.get('synthesis', 'No synthesis available')}"
            else:
                return f"❌ Archive synthesis failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error with Archive synthesis: {e}"
    
    async def enhanced_assistance(self, question: str, context: Dict[str, Any] = None) -> str:
        """Get enhanced assistance using unified platform"""
        try:
            data = {
                "question": question,
                "context": context or {}
            }
            
            result = await self._make_request("/api/v1/assistant/help", data)
            
            if result.get("success"):
                return f"🤖 Enhanced Assistance:\n\n{result.get('response', 'No response available')}"
            else:
                return f"❌ Enhanced assistance failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error with enhanced assistance: {e}"
    
    async def platform_status(self) -> str:
        """Check unified platform status"""
        try:
            result = await self._make_request("/api/v1/status")
            
            if result.get("platform"):
                status_text = f"🚀 Unified Platform Status:\n\n"
                status_text += f"Platform: {result.get('platform')}\n"
                status_text += f"Version: {result.get('version')}\n"
                status_text += f"Environment: {result.get('environment')}\n\n"
                
                services = result.get("services", {})
                for service, info in services.items():
                    status_text += f"📋 {service.title()}:\n"
                    status_text += f"   Status: {info.get('status', 'unknown')}\n"
                    status_text += f"   LLM: {info.get('llm', 'unknown')}\n"
                    status_text += f"   Features: {', '.join(info.get('features', []))}\n\n"
                
                return status_text
            else:
                return f"❌ Platform status check failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error checking platform status: {e}"
    
    # === CHAT INTERFACE ===
    
    async def chat(self):
        """Interactive chat interface"""
        console.print(Panel.fit(
            "[bold blue]Vertikal Unified[/bold blue] - Terminal Assistant\n"
            "Connected to FinSight + Archive + Enhanced R/SQL Assistant\n\n"
            "[yellow]Commands:[/yellow]\n"
            "• [green]list[/green] [dir] - List files\n"
            "• [green]read[/green] <file> - Read file\n"
            "• [green]search[/green] <query> - Search files\n"
            "• [green]finsight[/green] <ticker> - Financial analysis\n"
            "• [green]research[/green] <papers> - Research synthesis\n"
            "• [green]status[/green] - Platform status\n"
            "• [green]quit[/green] - Exit\n\n"
            "Or just ask questions for enhanced assistance!",
            title="🤖 Vertikal Unified",
            border_style="blue"
        ))
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("👋 Goodbye!")
                    break
                
                # Handle commands
                if user_input.startswith('list '):
                    directory = user_input[5:].strip() or "."
                    result = self.list_files(directory)
                    console.print(result)
                
                elif user_input.startswith('read '):
                    filepath = user_input[5:].strip()
                    result = self.read_file(filepath)
                    console.print(result)
                
                elif user_input.startswith('search '):
                    query = user_input[7:].strip()
                    result = self.search_files(query)
                    console.print(result)
                
                elif user_input.startswith('finsight '):
                    ticker = user_input[9:].strip()
                    result = await self.finsight_analysis(ticker)
                    console.print(result)
                
                elif user_input.startswith('research '):
                    papers = user_input[9:].strip().split()
                    result = await self.research_synthesis(papers)
                    console.print(result)
                
                elif user_input.lower() == 'status':
                    result = await self.platform_status()
                    console.print(result)
                
                else:
                    # Enhanced assistance
                    result = await self.enhanced_assistance(user_input)
                    console.print(result)
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Vertikal Unified - Terminal assistant with platform integration")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--platform-url", default="http://localhost:8000", help="Unified platform URL")
    parser.add_argument("--api-key", help="API key for platform access")
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = args.api_key or os.getenv("UNIFIED_API_KEY")
    if not api_key:
        console.print("⚠️  Warning: No API key provided. Some features may not work.")
        console.print("Set UNIFIED_API_KEY environment variable or use --api-key")
    
    try:
        async with VertikalUnified(args.project_root, args.platform_url, api_key) as vertikal:
            await vertikal.chat()
    except Exception as e:
        console.print(f"❌ Failed to start Vertikal Unified: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
