"""Tree-sitter based multi-language AST parsing"""
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import hashlib
import os

# Tree-sitter will be optional dependency
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class ASTNode:
    """Represents a parsed AST node"""
    type: str  # function, class, method, variable, import
    name: str
    filepath: str
    start_line: int
    end_line: int
    code: str
    parent: Optional[str] = None  # For methods inside classes
    imports: List[str] = None
    calls: List[str] = None


class TreeSitterParser:
    """Multi-language parser using Tree-sitter"""

    LANGUAGE_QUERIES = {
        'python': {
            'function': '(function_definition name: (identifier) @name)',
            'class': '(class_definition name: (identifier) @name)',
            'import': '(import_statement)',
            'call': '(call function: (identifier) @name)',
        },
        'javascript': {
            'function': '(function_declaration name: (identifier) @name)',
            'class': '(class_declaration name: (identifier) @name)',
            'import': '(import_statement)',
            'call': '(call_expression function: (identifier) @name)',
        },
        'typescript': {
            'function': '(function_declaration name: (identifier) @name)',
            'class': '(class_declaration name: (identifier) @name)',
            'interface': '(interface_declaration name: (type_identifier) @name)',
            'import': '(import_statement)',
        },
        'go': {
            'function': '(function_declaration name: (identifier) @name)',
            'struct': '(type_declaration (type_spec name: (type_identifier) @name))',
            'import': '(import_declaration)',
        },
        'rust': {
            'function': '(function_item name: (identifier) @name)',
            'struct': '(struct_item name: (type_identifier) @name)',
            'impl': '(impl_item type: (type_identifier) @name)',
        },
    }

    def __init__(self, languages_path: Optional[str] = None):
        """Initialize parser with language libraries"""
        self.parsers = {}
        self.available_languages = []

        if not TREE_SITTER_AVAILABLE:
            return

        # Try to load from environment variable or provided path
        if languages_path is None:
            languages_path = os.getenv('TREE_SITTER_LIB_PATH')

        if languages_path:
            self._load_languages(languages_path)

    def _load_languages(self, languages_path: str):
        """Load tree-sitter language libraries"""
        lang_dir = Path(languages_path)

        for lang_name in ['python', 'javascript', 'typescript', 'go', 'rust']:
            lang_file = lang_dir / f"tree-sitter-{lang_name}.so"
            if lang_file.exists():
                try:
                    language = Language(str(lang_file), lang_name)
                    parser = Parser()
                    parser.set_language(language)
                    self.parsers[lang_name] = parser
                    self.available_languages.append(lang_name)
                except Exception:
                    continue

    def parse_file(self, filepath: Path) -> List[ASTNode]:
        """Parse a file and extract AST nodes"""
        # Determine language from extension
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
        }

        language = ext_to_lang.get(filepath.suffix)
        if not language or language not in self.parsers:
            return []

        try:
            content = filepath.read_text()
            tree = self.parsers[language].parse(bytes(content, 'utf8'))
            return self._extract_nodes(tree.root_node, filepath, content, language)
        except Exception:
            return []

    def _extract_nodes(
        self,
        node: Any,
        filepath: Path,
        content: str,
        language: str
    ) -> List[ASTNode]:
        """Extract meaningful nodes from parse tree"""
        nodes = []
        lines = content.split('\n')

        def get_node_text(n):
            start_byte = n.start_byte
            end_byte = n.end_byte
            return content[start_byte:end_byte]

        def get_node_code(n):
            start_line = n.start_point[0]
            end_line = n.end_point[0]
            return '\n'.join(lines[start_line:end_line + 1])

        def traverse(n, parent_name=None):
            node_type = n.type

            # Extract functions
            if node_type == 'function_definition' or node_type == 'function_declaration' or node_type == 'function_item':
                name_node = None
                for child in n.children:
                    if child.type == 'identifier':
                        name_node = child
                        break

                if name_node:
                    name = get_node_text(name_node)
                    ast_node = ASTNode(
                        type='method' if parent_name else 'function',
                        name=name,
                        filepath=str(filepath),
                        start_line=n.start_point[0] + 1,
                        end_line=n.end_point[0] + 1,
                        code=get_node_code(n),
                        parent=parent_name,
                        imports=[],
                        calls=[]
                    )

                    # Extract function calls within this function
                    calls = []
                    self._extract_calls(n, calls, content)
                    ast_node.calls = calls

                    nodes.append(ast_node)

            # Extract classes
            elif node_type == 'class_definition' or node_type == 'class_declaration':
                name_node = None
                for child in n.children:
                    if child.type == 'identifier':
                        name_node = child
                        break

                if name_node:
                    name = get_node_text(name_node)
                    nodes.append(ASTNode(
                        type='class',
                        name=name,
                        filepath=str(filepath),
                        start_line=n.start_point[0] + 1,
                        end_line=n.end_point[0] + 1,
                        code=get_node_code(n),
                        imports=[],
                        calls=[]
                    ))

                    # Parse methods inside class
                    for child in n.children:
                        traverse(child, parent_name=name)
                    return  # Don't traverse children again

            # Extract imports
            elif 'import' in node_type:
                code = get_node_code(n)
                nodes.append(ASTNode(
                    type='import',
                    name=code.strip(),
                    filepath=str(filepath),
                    start_line=n.start_point[0] + 1,
                    end_line=n.end_point[0] + 1,
                    code=code,
                    imports=[],
                    calls=[]
                ))

            # Traverse children
            for child in n.children:
                traverse(child, parent_name)

        traverse(node)
        return nodes

    def _extract_calls(self, node: Any, calls: List[str], content: str):
        """Extract function calls from a node"""
        if node.type == 'call' or node.type == 'call_expression':
            # Get function name
            for child in node.children:
                if child.type == 'identifier':
                    call_name = content[child.start_byte:child.end_byte]
                    if call_name not in calls:
                        calls.append(call_name)
                    break

        for child in node.children:
            self._extract_calls(child, calls, content)

    def get_imports(self, filepath: Path) -> List[str]:
        """Get all imports from a file"""
        nodes = self.parse_file(filepath)
        return [n.name for n in nodes if n.type == 'import']

    def get_function_calls(self, filepath: Path, function_name: str) -> List[str]:
        """Get all calls made by a specific function"""
        nodes = self.parse_file(filepath)
        for node in nodes:
            if node.type in ['function', 'method'] and node.name == function_name:
                return node.calls or []
        return []

    def find_definition(self, filepath: Path, symbol_name: str) -> Optional[ASTNode]:
        """Find definition of a symbol (class, function, etc.)"""
        nodes = self.parse_file(filepath)
        for node in nodes:
            if node.name == symbol_name:
                return node
        return None


class FallbackParser:
    """Fallback regex-based parser when Tree-sitter unavailable"""

    def __init__(self):
        self.patterns = {
            'python': {
                'function': r'^def\s+(\w+)\s*\(',
                'class': r'^class\s+(\w+)',
                'import': r'^(?:from\s+[\w.]+\s+)?import\s+(.+)',
            },
            'javascript': {
                'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\()',
                'class': r'class\s+(\w+)',
                'import': r'import\s+(?:{[^}]+}|\w+)\s+from',
            },
        }

    def parse_file(self, filepath: Path) -> List[ASTNode]:
        """Basic regex-based parsing"""
        import re

        ext_to_lang = {'.py': 'python', '.js': 'javascript', '.ts': 'javascript'}
        language = ext_to_lang.get(filepath.suffix)

        if not language or language not in self.patterns:
            return []

        nodes = []
        try:
            content = filepath.read_text()
            lines = content.split('\n')

            for i, line in enumerate(lines):
                for node_type, pattern in self.patterns[language].items():
                    match = re.match(pattern, line.strip())
                    if match:
                        name = match.group(1) or match.group(2) if match.lastindex >= 2 else match.group(1)
                        if name:
                            nodes.append(ASTNode(
                                type=node_type,
                                name=name,
                                filepath=str(filepath),
                                start_line=i + 1,
                                end_line=i + 1,
                                code=line.strip(),
                                imports=[],
                                calls=[]
                            ))
        except Exception:
            pass

        return nodes


# Factory function
def create_parser(languages_path: Optional[str] = None):
    """Create appropriate parser based on availability"""
    if TREE_SITTER_AVAILABLE and languages_path:
        parser = TreeSitterParser(languages_path)
        if parser.available_languages:
            return parser

    # Fallback to regex-based parser
    return FallbackParser()
