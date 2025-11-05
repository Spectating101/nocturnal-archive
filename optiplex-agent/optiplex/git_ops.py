"""Git operations for Optiplex Agent"""
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class GitStatus:
    """Git repository status"""
    branch: str
    staged: List[str]
    unstaged: List[str]
    untracked: List[str]
    is_clean: bool

class GitOperations:
    """Manages git operations"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not (self.repo_path / '.git').exists():
            raise ValueError(f"Not a git repository: {repo_path}")
    
    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command"""
        return subprocess.run(
            ['git'] + cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check
        )
    
    def get_status(self) -> GitStatus:
        """Get current git status"""
        result = self.run_command(['status', '--porcelain=v1', '-b'])
        
        branch = "unknown"
        staged = []
        unstaged = []
        untracked = []
        
        for line in result.stdout.splitlines():
            if line.startswith('##'):
                # Branch info
                branch = line.split()[1].split('...')[0]
            else:
                status = line[:2]
                filepath = line[3:]
                
                if status[0] != ' ' and status[0] != '?':
                    staged.append(filepath)
                if status[1] != ' ' and status[1] != '?':
                    unstaged.append(filepath)
                if status == '??':
                    untracked.append(filepath)
        
        return GitStatus(
            branch=branch,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
            is_clean=not (staged or unstaged or untracked)
        )
    
    def get_diff(self, filepath: Optional[str] = None, staged: bool = False) -> str:
        """Get git diff"""
        cmd = ['diff']
        if staged:
            cmd.append('--staged')
        if filepath:
            cmd.append(filepath)
        
        result = self.run_command(cmd)
        return result.stdout
    
    def stage_files(self, filepaths: List[str]) -> bool:
        """Stage files for commit"""
        try:
            self.run_command(['add'] + filepaths)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def unstage_files(self, filepaths: List[str]) -> bool:
        """Unstage files"""
        try:
            self.run_command(['reset', 'HEAD'] + filepaths)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def commit(self, message: str, allow_empty: bool = False) -> bool:
        """Create a commit"""
        try:
            cmd = ['commit', '-m', message]
            if allow_empty:
                cmd.append('--allow-empty')
            self.run_command(cmd)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """Create a new branch"""
        try:
            if checkout:
                self.run_command(['checkout', '-b', branch_name])
            else:
                self.run_command(['branch', branch_name])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout a branch"""
        try:
            self.run_command(['checkout', branch_name])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def list_branches(self) -> List[str]:
        """List all branches"""
        result = self.run_command(['branch'])
        branches = []
        for line in result.stdout.splitlines():
            branch = line.strip().lstrip('* ')
            branches.append(branch)
        return branches
    
    def get_log(self, max_count: int = 10, filepath: Optional[str] = None) -> List[Dict[str, str]]:
        """Get commit log"""
        cmd = ['log', f'--max-count={max_count}', '--format=%H|%an|%ae|%at|%s']
        if filepath:
            cmd.append(filepath)
        
        result = self.run_command(cmd)
        commits = []
        
        for line in result.stdout.splitlines():
            parts = line.split('|')
            if len(parts) == 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'timestamp': parts[3],
                    'message': parts[4]
                })
        
        return commits
    
    def get_current_branch(self) -> str:
        """Get current branch name"""
        result = self.run_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        return result.stdout.strip()
    
    def is_repo_clean(self) -> bool:
        """Check if repository is clean"""
        status = self.get_status()
        return status.is_clean
    
    def get_remote_url(self, remote: str = 'origin') -> Optional[str]:
        """Get remote URL"""
        try:
            result = self.run_command(['remote', 'get-url', remote])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
