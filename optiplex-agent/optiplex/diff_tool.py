"""Interactive diff viewing and application"""
import difflib
from pathlib import Path
from typing import Optional


class DiffApplier:
    """Apply and preview code diffs interactively"""

    def __init__(self, auto_apply: bool = False):
        self.auto_apply = auto_apply

    def generate_unified_diff(
        self,
        filepath: str,
        old_content: str,
        new_content: str
    ) -> str:
        """Generate a unified diff"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm=''
        )

        return ''.join(diff)

    def colorize_diff(self, diff: str) -> str:
        """Add ANSI colors to diff"""
        lines = []
        for line in diff.split('\n'):
            if line.startswith('+++') or line.startswith('---'):
                # File headers - bold
                lines.append(f"\033[1m{line}\033[0m")
            elif line.startswith('+'):
                # Additions - green
                lines.append(f"\033[32m{line}\033[0m")
            elif line.startswith('-'):
                # Deletions - red
                lines.append(f"\033[31m{line}\033[0m")
            elif line.startswith('@@'):
                # Hunk headers - cyan
                lines.append(f"\033[36m{line}\033[0m")
            else:
                lines.append(line)

        return '\n'.join(lines)

    def show_diff(self, filepath: str, old_content: str, new_content: str):
        """Show colored diff"""
        diff = self.generate_unified_diff(filepath, old_content, new_content)

        if not diff:
            print("No changes")
            return False

        colored_diff = self.colorize_diff(diff)
        print("\n" + "="*60)
        print(f"Changes to {filepath}:")
        print("="*60)
        print(colored_diff)
        print("="*60 + "\n")

        return True

    def prompt_apply(self) -> str:
        """Prompt user to apply changes"""
        while True:
            response = input("Apply changes? (y)es / (n)o / (e)dit / (s)how again: ").strip().lower()

            if response in ['y', 'yes']:
                return 'apply'
            elif response in ['n', 'no']:
                return 'reject'
            elif response in ['e', 'edit']:
                return 'edit'
            elif response in ['s', 'show']:
                return 'show'
            else:
                print("Invalid choice. Please enter y, n, e, or s.")

    def apply_with_confirmation(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        create_backup: bool = True
    ) -> bool:
        """Show diff and apply with user confirmation"""

        # Show the diff
        has_changes = self.show_diff(filepath, old_content, new_content)

        if not has_changes:
            return False

        # Auto-apply if enabled
        if self.auto_apply:
            print("Auto-applying changes...")
            return self._write_file(filepath, new_content, create_backup)

        # Interactive prompt
        while True:
            action = self.prompt_apply()

            if action == 'apply':
                success = self._write_file(filepath, new_content, create_backup)
                if success:
                    print("✅ Changes applied successfully")
                else:
                    print("❌ Failed to apply changes")
                return success

            elif action == 'reject':
                print("❌ Changes rejected")
                return False

            elif action == 'edit':
                print("\n💡 Edit mode:")
                print("1. Open file in your editor")
                print("2. Make manual changes")
                print("3. Come back and choose (n)o to skip auto-apply")
                continue

            elif action == 'show':
                self.show_diff(filepath, old_content, new_content)
                continue

    def _write_file(self, filepath: str, content: str, create_backup: bool) -> bool:
        """Write file with optional backup"""
        try:
            path = Path(filepath)

            # Create backup if requested
            if create_backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.bak')
                backup_path.write_text(path.read_text())

            # Write new content
            path.write_text(content)
            return True

        except Exception as e:
            print(f"Error writing file: {e}")
            return False

    def apply_edit(
        self,
        filepath: str,
        old_text: str,
        new_text: str,
        create_backup: bool = True
    ) -> bool:
        """Apply a search-and-replace edit with diff preview"""
        path = Path(filepath)

        if not path.exists():
            print(f"Error: File {filepath} does not exist")
            return False

        current_content = path.read_text()

        # Check if old_text exists
        if old_text not in current_content:
            print(f"Error: Text not found in {filepath}")
            print(f"Searching for: {old_text[:100]}...")
            return False

        # Generate new content
        new_content = current_content.replace(old_text, new_text, 1)

        # Show diff and confirm
        return self.apply_with_confirmation(filepath, current_content, new_content, create_backup)
