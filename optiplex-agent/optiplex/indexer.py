"""Codebase indexing and semantic search using embeddings"""
import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import ast
import re


@dataclass
class CodeChunk:
    """A chunk of code with metadata"""
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str  # 'class', 'function', 'file', 'block'
    name: Optional[str]
    docstring: Optional[str]
    imports: List[str]
    calls: List[str]
    hash: str


class CodebaseIndexer:
    """Index codebase for fast semantic search"""

    def __init__(self, root_dir: str, index_dir: str = ".optiplex/index"):
        self.root_dir = Path(root_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_filepath = self.index_dir / "code_index.pkl"
        self.metadata_filepath = self.index_dir / "metadata.json"
        self.embeddings_filepath = self.index_dir / "embeddings.pkl"

        # Code index: file_path -> list of chunks
        self.code_index: Dict[str, List[CodeChunk]] = {}
        # Embeddings cache (if using embedding models)
        self.embeddings_cache: Dict[str, List[float]] = {}
        # Metadata about indexing
        self.metadata = {
            "indexed_files": 0,
            "total_chunks": 0,
            "last_indexed": None,
            "file_hashes": {}
        }

        self._load_index()

    def _load_index(self):
        """Load existing index from disk"""
        try:
            if self.index_filepath.exists():
                with open(self.index_filepath, 'rb') as f:
                    self.code_index = pickle.load(f)

            if self.metadata_filepath.exists():
                with open(self.metadata_filepath, 'r') as f:
                    self.metadata = json.load(f)

            if self.embeddings_filepath.exists():
                with open(self.embeddings_filepath, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load index: {e}")

    def _save_index(self):
        """Save index to disk"""
        try:
            with open(self.index_filepath, 'wb') as f:
                pickle.dump(self.code_index, f)

            with open(self.metadata_filepath, 'w') as f:
                json.dump(self.metadata, f, indent=2)

            with open(self.embeddings_filepath, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
        except Exception as e:
            print(f"Error saving index: {e}")

    def _file_hash(self, filepath: Path) -> str:
        """Get MD5 hash of file content"""
        try:
            return hashlib.md5(filepath.read_bytes()).hexdigest()
        except:
            return ""

    def _chunk_hash(self, content: str) -> str:
        """Get hash of code chunk"""
        return hashlib.md5(content.encode()).hexdigest()

    def _needs_reindex(self, filepath: Path) -> bool:
        """Check if file needs to be reindexed"""
        current_hash = self._file_hash(filepath)
        stored_hash = self.metadata["file_hashes"].get(str(filepath))
        return current_hash != stored_hash

    def _extract_python_chunks(self, filepath: Path) -> List[CodeChunk]:
        """Extract meaningful chunks from Python file"""
        chunks = []

        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            lines = content.splitlines()

            # Extract top-level imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    chunk_content = '\n'.join(lines[start_line-1:end_line])

                    docstring = ast.get_docstring(node)

                    # Find method calls
                    calls = []
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            if isinstance(subnode.func, ast.Name):
                                calls.append(subnode.func.id)
                            elif isinstance(subnode.func, ast.Attribute):
                                calls.append(subnode.func.attr)

                    chunks.append(CodeChunk(
                        file_path=str(filepath),
                        start_line=start_line,
                        end_line=end_line,
                        content=chunk_content,
                        chunk_type='class',
                        name=node.name,
                        docstring=docstring,
                        imports=imports,
                        calls=list(set(calls)),
                        hash=self._chunk_hash(chunk_content)
                    ))

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip methods (already in classes)
                    skip = False
                    for p in ast.walk(tree):
                        if isinstance(p, ast.ClassDef):
                            if hasattr(p, 'body') and isinstance(p.body, list) and node in p.body:
                                skip = True
                                break
                    if skip:
                        continue

                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    chunk_content = '\n'.join(lines[start_line-1:end_line])

                    docstring = ast.get_docstring(node)

                    calls = []
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            if isinstance(subnode.func, ast.Name):
                                calls.append(subnode.func.id)
                            elif isinstance(subnode.func, ast.Attribute):
                                calls.append(subnode.func.attr)

                    chunks.append(CodeChunk(
                        file_path=str(filepath),
                        start_line=start_line,
                        end_line=end_line,
                        content=chunk_content,
                        chunk_type='function',
                        name=node.name,
                        docstring=docstring,
                        imports=imports,
                        calls=list(set(calls)),
                        hash=self._chunk_hash(chunk_content)
                    ))

            # If no classes/functions, index entire file as one chunk
            if not chunks:
                chunks.append(CodeChunk(
                    file_path=str(filepath),
                    start_line=1,
                    end_line=len(lines),
                    content=content,
                    chunk_type='file',
                    name=filepath.name,
                    docstring=None,
                    imports=imports,
                    calls=[],
                    hash=self._chunk_hash(content)
                ))

        except Exception as e:
            # Fallback: treat as plain text
            print(f"Debug - Exception in _extract_python_chunks: {type(e).__name__}: {e}")
            try:
                content = filepath.read_text()
                chunks.append(CodeChunk(
                    file_path=str(filepath),
                    start_line=1,
                    end_line=len(content.splitlines()),
                    content=content,
                    chunk_type='file',
                    name=filepath.name,
                    docstring=None,
                    imports=[],
                    calls=[],
                    hash=self._chunk_hash(content)
                ))
            except Exception as e2:
                print(f"Debug - Even fallback failed: {type(e2).__name__}: {e2}")

        return chunks

    def _extract_generic_chunks(self, filepath: Path) -> List[CodeChunk]:
        """Extract chunks from non-Python files"""
        try:
            content = filepath.read_text()
            lines = content.splitlines()

            # Chunk by functions/classes using simple regex
            chunks = []

            # Try to find function/class definitions
            function_pattern = r'(function|def|func|fn|class|struct|interface)\s+(\w+)'

            current_chunk_start = 1
            current_chunk_lines = []
            chunk_name = None

            for i, line in enumerate(lines, 1):
                match = re.search(function_pattern, line)
                if match and current_chunk_lines:
                    # Save previous chunk
                    chunks.append(CodeChunk(
                        file_path=str(filepath),
                        start_line=current_chunk_start,
                        end_line=i-1,
                        content='\n'.join(current_chunk_lines),
                        chunk_type='block',
                        name=chunk_name,
                        docstring=None,
                        imports=[],
                        calls=[],
                        hash=self._chunk_hash('\n'.join(current_chunk_lines))
                    ))
                    current_chunk_start = i
                    current_chunk_lines = [line]
                    chunk_name = match.group(2)
                else:
                    current_chunk_lines.append(line)

            # Save last chunk
            if current_chunk_lines:
                chunks.append(CodeChunk(
                    file_path=str(filepath),
                    start_line=current_chunk_start,
                    end_line=len(lines),
                    content='\n'.join(current_chunk_lines),
                    chunk_type='block',
                    name=chunk_name,
                    docstring=None,
                    imports=[],
                    calls=[],
                    hash=self._chunk_hash('\n'.join(current_chunk_lines))
                ))

            # If no chunks found, index entire file
            if not chunks:
                chunks.append(CodeChunk(
                    file_path=str(filepath),
                    start_line=1,
                    end_line=len(lines),
                    content=content,
                    chunk_type='file',
                    name=filepath.name,
                    docstring=None,
                    imports=[],
                    calls=[],
                    hash=self._chunk_hash(content)
                ))

            return chunks

        except Exception as e:
            return []

    def index_file(self, filepath: Path) -> int:
        """Index a single file, return number of chunks"""
        if not filepath.is_file():
            return 0

        # Check if needs reindexing
        if not self._needs_reindex(filepath):
            return len(self.code_index.get(str(filepath), []))

        # Extract chunks based on file type
        if filepath.suffix == '.py':
            chunks = self._extract_python_chunks(filepath)
        else:
            chunks = self._extract_generic_chunks(filepath)

        # Store chunks
        self.code_index[str(filepath)] = chunks
        self.metadata["file_hashes"][str(filepath)] = self._file_hash(filepath)

        return len(chunks)

    def index_directory(
        self,
        extensions: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Index entire directory"""
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go',
                         '.rs', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php']

        if ignore_patterns is None:
            ignore_patterns = [
                '.git', '__pycache__', 'node_modules', 'venv', '.venv',
                'dist', 'build', '.optiplex', 'target', '.next'
            ]

        stats = {"files_indexed": 0, "chunks_created": 0, "files_skipped": 0}

        for filepath in self.root_dir.rglob('*'):
            # Skip ignored paths
            if any(pattern in str(filepath) for pattern in ignore_patterns):
                continue

            # Check extension
            if filepath.suffix not in extensions:
                continue

            # Index file
            try:
                num_chunks = self.index_file(filepath)
                stats["files_indexed"] += 1
                stats["chunks_created"] += num_chunks
            except Exception as e:
                stats["files_skipped"] += 1
                print(f"Error indexing {filepath}: {e}")

        # Update metadata
        self.metadata["indexed_files"] = stats["files_indexed"]
        self.metadata["total_chunks"] = stats["chunks_created"]
        self.metadata["last_indexed"] = str(Path.cwd())

        # Save index
        self._save_index()

        return stats

    def search_by_name(self, query: str, limit: int = 20) -> List[CodeChunk]:
        """Search for code chunks by name"""
        results = []
        query_lower = query.lower()

        for chunks in self.code_index.values():
            for chunk in chunks:
                if chunk.name and query_lower in chunk.name.lower():
                    results.append(chunk)

        return results[:limit]

    def search_by_content(self, query: str, limit: int = 20) -> List[CodeChunk]:
        """Search for code chunks by content (regex)"""
        results = []

        try:
            pattern = re.compile(query, re.IGNORECASE)
        except:
            # Fallback to plain text search
            pattern = None

        for chunks in self.code_index.values():
            for chunk in chunks:
                if pattern:
                    if pattern.search(chunk.content):
                        results.append(chunk)
                else:
                    if query.lower() in chunk.content.lower():
                        results.append(chunk)

        return results[:limit]

    def search_by_import(self, module: str) -> List[CodeChunk]:
        """Find all code that imports a module"""
        results = []

        for chunks in self.code_index.values():
            for chunk in chunks:
                if any(module in imp for imp in chunk.imports):
                    results.append(chunk)

        return results

    def search_by_call(self, function_name: str) -> List[CodeChunk]:
        """Find all code that calls a function"""
        results = []

        for chunks in self.code_index.values():
            for chunk in chunks:
                if function_name in chunk.calls:
                    results.append(chunk)

        return results

    def get_file_summary(self, filepath: str) -> Dict[str, Any]:
        """Get summary of a file's contents"""
        chunks = self.code_index.get(filepath, [])

        classes = [c.name for c in chunks if c.chunk_type == 'class' and c.name]
        functions = [c.name for c in chunks if c.chunk_type == 'function' and c.name]
        imports = []
        for chunk in chunks:
            imports.extend(chunk.imports)
        imports = list(set(imports))

        return {
            "filepath": filepath,
            "num_chunks": len(chunks),
            "classes": classes,
            "functions": functions,
            "imports": imports
        }

    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get summary of entire codebase"""
        total_files = len(self.code_index)
        total_chunks = sum(len(chunks) for chunks in self.code_index.values())

        all_classes = []
        all_functions = []
        all_imports = []

        for chunks in self.code_index.values():
            for chunk in chunks:
                if chunk.chunk_type == 'class' and chunk.name:
                    all_classes.append(chunk.name)
                if chunk.chunk_type == 'function' and chunk.name:
                    all_functions.append(chunk.name)
                all_imports.extend(chunk.imports)

        # Count file types
        file_types = {}
        for filepath in self.code_index.keys():
            ext = Path(filepath).suffix
            file_types[ext] = file_types.get(ext, 0) + 1

        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "total_classes": len(all_classes),
            "total_functions": len(all_functions),
            "unique_imports": len(set(all_imports)),
            "file_types": file_types,
            "top_classes": list(set(all_classes))[:20],
            "top_functions": list(set(all_functions))[:20]
        }

    def clear_index(self):
        """Clear all index data"""
        self.code_index = {}
        self.embeddings_cache = {}
        self.metadata = {
            "indexed_files": 0,
            "total_chunks": 0,
            "last_indexed": None,
            "file_hashes": {}
        }
        self._save_index()
