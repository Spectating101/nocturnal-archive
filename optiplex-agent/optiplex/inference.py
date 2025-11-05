"""Project inference engine - understands what you're building"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import subprocess


class ProjectInferenceEngine:
    """Analyzes a project to understand what it is and what needs to be done next"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.context = {}
    
    def analyze_project(self) -> Dict[str, Any]:
        """Deep analysis of project to understand intent and state"""
        
        analysis = {
            "project_name": self.project_path.name,
            "project_type": self._infer_project_type(),
            "tech_stack": self._detect_tech_stack(),
            "purpose": self._infer_purpose(),
            "current_state": self._assess_current_state(),
            "next_steps": self._infer_next_steps(),
            "recent_work": self._analyze_recent_work(),
            "patterns": self._detect_patterns()
        }
        
        return analysis
    
    def _infer_project_type(self) -> str:
        """Guess project type from structure"""
        
        # Check for common markers
        has_api = any([
            (self.project_path / "api").exists(),
            (self.project_path / "src" / "routes").exists(),
            any(self.project_path.rglob("*api*.py"))
        ])
        
        has_cli = any([
            (self.project_path / "cli.py").exists(),
            any(self.project_path.rglob("*cli*.py"))
        ])
        
        has_frontend = any([
            (self.project_path / "frontend").exists(),
            (self.project_path / "public").exists(),
            (self.project_path / "src" / "components").exists()
        ])
        
        has_ml = any([
            any(self.project_path.rglob("*model*.py")),
            any(self.project_path.rglob("*train*.py")),
            (self.project_path / "models").exists()
        ])
        
        if has_api and has_frontend:
            return "full-stack-web-app"
        elif has_api:
            return "backend-api"
        elif has_cli:
            return "cli-tool"
        elif has_ml:
            return "ml-pipeline"
        else:
            return "library"
    
    def _detect_tech_stack(self) -> Dict[str, Any]:
        """Detect languages, frameworks, dependencies"""
        
        stack = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "deployment": []
        }
        
        # Check for language markers
        if (self.project_path / "setup.py").exists() or any(self.project_path.rglob("*.py")):
            stack["languages"].append("python")
            
            # Check for frameworks
            if self._file_contains_pattern("requirements.txt", ["flask", "Flask"]):
                stack["frameworks"].append("Flask")
            if self._file_contains_pattern("requirements.txt", ["fastapi", "FastAPI"]):
                stack["frameworks"].append("FastAPI")
            if self._file_contains_pattern("requirements.txt", ["django", "Django"]):
                stack["frameworks"].append("Django")
        
        if (self.project_path / "Cargo.toml").exists():
            stack["languages"].append("rust")
        
        if (self.project_path / "package.json").exists():
            stack["languages"].append("javascript/typescript")
            
            # Check for frameworks
            pkg_json = self.project_path / "package.json"
            if pkg_json.exists():
                try:
                    with open(pkg_json) as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        
                        if "react" in deps:
                            stack["frameworks"].append("React")
                        if "vue" in deps:
                            stack["frameworks"].append("Vue")
                        if "express" in deps:
                            stack["frameworks"].append("Express")
                except:
                    pass
        
        # Check for databases
        if self._file_contains_pattern("requirements.txt", ["psycopg", "postgres"]):
            stack["databases"].append("PostgreSQL")
        if self._file_contains_pattern("requirements.txt", ["pymongo", "mongodb"]):
            stack["databases"].append("MongoDB")
        
        # Check for deployment
        if (self.project_path / "Dockerfile").exists():
            stack["deployment"].append("Docker")
        if (self.project_path / "Procfile").exists():
            stack["deployment"].append("Heroku")
        if (self.project_path / ".github" / "workflows").exists():
            stack["deployment"].append("GitHub Actions")
        
        return stack
    
    def _infer_purpose(self) -> str:
        """Read README and docs to understand project purpose"""
        
        # Try to read README
        readme_files = [
            self.project_path / "README.md",
            self.project_path / "README",
            self.project_path / "readme.md"
        ]
        
        for readme in readme_files:
            if readme.exists():
                try:
                    content = readme.read_text()
                    
                    # Extract first paragraph after title
                    lines = content.split('\n')
                    description_lines = []
                    
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            description_lines.append(line.strip())
                            if len(description_lines) >= 3:
                                break
                    
                    if description_lines:
                        return ' '.join(description_lines)[:500]
                except:
                    pass
        
        # Fallback: guess from directory name
        name = self.project_path.name.lower()
        if "api" in name:
            return f"API service for {name.replace('api', '').replace('-', ' ')}"
        elif "cli" in name:
            return f"Command-line tool for {name.replace('cli', '').replace('-', ' ')}"
        else:
            return f"Project: {name}"
    
    def _assess_current_state(self) -> Dict[str, Any]:
        """Evaluate project maturity and completeness"""
        
        state = {
            "maturity": "unknown",
            "has_tests": False,
            "has_docs": False,
            "has_ci_cd": False,
            "has_deployment": False,
            "code_quality": "unknown",
            "completeness_score": 0.0
        }
        
        # Check for tests
        test_indicators = [
            self.project_path / "tests",
            self.project_path / "test",
            any(self.project_path.rglob("test_*.py")),
            any(self.project_path.rglob("*_test.py"))
        ]
        state["has_tests"] = any(indicator if isinstance(indicator, bool) else indicator.exists() 
                                  for indicator in test_indicators)
        
        # Check for docs
        doc_indicators = [
            self.project_path / "docs",
            self.project_path / "README.md",
            any(self.project_path.rglob("*.md"))
        ]
        state["has_docs"] = any(indicator if isinstance(indicator, bool) else indicator.exists() 
                                 for indicator in doc_indicators)
        
        # Check for CI/CD
        state["has_ci_cd"] = (self.project_path / ".github" / "workflows").exists() or \
                             (self.project_path / ".gitlab-ci.yml").exists()
        
        # Check for deployment config
        state["has_deployment"] = any([
            (self.project_path / "Dockerfile").exists(),
            (self.project_path / "Procfile").exists(),
            (self.project_path / "docker-compose.yml").exists()
        ])
        
        # Calculate completeness score
        score = 0.0
        if state["has_tests"]: score += 0.25
        if state["has_docs"]: score += 0.25
        if state["has_ci_cd"]: score += 0.2
        if state["has_deployment"]: score += 0.3
        
        state["completeness_score"] = score
        
        # Infer maturity
        if score >= 0.8:
            state["maturity"] = "production-ready"
        elif score >= 0.5:
            state["maturity"] = "beta"
        elif score >= 0.25:
            state["maturity"] = "alpha"
        else:
            state["maturity"] = "experimental"
        
        return state
    
    def _infer_next_steps(self) -> List[str]:
        """Based on current state, suggest what to build next"""
        
        next_steps = []
        state = self._assess_current_state()
        project_type = self._infer_project_type()
        
        # Production readiness checklist
        if not state["has_tests"]:
            next_steps.append("Add test suite (unit tests, integration tests)")
        
        if not state["has_docs"]:
            next_steps.append("Create documentation (API docs, user guide)")
        
        if project_type in ["backend-api", "full-stack-web-app"]:
            if not self._has_feature("error_handling"):
                next_steps.append("Add comprehensive error handling and logging")
            
            if not self._has_feature("monitoring"):
                next_steps.append("Add monitoring/observability (metrics, health checks)")
            
            if not self._has_feature("authentication"):
                next_steps.append("Implement authentication/authorization")
        
        if not state["has_deployment"]:
            next_steps.append("Create deployment configuration (Docker, CI/CD)")
        
        # Check for common missing pieces
        if not self._has_feature("validation"):
            next_steps.append("Add input validation and sanitization")
        
        if not self._has_feature("rate_limiting"):
            next_steps.append("Implement rate limiting/throttling")
        
        # Check git status for uncommitted work
        if self._has_uncommitted_changes():
            next_steps.append("Review and commit current changes")
        
        return next_steps
    
    def _analyze_recent_work(self) -> Dict[str, Any]:
        """Analyze recent git commits to understand what was being worked on"""
        
        recent_work = {
            "recent_commits": [],
            "active_branch": None,
            "last_focus_area": None
        }
        
        try:
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                recent_work["recent_commits"] = commits[:5]
                
                # Analyze commit messages to understand focus
                commit_text = ' '.join(commits).lower()
                
                if any(word in commit_text for word in ["test", "testing"]):
                    recent_work["last_focus_area"] = "testing"
                elif any(word in commit_text for word in ["deploy", "docker", "ci"]):
                    recent_work["last_focus_area"] = "deployment"
                elif any(word in commit_text for word in ["fix", "bug", "error"]):
                    recent_work["last_focus_area"] = "bug_fixes"
                elif any(word in commit_text for word in ["feat", "feature", "add"]):
                    recent_work["last_focus_area"] = "feature_development"
            
            # Get active branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                recent_work["active_branch"] = result.stdout.strip()
        
        except Exception:
            pass
        
        return recent_work
    
    def _detect_patterns(self) -> List[str]:
        """Detect architectural patterns and design choices"""
        
        patterns = []
        
        # Check for common patterns
        if (self.project_path / "src" / "routes").exists() or \
           (self.project_path / "routes").exists():
            patterns.append("MVC/Route-based architecture")
        
        if any(self.project_path.rglob("*service*.py")):
            patterns.append("Service layer pattern")
        
        if any(self.project_path.rglob("*repository*.py")):
            patterns.append("Repository pattern")
        
        if (self.project_path / "migrations").exists():
            patterns.append("Database migrations")
        
        if self._file_contains_pattern("*.py", ["async def", "await "]):
            patterns.append("Async/await concurrency")
        
        return patterns
    
    def _has_feature(self, feature: str) -> bool:
        """Check if project has a specific feature"""
        
        feature_markers = {
            "error_handling": ["try:", "except", "Error", "Exception"],
            "monitoring": ["metrics", "prometheus", "statsd", "logging"],
            "authentication": ["jwt", "auth", "token", "login"],
            "validation": ["validator", "pydantic", "schema", "validate"],
            "rate_limiting": ["rate_limit", "throttle", "RateLimiter"]
        }
        
        markers = feature_markers.get(feature, [])
        
        # Search in Python files
        for py_file in self.project_path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                if any(marker in content for marker in markers):
                    return True
            except:
                pass
        
        return False
    
    def _has_uncommitted_changes(self) -> bool:
        """Check for uncommitted git changes"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def _file_contains_pattern(self, filename_pattern: str, search_patterns: List[str]) -> bool:
        """Check if files matching pattern contain any of the search patterns"""
        
        try:
            for file in self.project_path.rglob(filename_pattern):
                if "venv" in str(file) or "node_modules" in str(file):
                    continue
                
                try:
                    content = file.read_text()
                    if any(pattern in content for pattern in search_patterns):
                        return True
                except:
                    pass
        except:
            pass
        
        return False
    
    def generate_work_plan(self) -> Dict[str, Any]:
        """Generate a concrete work plan based on analysis"""
        
        analysis = self.analyze_project()
        
        plan = {
            "project": analysis["project_name"],
            "understanding": analysis["purpose"],
            "current_maturity": analysis["current_state"]["maturity"],
            "priority_tasks": [],
            "estimated_hours": 0
        }
        
        # Prioritize based on maturity and type
        next_steps = analysis["next_steps"]
        
        for step in next_steps[:5]:  # Top 5 priorities
            task = {
                "description": step,
                "priority": self._calculate_priority(step, analysis),
                "estimated_hours": self._estimate_hours(step)
            }
            plan["priority_tasks"].append(task)
            plan["estimated_hours"] += task["estimated_hours"]
        
        return plan
    
    def _calculate_priority(self, task: str, analysis: Dict) -> str:
        """Calculate task priority based on context"""
        
        task_lower = task.lower()
        maturity = analysis["current_state"]["maturity"]
        
        # High priority: Critical for production
        if any(word in task_lower for word in ["error", "security", "auth", "validation"]):
            return "critical"
        
        # High priority for almost-done projects
        if maturity in ["beta", "production-ready"]:
            if any(word in task_lower for word in ["test", "doc", "deploy"]):
                return "high"
        
        # Medium priority: Nice to have
        if any(word in task_lower for word in ["monitoring", "logging", "ci"]):
            return "medium"
        
        return "low"
    
    def _estimate_hours(self, task: str) -> float:
        """Estimate hours for a task"""
        
        task_lower = task.lower()
        
        if "test" in task_lower:
            return 3.0  # Writing tests takes time
        elif "docs" in task_lower or "documentation" in task_lower:
            return 2.0
        elif "deploy" in task_lower or "docker" in task_lower:
            return 1.5
        elif "monitoring" in task_lower or "logging" in task_lower:
            return 2.5
        else:
            return 1.0


