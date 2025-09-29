#!/usr/bin/env python3
"""
Auto Updater - Handles automatic updates for Windows installations
"""

import os
import sys
import json
import requests
import subprocess
import shutil
from pathlib import Path
import tempfile
from packaging import version

class AutoUpdater:
    def __init__(self):
        self.current_version = "1.0.0"
        self.update_url = "https://api.github.com/repos/yourusername/vertikal/releases/latest"
        self.download_url = "https://github.com/yourusername/vertikal/releases/download"
        self.install_dir = Path(sys.executable).parent
        self.temp_dir = Path(tempfile.gettempdir()) / "vertikal_update"
        
    def check_for_updates(self):
        """Check for available updates"""
        try:
            print("🔍 Checking for updates...")
            
            response = requests.get(self.update_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                print(f"✅ Update available: {latest_version}")
                return {
                    'available': True,
                    'version': latest_version,
                    'download_url': self._get_download_url(release_data),
                    'release_notes': release_data.get('body', '')
                }
            else:
                print("✅ You have the latest version")
                return {'available': False}
                
        except Exception as e:
            print(f"⚠️ Could not check for updates: {e}")
            return {'available': False, 'error': str(e)}
    
    def _get_download_url(self, release_data):
        """Get download URL for the latest release"""
        assets = release_data.get('assets', [])
        
        # Look for Windows installer
        for asset in assets:
            if asset['name'].endswith('.exe') and 'installer' in asset['name'].lower():
                return asset['browser_download_url']
        
        # Fallback to any executable
        for asset in assets:
            if asset['name'].endswith('.exe'):
                return asset['browser_download_url']
        
        return None
    
    def download_update(self, update_info):
        """Download the update"""
        if not update_info.get('download_url'):
            print("❌ No download URL available")
            return False
        
        try:
            print(f"📥 Downloading update {update_info['version']}...")
            
            # Create temp directory
            self.temp_dir.mkdir(exist_ok=True)
            
            # Download file
            response = requests.get(update_info['download_url'], stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            filename = update_info['download_url'].split('/')[-1]
            if not filename.endswith('.exe'):
                filename = f"vertikal-update-{update_info['version']}.exe"
            
            download_path = self.temp_dir / filename
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r   Progress: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ Download complete: {download_path}")
            return download_path
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def install_update(self, installer_path):
        """Install the update"""
        try:
            print("🔧 Installing update...")
            
            # Run installer silently
            cmd = [str(installer_path), '/S', '/D=' + str(self.install_dir)]
            result = subprocess.run(cmd, check=True)
            
            if result.returncode == 0:
                print("✅ Update installed successfully!")
                return True
            else:
                print("❌ Update installation failed")
                return False
                
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def update(self, auto_install=False):
        """Main update process"""
        print("🔄 Vertikal Auto Updater")
        print("=" * 30)
        
        # Check for updates
        update_info = self.check_for_updates()
        
        if not update_info.get('available'):
            if update_info.get('error'):
                print(f"⚠️ Update check failed: {update_info['error']}")
            return False
        
        # Show update info
        print(f"\n📋 Update Information:")
        print(f"   Current version: {self.current_version}")
        print(f"   Latest version: {update_info['version']}")
        print(f"   Release notes: {update_info['release_notes'][:100]}...")
        
        # Ask for confirmation (unless auto-install)
        if not auto_install:
            confirm = input("\nInstall update now? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Update cancelled")
                return False
        
        # Download update
        installer_path = self.download_update(update_info)
        if not installer_path:
            return False
        
        # Install update
        if self.install_update(installer_path):
            self.cleanup()
            print("\n🎉 Update complete! Please restart Vertikal.")
            return True
        else:
            self.cleanup()
            return False

class UpdateChecker:
    """Background update checker"""
    
    def __init__(self):
        self.updater = AutoUpdater()
        self.check_interval = 24 * 60 * 60  # 24 hours
        self.last_check_file = Path.home() / ".vertikal" / "last_update_check"
    
    def should_check(self):
        """Check if it's time to check for updates"""
        if not self.last_check_file.exists():
            return True
        
        try:
            last_check = self.last_check_file.stat().st_mtime
            import time
            return time.time() - last_check > self.check_interval
        except:
            return True
    
    def mark_checked(self):
        """Mark that we've checked for updates"""
        self.last_check_file.parent.mkdir(exist_ok=True)
        self.last_check_file.touch()
    
    def check_and_notify(self):
        """Check for updates and notify user"""
        if not self.should_check():
            return
        
        update_info = self.updater.check_for_updates()
        
        if update_info.get('available'):
            print(f"\n🔄 Update Available!")
            print(f"   New version: {update_info['version']}")
            print(f"   Run 'vertikal --update' to install")
        
        self.mark_checked()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vertikal Auto Updater")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--update", action="store_true", help="Update to latest version")
    parser.add_argument("--auto", action="store_true", help="Auto-install updates")
    
    args = parser.parse_args()
    
    updater = AutoUpdater()
    
    if args.check:
        update_info = updater.check_for_updates()
        if update_info.get('available'):
            print(f"Update available: {update_info['version']}")
        else:
            print("No updates available")
    elif args.update:
        updater.update(auto_install=args.auto)
    else:
        # Default: check and ask
        updater.update()

if __name__ == "__main__":
    main()
