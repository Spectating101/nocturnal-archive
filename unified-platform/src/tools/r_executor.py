#!/usr/bin/env python3
"""
R Code Executor - Mimics Claude's ability to execute R code and see results
Provides real-time R code execution with output capture and error handling
"""

import os
import subprocess
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class RExecutor:
    """Execute R code and capture results - mimicking Claude's R execution capabilities"""
    
    def __init__(self, r_path: str = "R", timeout: int = 30):
        self.r_path = r_path
        self.timeout = timeout
        self.session_active = False
        self.session_file = None
        self.workspace_dir = None
        
    def check_r_availability(self) -> Dict[str, Any]:
        """Check if R is available and get version info"""
        try:
            result = subprocess.run(
                [self.r_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                return {
                    "success": True,
                    "available": True,
                    "version": version_info,
                    "path": self.r_path
                }
            else:
                return {
                    "success": False,
                    "available": False,
                    "error": "R command failed",
                    "stderr": result.stderr
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "available": False,
                "error": f"R not found at {self.r_path}"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "available": False,
                "error": "R version check timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "available": False,
                "error": f"Error checking R: {str(e)}"
            }
    
    def start_session(self, workspace_dir: str = None) -> Dict[str, Any]:
        """Start an R session with persistent workspace"""
        try:
            # Create temporary workspace if not provided
            if workspace_dir:
                self.workspace_dir = Path(workspace_dir)
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
            else:
                self.workspace_dir = Path(tempfile.mkdtemp(prefix="r_session_"))
            
            # Create R session file
            self.session_file = self.workspace_dir / "session.R"
            
            # Initialize session
            init_code = """
# Session initialization
cat("R Session Started\\n")
cat("Working directory:", getwd(), "\\n")
cat("R Version:", R.version.string, "\\n")
cat("Available packages:", length(installed.packages()[,1]), "\\n")
cat("\\n")
"""
            
            with open(self.session_file, 'w') as f:
                f.write(init_code)
            
            self.session_active = True
            
            return {
                "success": True,
                "session_id": str(self.workspace_dir),
                "workspace_dir": str(self.workspace_dir),
                "session_file": str(self.session_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error starting R session: {str(e)}"
            }
    
    def execute_r_code(self, code: str, capture_plots: bool = True) -> Dict[str, Any]:
        """
        Execute R code and capture results - mimics Claude's R execution
        """
        try:
            if not self.session_active:
                # Start session if not active
                session_result = self.start_session()
                if not session_result["success"]:
                    return session_result
            
            # Prepare R script
            r_script = self._prepare_r_script(code, capture_plots)
            
            # Execute R script
            result = subprocess.run(
                [self.r_path, "--slave", "--no-restore", "--no-save"],
                input=r_script,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.workspace_dir
            )
            
            # Parse results
            output = self._parse_r_output(result.stdout, result.stderr)
            
            return {
                "success": True,
                "code": code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "output": output,
                "plots": self._get_plots() if capture_plots else [],
                "variables": self._get_session_variables(),
                "execution_time": time.time()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"R code execution timed out after {self.timeout} seconds",
                "code": code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing R code: {str(e)}",
                "code": code
            }
    
    def execute_r_file(self, file_path: str) -> Dict[str, Any]:
        """Execute an R file"""
        try:
            full_path = Path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"R file not found: {file_path}"
                }
            
            # Read R file
            with open(full_path, 'r') as f:
                code = f.read()
            
            return self.execute_r_code(code)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing R file: {str(e)}",
                "file_path": file_path
            }
    
    def install_package(self, package_name: str) -> Dict[str, Any]:
        """Install an R package"""
        install_code = f"""
# Install package: {package_name}
install.packages("{package_name}", repos="https://cran.r-project.org/")
cat("Package {package_name} installation completed\\n")
"""
        
        result = self.execute_r_code(install_code)
        
        if result["success"]:
            result["package"] = package_name
            result["action"] = "install"
        
        return result
    
    def load_package(self, package_name: str) -> Dict[str, Any]:
        """Load an R package"""
        load_code = f"""
# Load package: {package_name}
library({package_name})
cat("Package {package_name} loaded successfully\\n")
"""
        
        result = self.execute_r_code(load_code)
        
        if result["success"]:
            result["package"] = package_name
            result["action"] = "load"
        
        return result
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        info_code = """
# Session information
cat("=== R Session Info ===\\n")
cat("R Version:", R.version.string, "\\n")
cat("Platform:", R.version$platform, "\\n")
cat("Working Directory:", getwd(), "\\n")
cat("Loaded Packages:", paste(.packages(), collapse=", "), "\\n")
cat("Environment Objects:", length(ls()), "\\n")
cat("Memory Usage:", format(memory.size(), big.mark=","), "MB\\n")
cat("\\n")
"""
        
        return self.execute_r_code(info_code)
    
    def _prepare_r_script(self, code: str, capture_plots: bool = True) -> str:
        """Prepare R script with proper setup"""
        script_parts = []
        
        # Set up plot capture if requested
        if capture_plots:
            script_parts.append("""
# Set up plot capture
plot_dir <- "plots"
if (!dir.exists(plot_dir)) dir.create(plot_dir)
plot_counter <- 0
""")
        
        # Add the user code
        script_parts.append(code)
        
        # Add plot saving if capturing plots
        if capture_plots:
            script_parts.append("""
# Save any plots
if (dev.cur() != 1) {
  plot_counter <- plot_counter + 1
  plot_file <- file.path(plot_dir, paste0("plot_", plot_counter, ".png"))
  dev.copy(png, plot_file, width=800, height=600)
  dev.off()
  cat("Plot saved:", plot_file, "\\n")
}
""")
        
        return "\n".join(script_parts)
    
    def _parse_r_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse R output into structured format"""
        output = {
            "text": stdout,
            "errors": stderr,
            "warnings": [],
            "messages": []
        }
        
        # Extract warnings and messages
        lines = stdout.split('\n')
        for line in lines:
            if 'Warning:' in line:
                output["warnings"].append(line.strip())
            elif 'Message:' in line:
                output["messages"].append(line.strip())
        
        return output
    
    def _get_plots(self) -> List[Dict[str, Any]]:
        """Get information about generated plots"""
        plots = []
        
        if self.workspace_dir:
            plots_dir = self.workspace_dir / "plots"
            if plots_dir.exists():
                for plot_file in plots_dir.glob("*.png"):
                    plots.append({
                        "filename": plot_file.name,
                        "path": str(plot_file),
                        "size": plot_file.stat().st_size
                    })
        
        return plots
    
    def _get_session_variables(self) -> Dict[str, Any]:
        """Get current session variables"""
        try:
            # Get variable names
            result = self.execute_r_code("ls()")
            if result["success"]:
                variables = result["stdout"].strip().split('\n')
                return {
                    "variables": [v.strip() for v in variables if v.strip()],
                    "count": len([v for v in variables if v.strip()])
                }
        except:
            pass
        
        return {"variables": [], "count": 0}
    
    def end_session(self) -> Dict[str, Any]:
        """End the R session and cleanup"""
        try:
            self.session_active = False
            
            # Cleanup temporary workspace if created
            if self.workspace_dir and "r_session_" in str(self.workspace_dir):
                import shutil
                shutil.rmtree(self.workspace_dir, ignore_errors=True)
            
            return {
                "success": True,
                "message": "R session ended successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ending session: {str(e)}"
            }