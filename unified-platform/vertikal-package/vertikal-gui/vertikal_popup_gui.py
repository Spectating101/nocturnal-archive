#!/usr/bin/env python3
"""
Vertikal Popup GUI - Simple popup window with progress indicators
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

# Try to import tkinter, fallback to simple terminal if not available
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

class VertikalPopupGUI:
    def __init__(self):
        self.project_root = Path.cwd()
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.process = None
        self.running = False
        
        if TKINTER_AVAILABLE:
            self.root = tk.Tk()
            self.root.title("Vertikal Assistant")
            self.root.geometry("500x400")
            self.root.configure(bg='#f0f0f0')
        else:
            self.root = None
    
    def show_setup_dialog(self):
        """Show setup dialog"""
        if TKINTER_AVAILABLE:
            return self.show_tkinter_setup()
        else:
            return self.show_terminal_setup()
    
    def show_tkinter_setup(self):
        """Show Tkinter setup dialog"""
        # Create setup window
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Vertikal Setup")
        setup_window.geometry("400x300")
        setup_window.configure(bg='#f0f0f0')
        setup_window.grab_set()  # Modal dialog
        
        # Center the window
        setup_window.transient(self.root)
        setup_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Header
        header_frame = tk.Frame(setup_window, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🤖 Vertikal Setup", 
                              font=('Arial', 14, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(setup_window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # API Key section
        api_frame = tk.Frame(main_frame, bg='#f0f0f0')
        api_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(api_frame, text="Groq API Key:", font=('Arial', 10, 'bold'),
                bg='#f0f0f0').pack(anchor='w')
        
        self.api_key_var = tk.StringVar(value=self.api_key)
        api_entry = tk.Entry(api_frame, textvariable=self.api_key_var,
                            font=('Arial', 10), width=40, show='*')
        api_entry.pack(fill='x', pady=(5, 0))
        
        get_key_btn = tk.Button(api_frame, text="Get Free Key",
                               command=self.open_groq_website,
                               bg='#3498db', fg='white', font=('Arial', 9))
        get_key_btn.pack(anchor='w', pady=(5, 0))
        
        # Project directory section
        project_frame = tk.Frame(main_frame, bg='#f0f0f0')
        project_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(project_frame, text="Project Directory:", font=('Arial', 10, 'bold'),
                bg='#f0f0f0').pack(anchor='w')
        
        self.project_var = tk.StringVar(value=str(self.project_root))
        project_entry = tk.Entry(project_frame, textvariable=self.project_var,
                                font=('Arial', 10), width=40)
        project_entry.pack(fill='x', pady=(5, 0))
        
        # Status section
        status_frame = tk.Frame(main_frame, bg='#f0f0f0')
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.status_text = tk.Text(status_frame, height=4, font=('Arial', 9),
                                  bg='#ecf0f1', fg='#2c3e50', wrap='word')
        self.status_text.pack(fill='x')
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        test_btn = tk.Button(button_frame, text="Test Setup",
                            command=self.test_setup,
                            bg='#f39c12', fg='white', font=('Arial', 10))
        test_btn.pack(side='left', padx=(0, 10))
        
        ok_btn = tk.Button(button_frame, text="Start Assistant",
                          command=lambda: self.finish_setup(setup_window),
                          bg='#27ae60', fg='white', font=('Arial', 10, 'bold'))
        ok_btn.pack(side='right')
        
        # Initial status check
        self.check_status()
        
        # Wait for dialog to close
        setup_window.wait_window()
        
        return self.api_key and self.project_root.exists()
    
    def show_terminal_setup(self):
        """Show terminal-based setup"""
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
        
        return True
    
    def check_status(self):
        """Check setup status"""
        if not TKINTER_AVAILABLE:
            return
        
        status = []
        
        # Check API key
        if self.api_key_var.get().strip():
            status.append("✅ Groq API Key: Set")
        else:
            status.append("❌ Groq API Key: Not set")
        
        # Check project directory
        if Path(self.project_var.get()).exists():
            status.append("✅ Project Directory: Valid")
        else:
            status.append("❌ Project Directory: Invalid")
        
        # Check vertikal installation
        try:
            result = subprocess.run(['vertikal', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status.append("✅ Vertikal: Installed")
            else:
                status.append("❌ Vertikal: Not installed")
        except:
            status.append("❌ Vertikal: Not installed")
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, '\n'.join(status))
    
    def test_setup(self):
        """Test the current setup"""
        if not TKINTER_AVAILABLE:
            return
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, "🧪 Testing setup...\n")
        
        # Update values
        self.api_key = self.api_key_var.get().strip()
        self.project_root = Path(self.project_var.get())
        
        # Test API key
        if not self.api_key:
            self.status_text.insert(tk.END, "❌ API key is empty\n")
            return
        
        # Test project directory
        if not self.project_root.exists():
            self.status_text.insert(tk.END, "❌ Project directory doesn't exist\n")
            return
        
        # Test vertikal installation
        try:
            result = subprocess.run(['vertikal', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.status_text.insert(tk.END, "✅ Vertikal is installed\n")
            else:
                self.status_text.insert(tk.END, "❌ Vertikal is not working\n")
                return
        except Exception as e:
            self.status_text.insert(tk.END, f"❌ Vertikal test failed: {e}\n")
            return
        
        self.status_text.insert(tk.END, "✅ All tests passed! Ready to start.\n")
    
    def finish_setup(self, setup_window):
        """Finish setup and start assistant"""
        self.api_key = self.api_key_var.get().strip()
        self.project_root = Path(self.project_var.get())
        
        if not self.api_key:
            messagebox.showerror("Error", "Please enter your Groq API key")
            return
        
        if not self.project_root.exists():
            messagebox.showerror("Error", "Project directory doesn't exist")
            return
        
        # Set environment variable
        os.environ['GROQ_API_KEY'] = self.api_key
        
        setup_window.destroy()
        self.show_progress_window()
    
    def open_groq_website(self):
        """Open Groq website in browser"""
        import webbrowser
        webbrowser.open('https://console.groq.com/')
        messagebox.showinfo("Get API Key", 
                           "1. Sign up for free account\n"
                           "2. Create API key\n"
                           "3. Copy and paste it above")
    
    def show_progress_window(self):
        """Show progress window"""
        if TKINTER_AVAILABLE:
            self.show_tkinter_progress()
        else:
            self.show_terminal_progress()
    
    def show_tkinter_progress(self):
        """Show Tkinter progress window"""
        # Hide main window
        self.root.withdraw()
        
        # Create progress window
        progress_window = tk.Toplevel()
        progress_window.title("Vertikal Assistant")
        progress_window.geometry("600x500")
        progress_window.configure(bg='#f0f0f0')
        
        # Header
        header_frame = tk.Frame(progress_window, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🤖 Vertikal Assistant", 
                              font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(progress_window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Status section
        status_frame = tk.LabelFrame(main_frame, text="Status", font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', fg='#2c3e50')
        status_frame.pack(fill='x', pady=(0, 20))
        
        self.status_text = tk.Text(status_frame, height=3, font=('Arial', 9),
                                  bg='#ecf0f1', fg='#2c3e50', wrap='word')
        self.status_text.pack(fill='x', padx=10, pady=10)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 20))
        
        self.start_btn = tk.Button(button_frame, text="🚀 Start Assistant",
                                  command=self.start_assistant,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  height=2)
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Assistant",
                                 command=self.stop_assistant,
                                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                 height=2, state='disabled')
        self.stop_btn.pack(side='left')
        
        # Output section
        output_frame = tk.LabelFrame(main_frame, text="Assistant Output", 
                                    font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', fg='#2c3e50')
        output_frame.pack(fill='both', expand=True)
        
        self.output_text = tk.Text(output_frame, font=('Consolas', 10),
                                  bg='#2c3e50', fg='#ecf0f1',
                                  wrap='word')
        self.output_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input section
        input_frame = tk.Frame(output_frame, bg='#f0f0f0')
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_var,
                                   font=('Arial', 10), width=50)
        self.input_entry.pack(side='left', fill='x', expand=True)
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(input_frame, text="Send",
                                 command=self.send_message,
                                 bg='#3498db', fg='white', font=('Arial', 9))
        self.send_btn.pack(side='right', padx=(10, 0))
        
        # Initial status
        self.update_status("Ready to start")
        
        # Start main loop
        progress_window.mainloop()
    
    def show_terminal_progress(self):
        """Show terminal progress"""
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
            self.show_terminal_chat()
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
            
            if TKINTER_AVAILABLE:
                self.update_status("Assistant started")
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
            
        except Exception as e:
            error_msg = f"Error starting assistant: {e}"
            if TKINTER_AVAILABLE:
                self.update_status(error_msg)
            else:
                print(f"❌ {error_msg}")
            self.running = False
    
    def read_output(self):
        """Read output from assistant process"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line and self.running:
                    if TKINTER_AVAILABLE:
                        self.root.after(0, self.append_output, line.rstrip())
                    else:
                        print(line.rstrip())
        except Exception as e:
            if self.running:
                error_msg = f"Error reading output: {e}"
                if TKINTER_AVAILABLE:
                    self.root.after(0, self.append_output, error_msg)
                else:
                    print(f"❌ {error_msg}")
    
    def send_message(self, event=None):
        """Send message to assistant"""
        if not TKINTER_AVAILABLE:
            return
        
        message = self.input_var.get().strip()
        if not message or not self.process:
            return
        
        self.input_var.set("")
        self.append_output(f"👤 You: {message}")
        
        try:
            self.process.stdin.write(message + '\n')
            self.process.stdin.flush()
        except Exception as e:
            self.append_output(f"❌ Error sending message: {e}")
    
    def show_terminal_chat(self):
        """Show terminal chat interface"""
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
    
    def update_status(self, message):
        """Update status text"""
        if not TKINTER_AVAILABLE:
            return
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, message)
    
    def append_output(self, text):
        """Append text to output (thread-safe)"""
        if not TKINTER_AVAILABLE:
            return
        
        self.output_text.insert(tk.END, text + '\n')
        self.output_text.see(tk.END)
    
    def stop_assistant(self):
        """Stop the assistant"""
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.running = False
        
        if TKINTER_AVAILABLE:
            self.update_status("Assistant stopped")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.append_output("⏹️ Assistant stopped")
        else:
            print("👋 Assistant stopped. Goodbye!")

def main():
    """Main entry point"""
    gui = VertikalPopupGUI()
    
    # Show setup dialog
    if not gui.show_setup_dialog():
        print("❌ Setup failed. Exiting.")
        return
    
    # Show progress window
    gui.show_progress_window()

if __name__ == "__main__":
    main()
