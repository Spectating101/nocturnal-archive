"""Auto-import detection and insertion"""
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import ast
import re
from dataclasses import dataclass


@dataclass
class ImportSuggestion:
    """Represents an import suggestion"""
    module: str
    names: List[str]
    import_type: str  # 'import' or 'from_import'
    line_number: int  # Where to insert
    reason: str  # Why this import is needed


class AutoImport:
    """Detect missing imports and suggest additions"""

    # Common standard library modules by symbol
    STDLIB_SYMBOLS = {
        # File operations
        'Path': 'pathlib',
        'os': 'os',
        'sys': 'sys',
        'shutil': 'shutil',
        'glob': 'glob',

        # Data structures
        'defaultdict': 'collections',
        'Counter': 'collections',
        'OrderedDict': 'collections',
        'deque': 'collections',
        'namedtuple': 'collections',

        # Type hints
        'List': 'typing',
        'Dict': 'typing',
        'Optional': 'typing',
        'Union': 'typing',
        'Tuple': 'typing',
        'Any': 'typing',
        'Callable': 'typing',

        # Async
        'asyncio': 'asyncio',
        'aiohttp': 'aiohttp',

        # Data classes
        'dataclass': 'dataclasses',
        'field': 'dataclasses',

        # JSON
        'json': 'json',

        # Regex
        're': 're',

        # Time
        'datetime': 'datetime',
        'time': 'time',
        'timedelta': 'datetime',

        # Math
        'math': 'math',
        'random': 'random',

        # HTTP
        'requests': 'requests',
        'urllib': 'urllib',

        # Subprocess
        'subprocess': 'subprocess',

        # Threading
        'Thread': 'threading',
        'Lock': 'threading',
        'Queue': 'queue',
        'ThreadPoolExecutor': 'concurrent.futures',
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.project_symbols: Dict[str, str] = {}  # symbol -> module path
        self._index_project()

    def _index_project(self):
        """Index all symbols defined in project files"""
        for py_file in self.project_root.rglob("*.py"):
            if 'venv' in str(py_file) or '.venv' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # Get module path relative to project root
                rel_path = py_file.relative_to(self.project_root)
                module_path = str(rel_path.with_suffix('')).replace('/', '.')

                # Extract all defined symbols
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.project_symbols[node.name] = module_path
                    elif isinstance(node, ast.ClassDef):
                        self.project_symbols[node.name] = module_path
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.project_symbols[target.id] = module_path
            except Exception:
                continue

    def analyze_file(self, filepath: Path) -> List[ImportSuggestion]:
        """Analyze a file and suggest missing imports"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
        except Exception:
            return []

        # Get current imports
        current_imports = self._get_current_imports(tree)

        # Get all used symbols
        used_symbols = self._get_used_symbols(tree)

        # Find missing imports
        suggestions = []

        for symbol in used_symbols:
            # Skip if already imported
            if symbol in current_imports:
                continue

            # Check if it's a stdlib symbol
            if symbol in self.STDLIB_SYMBOLS:
                module = self.STDLIB_SYMBOLS[symbol]
                suggestions.append(ImportSuggestion(
                    module=module,
                    names=[symbol] if symbol != module else [],
                    import_type='from_import' if symbol != module else 'import',
                    line_number=self._find_import_insertion_line(tree),
                    reason=f"'{symbol}' is used but not imported"
                ))

            # Check if it's a project symbol
            elif symbol in self.project_symbols:
                module = self.project_symbols[symbol]
                suggestions.append(ImportSuggestion(
                    module=module,
                    names=[symbol],
                    import_type='from_import',
                    line_number=self._find_import_insertion_line(tree),
                    reason=f"'{symbol}' is defined in {module}"
                ))

        return suggestions

    def _get_current_imports(self, tree: ast.AST) -> Set[str]:
        """Get all currently imported symbols"""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name)

        return imports

    def _get_used_symbols(self, tree: ast.AST) -> Set[str]:
        """Get all symbols used in the code"""
        used = set()

        for node in ast.walk(tree):
            # Function/method calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Handle chained attributes: obj.method()
                    value = node.func.value
                    while isinstance(value, ast.Attribute):
                        value = value.value
                    if isinstance(value, ast.Name):
                        used.add(value.id)

            # Type annotations
            elif isinstance(node, ast.arg):
                if node.annotation:
                    if isinstance(node.annotation, ast.Name):
                        used.add(node.annotation.id)

            # Variable references
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):  # Only when used, not defined
                    used.add(node.id)

        return used

    def _find_import_insertion_line(self, tree: ast.AST) -> int:
        """Find the line number where imports should be inserted"""
        # Find last import statement
        last_import_line = 0

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                last_import_line = node.end_lineno or node.lineno
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                # Skip module docstring
                continue
            else:
                # Stop at first non-import statement
                break

        # Insert after last import, or after module docstring
        return last_import_line + 1 if last_import_line > 0 else 1

    def insert_imports(
        self,
        filepath: Path,
        suggestions: List[ImportSuggestion],
        auto_apply: bool = False
    ) -> bool:
        """Insert suggested imports into file"""
        if not suggestions:
            return False

        content = filepath.read_text()
        lines = content.split('\n')

        # Group suggestions by line number
        imports_by_line: Dict[int, List[str]] = {}

        for suggestion in suggestions:
            if suggestion.import_type == 'import':
                import_line = f"import {suggestion.module}"
            else:
                names = ', '.join(suggestion.names)
                import_line = f"from {suggestion.module} import {names}"

            line_num = suggestion.line_number
            if line_num not in imports_by_line:
                imports_by_line[line_num] = []
            imports_by_line[line_num].append(import_line)

        # Show preview
        print("\n" + "="*60)
        print("Suggested imports:")
        print("="*60)
        for suggestion in suggestions:
            if suggestion.import_type == 'import':
                print(f"  import {suggestion.module}")
            else:
                names = ', '.join(suggestion.names)
                print(f"  from {suggestion.module} import {names}")
            print(f"    → {suggestion.reason}")
        print("="*60 + "\n")

        # Ask for confirmation
        if not auto_apply:
            response = input("Add these imports? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Imports not added")
                return False

        # Insert imports
        for line_num in sorted(imports_by_line.keys(), reverse=True):
            import_lines = imports_by_line[line_num]
            # Insert at the specified line (0-indexed)
            for import_line in reversed(import_lines):
                lines.insert(line_num - 1, import_line)

        # Write back
        new_content = '\n'.join(lines)
        filepath.write_text(new_content)

        print(f"✅ Added {len(suggestions)} import(s) to {filepath}")
        return True

    def check_unused_imports(self, filepath: Path) -> List[str]:
        """Find imports that are not used"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
        except Exception:
            return []

        # Get current imports
        imported_symbols = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imported_symbols[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_symbols[name] = node.lineno

        # Get used symbols
        used_symbols = self._get_used_symbols(tree)

        # Find unused
        unused = []
        for symbol, line_num in imported_symbols.items():
            if symbol not in used_symbols:
                unused.append(f"Line {line_num}: '{symbol}' imported but not used")

        return unused


class ImportOptimizer:
    """Optimize import organization"""

    def __init__(self):
        self.stdlib_modules = {
            'os', 'sys', 'pathlib', 'collections', 'typing', 'dataclasses',
            'json', 're', 'datetime', 'time', 'math', 'random', 'asyncio',
            'subprocess', 'threading', 'queue', 'concurrent', 'functools'
        }

    def organize_imports(self, filepath: Path) -> str:
        """Organize imports following PEP 8"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
        except Exception:
            return content

        # Extract imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_line = ast.get_source_segment(content, node)

                if isinstance(node, ast.Import):
                    module = node.names[0].name.split('.')[0]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module.split('.')[0] if node.module else ''

                # Categorize
                if module in self.stdlib_modules:
                    stdlib_imports.append(import_line)
                elif module.startswith('.'):
                    local_imports.append(import_line)
                else:
                    third_party_imports.append(import_line)

        # Sort each group
        stdlib_imports.sort()
        third_party_imports.sort()
        local_imports.sort()

        # Rebuild import block
        import_block = []
        if stdlib_imports:
            import_block.extend(stdlib_imports)
        if third_party_imports:
            if import_block:
                import_block.append('')  # Blank line
            import_block.extend(third_party_imports)
        if local_imports:
            if import_block:
                import_block.append('')  # Blank line
            import_block.extend(local_imports)

        return '\n'.join(import_block)


# Tool integration
def suggest_imports_for_file(filepath: str, project_root: str = ".") -> Dict:
    """Tool function: Suggest imports for a file"""
    auto_import = AutoImport(Path(project_root))
    suggestions = auto_import.analyze_file(Path(filepath))

    return {
        "suggestions": [
            {
                "module": s.module,
                "names": s.names,
                "type": s.import_type,
                "reason": s.reason
            }
            for s in suggestions
        ],
        "count": len(suggestions)
    }


def check_unused_imports(filepath: str, project_root: str = ".") -> Dict:
    """Tool function: Check for unused imports"""
    auto_import = AutoImport(Path(project_root))
    unused = auto_import.check_unused_imports(Path(filepath))

    return {
        "unused": unused,
        "count": len(unused)
    }
