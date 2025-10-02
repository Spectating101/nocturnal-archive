#!/usr/bin/env python3
"""
Simple installation script for Nocturnal Archive
No interactive prompts - just install and go!
"""

import sys
import subprocess
import os
from pathlib import Path

def create_venv():
    """Create virtual environment if needed"""
    venv_path = Path("nocturnal-venv")
    if not venv_path.exists():
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                          check=True, capture_output=True)
            return venv_path
        except subprocess.CalledProcessError:
            return None
    else:
        return venv_path

def install_package():
    """Install the package with custom progress indicator"""
    import time
    import threading
    
    # Create virtual environment in user space
    venv_path = Path.home() / ".local" / "nocturnal-archive"
    venv_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create virtual environment (silent)
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                      check=True, capture_output=True)
        
        # Show custom progress indicator
        print("Installing dependencies...")
        progress_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        progress_running = True
        
        def show_progress():
            i = 0
            while progress_running:
                print(f"\r{progress_chars[i % len(progress_chars)]} Installing...", end="", flush=True)
                time.sleep(0.1)
                i += 1
        
        # Start progress indicator
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()
        
        # Install silently
        venv_python = venv_path / "bin" / "python"
        subprocess.run([str(venv_python), "-m", "pip", "install", "-qq", "-e", "."], 
                      check=True, capture_output=True)
        
        # Stop progress indicator
        progress_running = False
        print(f"\r✅ Installation complete!")
        
        # Create symlink for global access
        user_bin = Path.home() / ".local" / "bin"
        user_bin.mkdir(exist_ok=True)
        symlink_path = user_bin / "nocturnal"
        
        if symlink_path.exists():
            symlink_path.unlink()
        symlink_path.symlink_to(venv_path / "bin" / "nocturnal")
        
        return True, str(venv_python)
        
    except subprocess.CalledProcessError:
        progress_running = False
        return False, None

def test_installation(python_executable):
    """Test the installation"""
    try:
        # Test import silently
        subprocess.run([
            python_executable, "-c", 
            "from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest"
        ], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def launch_chatbot():
    """Launch the chatbot directly"""
    print("\n🌙 Nocturnal Archive is ready!")
    print("Launching chatbot...\n")
    
    # Launch the chatbot directly
    try:
        subprocess.run(["nocturnal"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to launch chatbot. Try running: nocturnal")
        return False
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return True
    
    return True

def main():
    """Main installation and launch"""
    print("Installing Nocturnal Archive...")
    
    success, python_executable = install_package()
    if not success:
        print("Installation failed")
        return False
    
    if not test_installation(python_executable):
        print("Installation verification failed")
        return False
    
    # Launch chatbot directly
    return launch_chatbot()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
