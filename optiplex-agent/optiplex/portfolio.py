"""Portfolio-wide task discovery and management"""
from pathlib import Path
from typing import List, Dict, Any
import json


class PortfolioScanner:
    """Scan entire project portfolio for tasks"""
    
    def __init__(self, portfolio_root: Path):
        self.portfolio_root = Path(portfolio_root)
    
    def find_all_projects(self) -> List[Path]:
        """Find all projects in portfolio"""
        projects = []
        
        # Look for directories with .git, package.json, Cargo.toml, setup.py, etc.
        markers = [".git", "package.json", "Cargo.toml", "setup.py", "pyproject.toml", "go.mod"]
        
        for item in self.portfolio_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it's a project
                for marker in markers:
                    if (item / marker).exists():
                        projects.append(item)
                        break
        
        return projects
    
    def scan_for_tasks(self) -> List[Dict[str, Any]]:
        """Scan all projects for tasks (TODOs, issues, etc.)"""
        all_tasks = []
        
        projects = self.find_all_projects()
        
        for project in projects:
            tasks = self._scan_project(project)
            all_tasks.extend(tasks)
        
        return all_tasks
    
    def _scan_project(self, project_path: Path) -> List[Dict[str, Any]]:
        """Scan a single project for tasks"""
        tasks = []
        task_id_counter = 0
        
        # 1. Check for TODO comments in code
        for code_file in project_path.rglob("*.py"):
            if "venv" in str(code_file) or ".git" in str(code_file):
                continue
                
            try:
                content = code_file.read_text()
                lines = content.splitlines()
                
                for i, line in enumerate(lines, 1):
                    if "TODO" in line or "FIXME" in line:
                        tasks.append({
                            "id": f"{project_path.name}_todo_{task_id_counter}",
                            "description": f"Address TODO in {code_file.relative_to(project_path)} line {i}: {line.strip()}",
                            "status": "pending",
                            "project": project_path.name,
                            "file": str(code_file),
                            "line": i,
                            "type": "todo",
                            "auto_discovered": True
                        })
                        task_id_counter += 1
            except Exception:
                pass
        
        # 2. Check for tasks.json in project
        project_tasks_file = project_path / "tasks.json"
        if project_tasks_file.exists():
            try:
                with open(project_tasks_file, 'r') as f:
                    data = json.load(f)
                    project_tasks = data.get("tasks", [])
                    
                    for task in project_tasks:
                        if task.get("status") == "pending":
                            task["project"] = project_path.name
                            task["type"] = "explicit"
                            tasks.append(task)
            except Exception:
                pass
        
        # 3. Check for uncommitted changes
        git_dir = project_path / ".git"
        if git_dir.exists():
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.stdout.strip():
                    tasks.append({
                        "id": f"{project_path.name}_git_uncommitted",
                        "description": f"Review and commit uncommitted changes in {project_path.name}",
                        "status": "pending",
                        "project": project_path.name,
                        "type": "git",
                        "auto_discovered": True
                    })
            except Exception:
                pass
        
        return tasks
    
    def create_master_task_list(self, output_file: Path) -> int:
        """Create a master task list for entire portfolio"""
        all_tasks = self.scan_for_tasks()
        
        # Group by project
        by_project = {}
        for task in all_tasks:
            project = task.get("project", "unknown")
            if project not in by_project:
                by_project[project] = []
            by_project[project].append(task)
        
        # Write to file
        from datetime import datetime
        with open(output_file, 'w') as f:
            json.dump({
                "created": datetime.now().isoformat(),
                "total_tasks": len(all_tasks),
                "projects": list(by_project.keys()),
                "tasks": all_tasks
            }, f, indent=2)
        
        return len(all_tasks)


def scan_portfolio(portfolio_root: str = None) -> List[Dict[str, Any]]:
    """Quick scan of portfolio for tasks"""
    if portfolio_root is None:
        # Try to find portfolio root
        possible_roots = [
            Path.home() / "Downloads/llm_automation/project_portfolio",
            Path.home() / "projects",
            Path.cwd().parent
        ]
        
        for root in possible_roots:
            if root.exists():
                portfolio_root = root
                break
    
    if portfolio_root is None:
        return []
    
    scanner = PortfolioScanner(portfolio_root)
    return scanner.scan_for_tasks()

