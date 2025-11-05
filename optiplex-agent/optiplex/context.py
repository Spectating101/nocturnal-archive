"""Context management for intelligent code analysis"""
import ast
import os
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class FileContext:
    """Context information for a file"""
    path: str
    content: str
    imports: List[str]
    classes: List[str]
    functions: List[str]
    dependencies: Set[str]
    size: int

class ContextManager:
    """Manages code context and dependencies"""
    
    def __init__(self, root_dir: str, max_files: int = 20, max_size: int = 100000):
        self.root_dir = Path(root_dir)
        self.max_files = max_files
        self.max_size = max_size
        self.context_cache: Dict[str, FileContext] = {}
    
    def analyze_python_file(self, filepath: Path) -> FileContext:
        """Analyze a Python file using AST"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            
            imports = []
            classes = []
            functions = []
            dependencies = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        dependencies.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(f"from {node.module}")
                        dependencies.add(node.module.split('.')[0])
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            return FileContext(
                path=str(filepath),
                content=content,
                imports=imports,
                classes=classes,
                functions=functions,
                dependencies=dependencies,
                size=len(content)
            )
        except Exception as e:
            # Fallback for non-parseable files
            content = filepath.read_text()
            return FileContext(
                path=str(filepath),
                content=content,
                imports=[],
                classes=[],
                functions=[],
                dependencies=set(),
                size=len(content)
            )
    
    def find_related_files(self, filepath: str, max_depth: int = 2) -> List[str]:
        """Find files related to the given file"""
        target_path = Path(filepath)
        if not target_path.exists():
            return []
        
        # Get context for target file
        if target_path.suffix == '.py':
            context = self.analyze_python_file(target_path)
        else:
            context = FileContext(
                path=str(target_path),
                content=target_path.read_text(),
                imports=[],
                classes=[],
                functions=[],
                dependencies=set(),
                size=target_path.stat().st_size
            )
        
        related = []
        
        # Find files in same directory
        for sibling in target_path.parent.glob('*.py'):
            if sibling != target_path and sibling.stat().st_size <= self.max_size:
                related.append(str(sibling))
        
        # Find files with matching dependencies
        for py_file in self.root_dir.rglob('*.py'):
            if py_file == target_path or py_file.stat().st_size > self.max_size:
                continue
            
            try:
                file_ctx = self.analyze_python_file(py_file)
                # Check if this file imports our target or vice versa
                if context.dependencies & file_ctx.dependencies:
                    related.append(str(py_file))
            except:
                pass
        
        # Limit results
        return related[:self.max_files]
    
    def get_context_for_files(self, filepaths: List[str]) -> Dict[str, FileContext]:
        """Get context for multiple files"""
        contexts = {}
        total_size = 0
        
        for filepath in filepaths:
            if total_size >= self.max_size * self.max_files:
                break
            
            path = Path(filepath)
            if not path.exists() or path.stat().st_size > self.max_size:
                continue
            
            if filepath in self.context_cache:
                context = self.context_cache[filepath]
            else:
                if path.suffix == '.py':
                    context = self.analyze_python_file(path)
                else:
                    context = FileContext(
                        path=filepath,
                        content=path.read_text(),
                        imports=[],
                        classes=[],
                        functions=[],
                        dependencies=set(),
                        size=path.stat().st_size
                    )
                self.context_cache[filepath] = context
            
            contexts[filepath] = context
            total_size += context.size
        
        return contexts
    
    def build_context_summary(self, contexts: Dict[str, FileContext]) -> str:
        """Build a summary of file contexts"""
        summary_parts = []
        
        for filepath, ctx in contexts.items():
            summary_parts.append(f"\n## {filepath}")
            summary_parts.append(f"Size: {ctx.size} bytes")
            
            if ctx.imports:
                summary_parts.append(f"Imports: {', '.join(ctx.imports[:5])}")
            if ctx.classes:
                summary_parts.append(f"Classes: {', '.join(ctx.classes)}")
            if ctx.functions:
                summary_parts.append(f"Functions: {', '.join(ctx.functions[:10])}")
        
        return '\n'.join(summary_parts)
    
    def get_smart_context(self, target_files: List[str]) -> str:
        """Get intelligent context for target files"""
        all_files = set(target_files)
        
        # Find related files for each target
        for target in target_files[:3]:  # Limit to first 3 targets
            related = self.find_related_files(target)
            all_files.update(related[:5])
        
        # Get contexts
        contexts = self.get_context_for_files(list(all_files)[:self.max_files])
        
        # Build summary
        summary = self.build_context_summary(contexts)
        
        # Add full content for target files
        full_context = [summary, "\n\n## Full File Contents\n"]
        for filepath in target_files:
            if filepath in contexts:
                ctx = contexts[filepath]
                full_context.append(f"\n### {filepath}\n```\n{ctx.content}\n```")
        
        return '\n'.join(full_context)
