#!/usr/bin/env python3
"""
Vertikal GUI - User-friendly wrapper for the terminal assistant
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import os
import sys
import threading
from pathlib import Path
import json

class VertikalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vertikal - File-Aware Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # State
        self.project_root = Path.cwd()
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.process = None
        
        self.setup_ui()
        self.check_setup()
    
    def setup_ui(self):
        """Create the user interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🤖 Vertikal Assistant", 
                              font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Setup section
        setup_frame = tk.LabelFrame(main_frame, text="Setup", font=('Arial', 12, 'bold'),
                                   bg='#f0f0f0', fg='#2c3e50')
        setup_frame.pack(fill='x', pady=(0, 20))
        
        # API Key section
        api_frame = tk.Frame(setup_frame, bg='#f0f0f0')
        api_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(api_frame, text="Groq API Key:", font=('Arial', 10, 'bold'),
                bg='#f0f0f0').pack(anchor='w')
        
        api_input_frame = tk.Frame(api_frame, bg='#f0f0f0')
        api_input_frame.pack(fill='x', pady=(5, 0))
        
        self.api_key_var = tk.StringVar(value=self.api_key)
        self.api_entry = tk.Entry(api_input_frame, textvariable=self.api_key_var,
                                 font=('Arial', 10), width=50, show='*')
        self.api_entry.pack(side='left', fill='x', expand=True)
        
        self.get_key_btn = tk.Button(api_input_frame, text="Get Free Key",
                                    command=self.open_groq_website,
                                    bg='#3498db', fg='white', font=('Arial', 9))
        self.get_key_btn.pack(side='right', padx=(10, 0))
        
        # Project directory section
        project_frame = tk.Frame(setup_frame, bg='#f0f0f0')
        project_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(project_frame, text="Project Directory:", font=('Arial', 10, 'bold'),
                bg='#f0f0f0').pack(anchor='w')
        
        project_input_frame = tk.Frame(project_frame, bg='#f0f0f0')
        project_input_frame.pack(fill='x', pady=(5, 0))
        
        self.project_var = tk.StringVar(value=str(self.project_root))
        self.project_entry = tk.Entry(project_input_frame, textvariable=self.project_var,
                                     font=('Arial', 10), width=50)
        self.project_entry.pack(side='left', fill='x', expand=True)
        
        self.browse_btn = tk.Button(project_input_frame, text="Browse",
                                   command=self.browse_project,
                                   bg='#95a5a6', fg='white', font=('Arial', 9))
        self.browse_btn.pack(side='right', padx=(10, 0))
        
        # Status section
        status_frame = tk.LabelFrame(main_frame, text="Status", font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', fg='#2c3e50')
        status_frame.pack(fill='x', pady=(0, 20))
        
        self.status_text = tk.Text(status_frame, height=4, font=('Arial', 9),
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
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        self.test_btn = tk.Button(button_frame, text="🧪 Test Setup",
                                 command=self.test_setup,
                                 bg='#f39c12', fg='white', font=('Arial', 12, 'bold'),
                                 height=2)
        self.test_btn.pack(side='right')
        
        # Output section
        output_frame = tk.LabelFrame(main_frame, text="Assistant Output", 
                                    font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', fg='#2c3e50')
        output_frame.pack(fill='both', expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, font=('Consolas', 10),
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
    
    def check_setup(self):
        """Check current setup status"""
        status = []
        
        # Check API key
        if self.api_key:
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
    
    def open_groq_website(self):
        """Open Groq website in browser"""
        import webbrowser
        webbrowser.open('https://console.groq.com/')
        messagebox.showinfo("Get API Key", 
                           "1. Sign up for free account\n"
                           "2. Create API key\n"
                           "3. Copy and paste it above")
    
    def browse_project(self):
        """Browse for project directory"""
        directory = filedialog.askdirectory(
            title="Select Project Directory",
            initialdir=str(self.project_root)
        )
        if directory:
            self.project_var.set(directory)
            self.project_root = Path(directory)
            self.check_setup()
    
    def test_setup(self):
        """Test the current setup"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, "🧪 Testing setup...\n")
        
        # Test API key
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.status_text.insert(tk.END, "❌ API key is empty\n")
            return
        
        # Test project directory
        project_dir = Path(self.project_var.get())
        if not project_dir.exists():
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
    
    def start_assistant(self):
        """Start the vertikal assistant"""
        # Validate setup
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Groq API key")
            return
        
        project_dir = Path(self.project_var.get())
        if not project_dir.exists():
            messagebox.showerror("Error", "Project directory doesn't exist")
            return
        
        # Set environment variable
        os.environ['GROQ_API_KEY'] = api_key
        
        # Start assistant in thread
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "🚀 Starting Vertikal Assistant...\n")
        self.output_text.insert(tk.END, f"📁 Project: {project_dir}\n")
        self.output_text.insert(tk.END, "💡 Type your questions below!\n\n")
        
        # Start the assistant process
        self.assistant_thread = threading.Thread(target=self.run_assistant)
        self.assistant_thread.daemon = True
        self.assistant_thread.start()
    
    def run_assistant(self):
        """Run the vertikal assistant"""
        try:
            # Change to project directory
            os.chdir(self.project_var.get())
            
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
            
            # Read output
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.root.after(0, self.append_output, line)
            
        except Exception as e:
            self.root.after(0, self.append_output, f"❌ Error: {e}\n")
        finally:
            self.root.after(0, self.assistant_stopped)
    
    def append_output(self, text):
        """Append text to output (thread-safe)"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
    
    def send_message(self, event=None):
        """Send message to assistant"""
        message = self.input_var.get().strip()
        if not message or not self.process:
            return
        
        self.input_var.set("")
        self.append_output(f"👤 You: {message}\n")
        
        try:
            self.process.stdin.write(message + '\n')
            self.process.stdin.flush()
        except Exception as e:
            self.append_output(f"❌ Error sending message: {e}\n")
    
    def stop_assistant(self):
        """Stop the assistant"""
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.assistant_stopped()
    
    def assistant_stopped(self):
        """Called when assistant stops"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.append_output("\n⏹️ Assistant stopped.\n")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = VertikalGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
