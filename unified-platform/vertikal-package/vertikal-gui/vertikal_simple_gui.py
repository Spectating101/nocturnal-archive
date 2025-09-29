#!/usr/bin/env python3
"""
Vertikal Simple GUI - Minimal terminal popup with progress indicators
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

class VertikalSimpleGUI:
    def __init__(self):
        self.project_root = Path.cwd()
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.process = None
        self.running = False
        
    def show_setup_dialog(self):
        """Show simple setup dialog"""
        print("🤖 Vertikal Assistant Setup")
        print("=" * 40)
        
        # Check API key
        if not self.api_key:
            print("❌ Groq API Key not set")
            print("💡 Get free key at: https://console.groq.com/")
            api_key = input("Enter your API key: ").strip()
            if api_key:
                os.environ['GROQ_API_KEY'] = api_key
                self.api_key = api_key
                print("✅ API key set")
            else:
                print("❌ No API key provided")
                return False
        else:
            print("✅ API key already set")
        
        # Check project directory
        print(f"📁 Project directory: {self.project_root}")
        change_dir = input("Change directory? (y/n): ").strip().lower()
        if change_dir == 'y':
            new_dir = input("Enter new directory: ").strip()
            if new_dir and Path(new_dir).exists():
                self.project_root = Path(new_dir)
                print(f"✅ Changed to: {self.project_root}")
            else:
                print("❌ Invalid directory")
                return False
        
        # Test vertikal installation
        print("🧪 Testing Vertikal installation...")
        try:
            result = subprocess.run(['vertikal', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Vertikal is installed and working")
            else:
                print("❌ Vertikal not working properly")
                return False
        except Exception as e:
            print(f"❌ Vertikal test failed: {e}")
            return False
        
        print("✅ Setup complete!")
        return True
    
    def show_progress_window(self):
        """Show simple progress window"""
        print("\n🚀 Starting Vertikal Assistant...")
        print("=" * 40)
        print("📁 Project:", self.project_root)
        print("🔑 API Key:", "✅ Set" if self.api_key else "❌ Not set")
        print("⏳ Status: Starting...")
        
        # Start assistant
        self.start_assistant()
        
        if self.running:
            print("✅ Assistant started successfully!")
            print("💡 Type your questions below (or 'quit' to exit)")
            print("-" * 40)
            self.show_chat_interface()
        else:
            print("❌ Failed to start assistant")
    
    def start_assistant(self):
        """Start the vertikal assistant"""
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Start vertikal process
            self.process = subprocess.Popen(
                ['vertikal', '--project-root', '.'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start output reader thread
            self.output_thread = threading.Thread(target=self.read_output)
            self.output_thread.daemon = True
            self.output_thread.start()
            
            self.running = True
            
        except Exception as e:
            print(f"❌ Error starting assistant: {e}")
            self.running = False
    
    def read_output(self):
        """Read output from assistant process"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line and self.running:
                    # Print assistant output
                    print(line.rstrip())
        except Exception as e:
            if self.running:
                print(f"❌ Error reading output: {e}")
    
    def show_chat_interface(self):
        """Show simple chat interface"""
        while self.running:
            try:
                # Get user input
                user_input = input("vertikal:project> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.stop_assistant()
                    break
                
                # Send message to assistant
                if self.process:
                    self.process.stdin.write(user_input + '\n')
                    self.process.stdin.flush()
                
            except KeyboardInterrupt:
                print("\n⏹️ Stopping assistant...")
                self.stop_assistant()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def stop_assistant(self):
        """Stop the assistant"""
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.running = False
        print("👋 Assistant stopped. Goodbye!")

def main():
    """Main entry point"""
    print("🤖 Vertikal Simple GUI")
    print("=" * 30)
    
    gui = VertikalSimpleGUI()
    
    # Show setup dialog
    if not gui.show_setup_dialog():
        print("❌ Setup failed. Exiting.")
        return
    
    # Show progress window and start chat
    gui.show_progress_window()

if __name__ == "__main__":
    main()
