"""Bridge between Optiplex and Molina Scheduler"""
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class SchedulerBridge:
    """Interface with Molina Rust scheduler"""
    
    def __init__(self, scheduler_path: Optional[Path] = None):
        if scheduler_path is None:
            # Try to find Molina-Optiplex directory
            possible_paths = [
                Path.home() / "Downloads/llm_automation/project_portfolio/Molina-Optiplex",
                Path.cwd().parent.parent / "Molina-Optiplex",
                Path("/home/phyrexian/Downloads/llm_automation/project_portfolio/Molina-Optiplex")
            ]
            
            for path in possible_paths:
                if path.exists():
                    scheduler_path = path
                    break
        
        self.scheduler_path = scheduler_path
        self.config_file = scheduler_path / "scheduler_config.json" if scheduler_path else None
    
    def is_safe_to_run(self) -> bool:
        """Check if it's safe to run autonomous tasks (user is idle)"""
        if not self.scheduler_path or not self.config_file:
            # No scheduler, assume it's safe
            return True
        
        try:
            # Read scheduler config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            patterns = config.get("schedule_patterns", {})
            
            if not patterns:
                # No learned patterns yet, be conservative
                return False
            
            # Get the first pattern (or specific machine)
            pattern = list(patterns.values())[0]
            
            now = datetime.now()
            current_hour = now.hour
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            # Check if we're in typical work hours
            start_hour = pattern.get("typical_start_hour", 9)
            end_hour = pattern.get("typical_end_hour", 17)
            workdays = pattern.get("workdays", [1, 2, 3, 4, 5])  # Mon-Fri
            
            # Convert Sunday=0 in config to Python's Monday=0
            # Rust uses 0=Sunday, Python uses 0=Monday
            rust_weekday = (current_weekday + 1) % 7
            
            is_workday = rust_weekday in workdays
            is_work_hours = start_hour <= current_hour < end_hour
            
            # Safe to run if:
            # 1. Outside work hours, OR
            # 2. Not a workday
            is_safe = not (is_workday and is_work_hours)
            
            return is_safe
            
        except Exception as e:
            print(f"Failed to check scheduler: {e}")
            # If we can't check, be conservative
            return False
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current system resource status from scheduler"""
        if not self.scheduler_path:
            return {"available": True}
        
        try:
            # Check if scheduler is running
            result = subprocess.run(
                ["pgrep", "-f", "optiplex-scheduler"],
                capture_output=True,
                text=True
            )
            
            scheduler_running = result.returncode == 0
            
            return {
                "scheduler_running": scheduler_running,
                "safe_to_run": self.is_safe_to_run(),
                "config_path": str(self.config_file) if self.config_file else None
            }
            
        except Exception as e:
            return {"error": str(e), "available": True}
    
    def wait_for_safe_window(self, check_interval: int = 300) -> bool:
        """Wait until it's safe to run autonomous tasks
        
        Args:
            check_interval: Seconds between checks (default 5 minutes)
        
        Returns:
            True when it's safe, False if interrupted
        """
        import time
        
        print("⏳ Waiting for safe execution window...")
        print(f"   Checking every {check_interval}s")
        
        while True:
            if self.is_safe_to_run():
                print("✅ Safe to proceed - user is idle")
                return True
            
            status = self.get_resource_status()
            print(f"⏸️  User is active. Waiting... (Status: {status})")
            
            try:
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("\n⏹️  Interrupted by user")
                return False


def check_before_autonomous(scheduler_path: Optional[Path] = None) -> bool:
    """Quick check before starting autonomous mode"""
    bridge = SchedulerBridge(scheduler_path)
    
    if bridge.is_safe_to_run():
        print("✅ Scheduler check: Safe to run")
        return True
    else:
        print("⚠️  User is active. Autonomous mode should wait.")
        print("   Run with --force to override")
        return False


