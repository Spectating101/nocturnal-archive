#!/usr/bin/env python3
"""
Vertikal - Terminal-based file-aware ChatGPT
A minimal CLI assistant that can see your project files and answer questions
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from groq import Groq

class VertikalAssistant:
    """Minimal terminal assistant with file awareness"""
    
    def __init__(self, project_root: str = ".", safe_mode: bool = True):
        self.project_root = Path(project_root).resolve()
        self.safe_mode = safe_mode
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.conversation_history = []
        self.token_count = 0
        
        # Ensure we're in the project root
        os.chdir(self.project_root)
        print(f"📁 Project root: {self.project_root}")
        print(f"🔒 Safe mode: {'ON' if safe_mode else 'OFF'}")
    
    def list_files(self, path: str = ".") -> str:
        """List files in directory with tree-like view"""
        try:
            target_path = self._validate_path(path)
            if not target_path.exists():
                return f"❌ Directory not found: {path}"
            
            files = []
            dirs = []
            
            for item in sorted(target_path.iterdir()):
                if item.is_file():
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({size} bytes)")
                elif item.is_dir() and not item.name.startswith('.'):
                    dirs.append(f"📁 {item.name}/")
            
            result = f"📂 {target_path.relative_to(self.project_root)}\n"
            result += "\n".join(dirs + files[:20])  # Limit to 20 files
            if len(files) > 20:
                result += f"\n... and {len(files) - 20} more files"
            
            return result
        except Exception as e:
            return f"❌ Error listing files: {e}"
    
    def read_file(self, filepath: str, lines: int = 50) -> str:
        """Read file with preview (head/tail)"""
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
            
            # Smart preview based on file type
            if target_path.suffix in ['.py', '.r', '.R', '.sql', '.js', '.ts']:
                # Show first N lines for code files
                lines_list = content.split('\n')
                preview = '\n'.join(lines_list[:lines])
                if len(lines_list) > lines:
                    preview += f"\n... ({len(lines_list) - lines} more lines)"
            else:
                # Show first N characters for other files
                preview = content[:1000]
                if len(content) > 1000:
                    preview += f"\n... ({len(content) - 1000} more characters)"
            
            return f"📄 {target_path.name}\n\n{preview}"
        except Exception as e:
            return f"❌ Error reading file: {e}"
    
    def search_files(self, query: str, extensions: List[str] = None) -> str:
        """Search for text in files"""
        try:
            if extensions is None:
                extensions = ['.py', '.r', '.R', '.Rmd', '.qmd', '.sql', '.md', '.txt']
            
            results = []
            for ext in extensions:
                for file_path in self.project_root.rglob(f"*{ext}"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                # Find line numbers
                                lines = content.split('\n')
                                matches = []
                                for i, line in enumerate(lines, 1):
                                    if query.lower() in line.lower():
                                        matches.append(f"  {i}: {line.strip()}")
                                
                                if matches:
                                    rel_path = file_path.relative_to(self.project_root)
                                    results.append(f"📄 {rel_path}")
                                    results.extend(matches[:5])  # Limit to 5 matches per file
                    except:
                        continue
            
            if results:
                return f"🔍 Search results for '{query}':\n\n" + "\n".join(results[:20])
            else:
                return f"🔍 No matches found for '{query}'"
        except Exception as e:
            return f"❌ Error searching files: {e}"
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path within project root"""
        if self.safe_mode:
            # Prevent path traversal
            if ".." in path or path.startswith("/"):
                raise ValueError("Access denied: Invalid path format")
        
        target_path = (self.project_root / path).resolve()
        
        # Ensure path is within project root
        try:
            target_path.relative_to(self.project_root)
        except ValueError:
            raise ValueError("Access denied: Path outside project directory")
        
        return target_path
    
    def chat(self, question: str) -> str:
        """Main chat function with file awareness"""
        # Add to conversation history (keep last 3 turns)
        self.conversation_history.append({"role": "user", "content": question})
        if len(self.conversation_history) > 6:  # 3 turns = 6 messages
            self.conversation_history = self.conversation_history[-6:]
        
        # Build context
        context = self._build_context()
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Vertikal, a terminal-based assistant that can see project files.

Available commands:
- list_files() - List directory contents
- read_file(path) - Read file content
- search_files(query) - Search in files

You can help with:
- R/SQL programming questions
- File navigation and analysis
- Code explanations and suggestions
- Project structure understanding

Keep responses concise and practical. When suggesting code, make it copy-pasteable."""
                    },
                    *self.conversation_history
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # Track tokens (rough estimate)
            self.token_count += len(question.split()) + len(answer.split())
            
            return answer
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _build_context(self) -> str:
        """Build context from current directory"""
        try:
            files = list(self.project_root.iterdir())
            file_list = [f.name for f in files if f.is_file()][:10]
            dir_list = [f.name for f in files if f.is_dir() and not f.name.startswith('.')][:5]
            
            context = f"Current directory: {self.project_root.name}\n"
            if file_list:
                context += f"Files: {', '.join(file_list)}\n"
            if dir_list:
                context += f"Directories: {', '.join(dir_list)}\n"
            
            return context
        except:
            return ""

def main():
    parser = argparse.ArgumentParser(
        description="Vertikal - Terminal file-aware assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vertikal --project-root /path/to/project
  vertikal --safe-mode --verbose
  vertikal --version

Environment:
  GROQ_API_KEY    Required: Get free key at https://console.groq.com/
        """
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--safe-mode", action="store_true", default=True, help="Enable safe mode")
    parser.add_argument("--verbose", action="store_true", help="Show debug info")
    parser.add_argument("--version", action="version", version=f"vertikal {__version__}")
    
    args = parser.parse_args()
    
    # Check for Groq API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("Get your free API key at: https://console.groq.com/")
        print("Then run: export GROQ_API_KEY='your_key_here'")
        sys.exit(1)
    
    # Validate project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"❌ Error: Project root does not exist: {project_root}")
        sys.exit(1)
    
    if not project_root.is_dir():
        print(f"❌ Error: Project root is not a directory: {project_root}")
        sys.exit(1)
    
    try:
        # Initialize assistant
        assistant = VertikalAssistant(project_root, args.safe_mode)
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    print("\n🤖 Vertikal - Terminal Assistant")
    print("=" * 40)
    print("Commands: list, read <file>, search <query>, or just ask questions")
    print("Type 'quit' to exit, 'help' for more info")
    print()
    
    while True:
        try:
            # Show current directory
            cwd = Path.cwd().relative_to(assistant.project_root)
            prompt = f"vertikal:{cwd}> "
            
            question = input(prompt).strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'help':
                print("""
📋 Available commands:
  list                    - List files in current directory
  read <filename>         - Read file content
  search <query>          - Search for text in files
  <any question>          - Ask about your project or code
  
Examples:
  list
  read README.md
  search "function"
  How do I create a histogram in R?
  Explain this SQL query
                """)
                continue
            
            if not question:
                continue
            
            # Handle commands
            if question.lower() == 'list':
                result = assistant.list_files()
                print(result)
                continue
            
            if question.lower().startswith('read '):
                filename = question[5:].strip()
                result = assistant.read_file(filename)
                print(result)
                continue
            
            if question.lower().startswith('search '):
                query = question[7:].strip()
                result = assistant.search_files(query)
                print(result)
                continue
            
            # Regular chat
            print("🤔 Thinking...")
            start_time = time.time()
            
            answer = assistant.chat(question)
            
            duration = time.time() - start_time
            print(f"\n{answer}")
            
            if args.verbose:
                print(f"\n⏱️  Response time: {duration:.2f}s | Tokens: ~{assistant.token_count}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
