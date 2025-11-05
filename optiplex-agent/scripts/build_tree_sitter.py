#!/usr/bin/env python3
"""Build Tree-sitter language libraries for Optiplex"""
import os
import sys
import subprocess
from pathlib import Path
import shutil

# Languages to build
LANGUAGES = {
    'python': 'https://github.com/tree-sitter/tree-sitter-python',
    'javascript': 'https://github.com/tree-sitter/tree-sitter-javascript',
    'typescript': 'https://github.com/tree-sitter/tree-sitter-typescript',
    'go': 'https://github.com/tree-sitter/tree-sitter-go',
    'rust': 'https://github.com/tree-sitter/tree-sitter-rust',
}

def check_dependencies():
    """Check if required tools are installed"""
    print("Checking dependencies...")

    # Check git
    if shutil.which('git') is None:
        print("❌ git is not installed. Please install git first.")
        return False

    # Check tree-sitter package
    try:
        import tree_sitter
        print("✅ tree-sitter package found")
    except ImportError:
        print("❌ tree-sitter package not found")
        print("   Install with: pip install tree-sitter")
        return False

    return True


def clone_language_repo(name: str, url: str, temp_dir: Path) -> Path:
    """Clone a language repository"""
    repo_path = temp_dir / f'tree-sitter-{name}'

    if repo_path.exists():
        print(f"  Repository already exists, pulling latest...")
        subprocess.run(['git', 'pull'], cwd=repo_path, capture_output=True)
    else:
        print(f"  Cloning {name}...")
        result = subprocess.run(
            ['git', 'clone', '--depth=1', url, str(repo_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  ❌ Failed to clone {name}: {result.stderr}")
            return None

    return repo_path


def build_language(name: str, repo_path: Path, build_dir: Path) -> bool:
    """Build a language library"""
    try:
        from tree_sitter import Language

        # Determine source directory
        src_dir = repo_path
        if name == 'typescript':
            # TypeScript has subdirectories
            src_dir = repo_path / 'typescript'

        # Build library
        output_path = build_dir / f'tree-sitter-{name}.so'

        print(f"  Building {name}...")
        Language.build_library(
            str(output_path),
            [str(src_dir)]
        )

        print(f"  ✅ Built {output_path}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to build {name}: {e}")
        return False


def main():
    """Main build script"""
    print("="*60)
    print("Tree-sitter Language Builder for Optiplex")
    print("="*60)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    temp_dir = project_root / '.tree-sitter-build'
    build_dir = project_root / 'tree-sitter-libs'

    temp_dir.mkdir(exist_ok=True)
    build_dir.mkdir(exist_ok=True)

    print(f"\nBuild directory: {build_dir}")
    print(f"Temporary directory: {temp_dir}\n")

    # Build each language
    success_count = 0

    for name, url in LANGUAGES.items():
        print(f"Building {name}...")

        # Clone repo
        repo_path = clone_language_repo(name, url, temp_dir)
        if not repo_path:
            continue

        # Build library
        if build_language(name, repo_path, build_dir):
            success_count += 1

    # Cleanup
    print(f"\nCleaning up temporary files...")
    shutil.rmtree(temp_dir)

    # Summary
    print("\n" + "="*60)
    print(f"Build complete: {success_count}/{len(LANGUAGES)} languages built")
    print("="*60)

    if success_count == len(LANGUAGES):
        print(f"\n✅ All language libraries built successfully!")
        print(f"\nLibraries installed in: {build_dir}")
        print(f"\nTo use Tree-sitter in Optiplex:")
        print(f"  export TREE_SITTER_LIB_PATH={build_dir}")
        print(f"  optiplex")
    else:
        print(f"\n⚠️  Some builds failed. Check errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
