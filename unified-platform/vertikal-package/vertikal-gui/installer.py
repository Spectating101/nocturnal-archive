#!/usr/bin/env python3
"""
Vertikal Installer - Creates desktop shortcuts and sets up the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import json

class VertikalInstaller:
    def __init__(self):
        self.system = platform.system()
        self.home_dir = Path.home()
        self.app_name = "Vertikal Assistant"
        
    def create_desktop_shortcut(self):
        """Create desktop shortcut based on OS"""
        if self.system == "Windows":
            return self.create_windows_shortcut()
        elif self.system == "Darwin":  # macOS
            return self.create_macos_shortcut()
        else:  # Linux
            return self.create_linux_shortcut()
    
    def create_windows_shortcut(self):
        """Create Windows desktop shortcut"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, f"{self.app_name}.lnk")
            target = sys.executable
            wDir = str(Path(__file__).parent)
            icon = target
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{Path(__file__).parent / "vertikal_gui.py"}"'
            shortcut.WorkingDirectory = wDir
            shortcut.IconLocation = icon
            shortcut.save()
            
            return True
        except ImportError:
            # Fallback: create batch file
            desktop = Path.home() / "Desktop"
            batch_file = desktop / f"{self.app_name}.bat"
            
            with open(batch_file, 'w') as f:
                f.write(f'@echo off\n')
                f.write(f'cd /d "{Path(__file__).parent}"\n')
                f.write(f'python "{Path(__file__).parent / "vertikal_gui.py"}"\n')
                f.write(f'pause\n')
            
            return True
        except Exception as e:
            print(f"Error creating Windows shortcut: {e}")
            return False
    
    def create_macos_shortcut(self):
        """Create macOS application bundle"""
        try:
            app_dir = Path.home() / "Applications" / f"{self.app_name}.app"
            app_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Contents directory
            contents_dir = app_dir / "Contents"
            contents_dir.mkdir(exist_ok=True)
            
            # Create Info.plist
            info_plist = contents_dir / "Info.plist"
            with open(info_plist, 'w') as f:
                f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>vertikal_gui.py</string>
    <key>CFBundleIdentifier</key>
    <string>com.vertikal.assistant</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
</dict>
</plist>''')
            
            # Create MacOS directory and executable
            macos_dir = contents_dir / "MacOS"
            macos_dir.mkdir(exist_ok=True)
            
            executable = macos_dir / "vertikal_gui.py"
            with open(executable, 'w') as f:
                f.write(f'#!/usr/bin/env python3\n')
                f.write(f'import sys\n')
                f.write(f'import os\n')
                f.write(f'sys.path.insert(0, "{Path(__file__).parent.parent.parent}")\n')
                f.write(f'exec(open("{Path(__file__).parent.parent.parent / "vertikal_gui.py"}").read())\n')
            
            os.chmod(executable, 0o755)
            
            return True
        except Exception as e:
            print(f"Error creating macOS shortcut: {e}")
            return False
    
    def create_linux_shortcut(self):
        """Create Linux desktop entry"""
        try:
            desktop_dir = Path.home() / "Desktop"
            desktop_dir.mkdir(exist_ok=True)
            
            desktop_file = desktop_dir / f"{self.app_name}.desktop"
            
            with open(desktop_file, 'w') as f:
                f.write(f'''[Desktop Entry]
Version=1.0
Type=Application
Name={self.app_name}
Comment=File-aware ChatGPT assistant
Exec=python3 "{Path(__file__).parent / "vertikal_gui.py"}"
Icon=applications-development
Terminal=false
Categories=Development;Education;
Path={Path(__file__).parent}
''')
            
            os.chmod(desktop_file, 0o755)
            
            return True
        except Exception as e:
            print(f"Error creating Linux shortcut: {e}")
            return False
    
    def install_vertikal(self):
        """Install vertikal package"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'vertikal'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "Vertikal installed successfully"
            else:
                return False, f"Installation failed: {result.stderr}"
        except Exception as e:
            return False, f"Installation error: {e}"
    
    def create_start_menu_entry(self):
        """Create start menu entry (Windows)"""
        if self.system != "Windows":
            return True
        
        try:
            start_menu = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            start_menu.mkdir(parents=True, exist_ok=True)
            
            shortcut_path = start_menu / f"{self.app_name}.lnk"
            
            # Use the same shortcut creation logic as desktop
            return self.create_windows_shortcut_at(shortcut_path)
        except Exception as e:
            print(f"Error creating start menu entry: {e}")
            return False
    
    def create_windows_shortcut_at(self, path):
        """Create Windows shortcut at specific path"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            target = sys.executable
            wDir = str(Path(__file__).parent)
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(path))
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{Path(__file__).parent / "vertikal_gui.py"}"'
            shortcut.WorkingDirectory = wDir
            shortcut.save()
            
            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"Error creating shortcut: {e}")
            return False

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vertikal Installer")
        self.root.geometry("500x400")
        self.root.configure(bg='#f0f0f0')
        
        self.installer = VertikalInstaller()
        self.setup_ui()
    
    def setup_ui(self):
        """Create installer UI"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🚀 Vertikal Installer", 
                              font=('Arial', 18, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Welcome text
        welcome_text = tk.Text(main_frame, height=6, font=('Arial', 10),
                              bg='#ecf0f1', fg='#2c3e50', wrap='word')
        welcome_text.pack(fill='x', pady=(0, 20))
        
        welcome_content = """Welcome to Vertikal Assistant!

This installer will:
• Install the Vertikal package
• Create a desktop shortcut
• Set up the application for easy use

Vertikal is a file-aware ChatGPT assistant that works great in RStudio and for data analysis projects."""
        
        welcome_text.insert(1.0, welcome_content)
        welcome_text.config(state='disabled')
        
        # Progress frame
        progress_frame = tk.Frame(main_frame, bg='#f0f0f0')
        progress_frame.pack(fill='x', pady=(0, 20))
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill='x')
        
        # Status text
        self.status_text = tk.Text(main_frame, height=4, font=('Arial', 9),
                                  bg='#ecf0f1', fg='#2c3e50', wrap='word')
        self.status_text.pack(fill='x', pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        self.install_btn = tk.Button(button_frame, text="Install Vertikal",
                                    command=self.start_installation,
                                    bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                    height=2)
        self.install_btn.pack(side='left', padx=(0, 10))
        
        self.close_btn = tk.Button(button_frame, text="Close",
                                  command=self.root.quit,
                                  bg='#95a5a6', fg='white', font=('Arial', 12, 'bold'),
                                  height=2)
        self.close_btn.pack(side='right')
    
    def log_status(self, message):
        """Log status message"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def start_installation(self):
        """Start the installation process"""
        self.install_btn.config(state='disabled')
        self.progress.start()
        
        # Run installation in thread
        import threading
        thread = threading.Thread(target=self.run_installation)
        thread.daemon = True
        thread.start()
    
    def run_installation(self):
        """Run the installation process"""
        try:
            self.log_status("🔍 Checking system...")
            
            # Install vertikal package
            self.log_status("📦 Installing Vertikal package...")
            success, message = self.installer.install_vertikal()
            if not success:
                self.log_status(f"❌ {message}")
                return
            
            self.log_status("✅ Vertikal package installed")
            
            # Create desktop shortcut
            self.log_status("🖥️ Creating desktop shortcut...")
            if self.installer.create_desktop_shortcut():
                self.log_status("✅ Desktop shortcut created")
            else:
                self.log_status("⚠️ Could not create desktop shortcut")
            
            # Create start menu entry (Windows)
            if platform.system() == "Windows":
                self.log_status("📋 Creating start menu entry...")
                if self.installer.create_start_menu_entry():
                    self.log_status("✅ Start menu entry created")
                else:
                    self.log_status("⚠️ Could not create start menu entry")
            
            self.log_status("🎉 Installation complete!")
            self.log_status("💡 You can now launch Vertikal from your desktop or start menu")
            
        except Exception as e:
            self.log_status(f"❌ Installation failed: {e}")
        finally:
            self.progress.stop()
            self.install_btn.config(state='normal')
    
    def run(self):
        """Run the installer"""
        self.root.mainloop()

def main():
    """Main entry point"""
    installer = InstallerGUI()
    installer.run()

if __name__ == "__main__":
    main()
