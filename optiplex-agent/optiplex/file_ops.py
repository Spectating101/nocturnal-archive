"""File operations with backup support"""
import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import hashlib

class FileOperations:
    """Manages file operations with backup support"""
    
    def __init__(self, root_dir: str, backup_dir: str = ".optiplex/backups", max_backups: int = 10):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / backup_dir
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Get MD5 hash of file content"""
        if not filepath.exists():
            return ""
        return hashlib.md5(filepath.read_bytes()).hexdigest()
    
    def _create_backup(self, filepath: Path) -> Optional[Path]:
        """Create a backup of the file"""
        if not filepath.exists():
            return None
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = filepath.relative_to(self.root_dir)
        backup_path = self.backup_dir / f"{relative_path.parent / relative_path.stem}_{timestamp}{relative_path.suffix}"
        
        # Create backup directory
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(filepath, backup_path)
        
        # Clean old backups
        self._cleanup_old_backups(filepath)
        
        return backup_path
    
    def _cleanup_old_backups(self, filepath: Path):
        """Remove old backups keeping only max_backups most recent"""
        relative_path = filepath.relative_to(self.root_dir)
        pattern = f"{relative_path.stem}_*{relative_path.suffix}"
        backup_parent = self.backup_dir / relative_path.parent
        
        if not backup_parent.exists():
            return
        
        backups = sorted(backup_parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for old_backup in backups[self.max_backups:]:
            old_backup.unlink()
    
    def read_file(self, filepath: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Read file content, optionally with line range (1-indexed)"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        content = path.read_text()
        
        # If line range specified, extract those lines
        if start_line is not None or end_line is not None:
            lines = content.splitlines()
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else len(lines)
            selected_lines = lines[start_idx:end_idx]
            return "\n".join(f"{i+start_idx+1}: {line}" for i, line in enumerate(selected_lines))
        
        return content
    
    def write_file(self, filepath: str, content: str, create_backup: bool = True) -> bool:
        """Write content to file with optional backup"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        try:
            # Create backup if file exists
            if create_backup and path.exists():
                self._create_backup(path)
            
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    def edit_file(self, filepath: str, old_content: str, new_content: str, create_backup: bool = True) -> bool:
        """Edit file by replacing old_content with new_content"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        try:
            # Read current content
            current = path.read_text()
            
            # Check if old_content exists
            if old_content not in current:
                print(f"Content not found in file: {filepath}")
                return False
            
            # Create backup
            if create_backup:
                self._create_backup(path)
            
            # Replace content
            updated = current.replace(old_content, new_content)
            path.write_text(updated)
            return True
        except Exception as e:
            print(f"Error editing file: {e}")
            return False
    
    def delete_file(self, filepath: str, create_backup: bool = True) -> bool:
        """Delete file with optional backup"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        try:
            if not path.exists():
                return False
            
            # Create backup
            if create_backup:
                self._create_backup(path)
            
            # Delete file
            path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_backups(self, filepath: str) -> List[Path]:
        """List all backups for a file"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        relative_path = path.relative_to(self.root_dir)
        pattern = f"{relative_path.stem}_*{relative_path.suffix}"
        backup_parent = self.backup_dir / relative_path.parent
        
        if not backup_parent.exists():
            return []
        
        return sorted(backup_parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    def restore_backup(self, filepath: str, backup_path: Path) -> bool:
        """Restore a file from backup"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        try:
            if not backup_path.exists():
                return False
            
            # Create backup of current version first
            if path.exists():
                self._create_backup(path)
            
            # Restore from backup
            shutil.copy2(backup_path, path)
            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def file_exists(self, filepath: str) -> bool:
        """Check if file exists"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        return path.exists()
    
    def get_file_info(self, filepath: str) -> dict:
        """Get file information"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.root_dir / path
        
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'hash': self._get_file_hash(path)
        }
