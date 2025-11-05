"""Autonomous agent that works independently"""
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from .agent import OptiplexAgent, AgentResponse
from .scheduler_bridge import SchedulerBridge
from .inference import ProjectInferenceEngine
from .cursor_bridge import check_cursor_continuation


class AutonomousMode:
    """Run Optiplex autonomously without human intervention"""
    
    def __init__(
        self,
        agent: OptiplexAgent,
        task_file: str = "tasks.json",
        log_file: str = "autonomous.log",
        max_iterations: int = 50,
        respect_scheduler: bool = True,
        smart_mode: bool = True
    ):
        self.agent = agent
        self.task_file = Path(agent.root_dir) / task_file
        self.log_file = Path(agent.root_dir) / log_file
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self.respect_scheduler = respect_scheduler
        self.scheduler = SchedulerBridge() if respect_scheduler else None
        self.smart_mode = smart_mode  # Use inference engine to understand project
        self.inference_engine = ProjectInferenceEngine(agent.root_dir) if smart_mode else None
        
    def log(self, message: str, level: str = "INFO"):
        """Log autonomous actions"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from task file"""
        if not self.task_file.exists():
            return []
        
        try:
            with open(self.task_file, "r") as f:
                data = json.load(f)
                return data.get("tasks", [])
        except Exception as e:
            self.log(f"Failed to load tasks: {e}", "ERROR")
            return []
    
    def save_tasks(self, tasks: List[Dict[str, Any]]):
        """Save tasks to file"""
        try:
            with open(self.task_file, "w") as f:
                json.dump({"tasks": tasks, "updated": datetime.now().isoformat()}, f, indent=2)
        except Exception as e:
            self.log(f"Failed to save tasks: {e}", "ERROR")
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task autonomously"""
        task_id = task.get("id", "unknown")
        description = task.get("description", "")
        
        self.log(f"Starting task {task_id}: {description}")
        
        try:
            # Execute the task
            response: AgentResponse = self.agent.chat(description)
            
            if response.success:
                self.log(f"✅ Task {task_id} completed", "SUCCESS")
                self.log(f"Result: {response.content[:200]}...")
                task["status"] = "completed"
                task["result"] = response.content
                task["completed_at"] = datetime.now().isoformat()
                return True
            else:
                self.log(f"❌ Task {task_id} failed: {response.error}", "ERROR")
                task["status"] = "failed"
                task["error"] = response.error
                return False
                
        except Exception as e:
            self.log(f"❌ Task {task_id} exception: {str(e)}", "ERROR")
            task["status"] = "failed"
            task["error"] = str(e)
            return False
    
    def self_reflect(self) -> Optional[str]:
        """Reflect on current state and suggest next actions"""
        reflection_prompt = """
Analyze the current codebase state:
1. Check git status for uncommitted changes
2. Look for TODO comments in the code
3. Check for linting errors or test failures
4. Suggest the most important task to work on next

Be specific and actionable. If nothing needs doing, say "All clear."
"""
        
        try:
            response: AgentResponse = self.agent.chat(reflection_prompt)
            if response.success:
                return response.content
        except Exception as e:
            self.log(f"Self-reflection failed: {e}", "ERROR")
        
        return None
    
    def _merge_inferred_tasks(self, work_plan: Dict[str, Any]):
        """Merge inferred tasks with existing task list"""
        
        tasks = self.load_tasks()
        
        # Add inferred tasks if not already present
        for plan_task in work_plan["priority_tasks"]:
            task_desc = plan_task["description"]
            
            # Check if similar task already exists
            exists = any(
                task_desc.lower() in existing["description"].lower() or
                existing["description"].lower() in task_desc.lower()
                for existing in tasks
            )
            
            if not exists:
                tasks.append({
                    "id": f"inferred_{len(tasks)}",
                    "description": task_desc,
                    "status": "pending",
                    "priority": plan_task["priority"],
                    "estimated_hours": plan_task["estimated_hours"],
                    "auto_inferred": True
                })
        
        self.save_tasks(tasks)
        self.log(f"📋 Merged inferred tasks. Total tasks: {len(tasks)}")
    
    def _execute_cursor_continuation(self, cursor_prompt: str):
        """Execute task continuation from Cursor"""
        
        self.log("💬 Asking agent to continue Cursor's work...")
        
        try:
            response = self.agent.chat(cursor_prompt)
            
            self.log(f"✅ Cursor continuation completed")
            self.log(f"Response: {response.content[:200]}...")
            
            # Check if any files were modified
            if response.tool_calls:
                self.log(f"🔧 Modified {len(response.tool_calls)} files")
        
        except Exception as e:
            self.log(f"❌ Cursor continuation failed: {e}", "ERROR")
    
    def run(self, auto_reflect: bool = True):
        """Run autonomously until tasks are done or max iterations reached"""
        self.log("🚀 Starting SMART autonomous mode")
        self.log(f"Max iterations: {self.max_iterations}")
        
        # STEP 1: Check Cursor continuation
        cursor_prompt = check_cursor_continuation(Path(self.agent.root_dir))
        if cursor_prompt:
            self.log("🔄 Detected Cursor session - will continue from there!")
            self.log(f"Context: {cursor_prompt[:200]}...")
        
        # STEP 2: Understand the project (inference engine)
        if self.smart_mode and self.inference_engine:
            self.log("🧠 Analyzing project to understand what you're building...")
            analysis = self.inference_engine.analyze_project()
            
            self.log(f"📋 Project Type: {analysis['project_type']}")
            self.log(f"🎯 Purpose: {analysis['purpose'][:150]}...")
            self.log(f"📊 Maturity: {analysis['current_state']['maturity']} ({analysis['current_state']['completeness_score']*100:.0f}% complete)")
            
            # Generate smart work plan
            work_plan = self.inference_engine.generate_work_plan()
            self.log(f"📝 Generated work plan: {len(work_plan['priority_tasks'])} tasks, ~{work_plan['estimated_hours']}h")
            
            # Add inferred tasks to task list
            self._merge_inferred_tasks(work_plan)
        
        # STEP 3: Check scheduler if enabled
        if self.respect_scheduler and self.scheduler:
            self.log("🔍 Checking Molina scheduler for safe execution window...")
            status = self.scheduler.get_resource_status()
            self.log(f"Scheduler status: {status}")
            
            if not self.scheduler.is_safe_to_run():
                self.log("⏸️  User is active. Waiting for idle window...")
                if not self.scheduler.wait_for_safe_window():
                    self.log("❌ Autonomous mode cancelled by user")
                    return
        
        # If Cursor continuation available, prioritize that
        if cursor_prompt:
            self.log("🎯 Executing Cursor continuation task first...")
            self._execute_cursor_continuation(cursor_prompt)
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            self.log(f"\n{'='*60}")
            self.log(f"Iteration {self.iteration_count}/{self.max_iterations}")
            
            # Load pending tasks
            tasks = self.load_tasks()
            pending_tasks = [t for t in tasks if t.get("status") == "pending"]
            
            if not pending_tasks:
                if auto_reflect:
                    self.log("No pending tasks. Running self-reflection...")
                    next_action = self.self_reflect()
                    
                    if next_action and "all clear" not in next_action.lower():
                        self.log(f"Self-reflection suggests: {next_action[:200]}...")
                        
                        # Create a new task from reflection
                        new_task = {
                            "id": f"auto_{self.iteration_count}",
                            "description": next_action,
                            "status": "pending",
                            "created_at": datetime.now().isoformat(),
                            "auto_generated": True
                        }
                        tasks.append(new_task)
                        self.save_tasks(tasks)
                        continue
                    else:
                        self.log("✅ All tasks complete. Entering idle mode.")
                        break
                else:
                    self.log("No pending tasks. Exiting.")
                    break
            
            # Execute next pending task
            next_task = pending_tasks[0]
            success = self.execute_task(next_task)
            
            # Save updated tasks
            self.save_tasks(tasks)
            
            # Brief pause between tasks
            time.sleep(1)
        
        if self.iteration_count >= self.max_iterations:
            self.log("⚠️  Max iterations reached. Stopping.", "WARNING")
        
        self.log("🏁 Autonomous mode ended")
        self.log(f"Total iterations: {self.iteration_count}")


class WatchMode:
    """Watch for file changes and trigger autonomous actions"""
    
    def __init__(self, agent: OptiplexAgent, watch_patterns: List[str] = None):
        self.agent = agent
        self.autonomous = AutonomousMode(agent)
        self.watch_patterns = watch_patterns or ["*.py", "*.md", "*.json"]
        self.last_check = {}
    
    def check_for_changes(self) -> List[Path]:
        """Check for file modifications"""
        changed_files = []
        
        for pattern in self.watch_patterns:
            for file_path in Path(self.agent.root_dir).rglob(pattern):
                if file_path.is_file():
                    mtime = file_path.stat().st_mtime
                    
                    if str(file_path) in self.last_check:
                        if mtime > self.last_check[str(file_path)]:
                            changed_files.append(file_path)
                    
                    self.last_check[str(file_path)] = mtime
        
        return changed_files
    
    def handle_change(self, file_path: Path):
        """Handle file change event"""
        self.autonomous.log(f"🔔 Change detected: {file_path}")
        
        # Create task to analyze change
        task = {
            "id": f"change_{int(time.time())}",
            "description": f"Analyze changes in {file_path} and take appropriate action (fix issues, update tests, etc.)",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "trigger": "file_change",
            "file": str(file_path)
        }
        
        tasks = self.autonomous.load_tasks()
        tasks.append(task)
        self.autonomous.save_tasks(tasks)
    
    def run(self, check_interval: int = 5):
        """Run in watch mode"""
        self.autonomous.log("👁️  Starting watch mode")
        self.autonomous.log(f"Watching patterns: {self.watch_patterns}")
        self.autonomous.log(f"Check interval: {check_interval}s")
        
        # Initial scan
        self.check_for_changes()
        
        try:
            while True:
                changed_files = self.check_for_changes()
                
                for file_path in changed_files:
                    self.handle_change(file_path)
                
                # Process any pending tasks
                tasks = self.autonomous.load_tasks()
                pending = [t for t in tasks if t.get("status") == "pending"]
                
                if pending:
                    self.autonomous.run(auto_reflect=False)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.autonomous.log("⏹️  Watch mode stopped by user")

