#!/usr/bin/env python3
"""
Auto-updater for Nocturnal Archive
Checks for updates and handles installation
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

class NocturnalUpdater:
    """Handles automatic updates for Nocturnal Archive"""
    
    def __init__(self):
        self.current_version = self.get_current_version()
        self.package_name = "nocturnal-archive"
        self.pypi_url = f"https://pypi.org/pypi/{self.package_name}/json"
        self.kill_switch_url = "https://api.nocturnal.dev/api/admin/status"
    
    def check_kill_switch(self) -> Dict[str, Any]:
        """Check if kill switch is activated"""
        try:
            with urllib.request.urlopen(self.kill_switch_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception:
            # If we can't reach the kill switch API, allow operation
            return {"enabled": True, "message": ""}
    
    def get_current_version(self) -> str:
        """Get current installed version"""
        if pkg_resources:
            try:
                return pkg_resources.get_distribution(self.package_name).version
            except (pkg_resources.DistributionNotFound, Exception):
                pass
        
        # Fallback: try to get version from installed package
        try:
            import nocturnal_archive
            return getattr(nocturnal_archive, '__version__', '1.0.0')
        except ImportError:
            return "1.0.0"
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check if updates are available"""
        try:
            with urllib.request.urlopen(self.pypi_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data["info"]["version"]
            
            if self.is_newer_version(latest_version, self.current_version):
                return {
                    "current": self.current_version,
                    "latest": latest_version,
                    "available": True,
                    "release_notes": data["info"].get("description", ""),
                    "download_url": f"https://pypi.org/project/{self.package_name}/{latest_version}/"
                }
            
            return {
                "current": self.current_version,
                "latest": latest_version,
                "available": False
            }
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Package not published to PyPI yet - this is normal for development
                return {
                    "available": False,
                    "current": self.current_version,
                    "latest": self.current_version,
                    "note": "Development version (not published to PyPI)"
                }
            # Silently ignore other HTTP errors
            return None
        except (urllib.error.URLError, Exception):
            # Silently ignore network errors
            return None
    
    def is_newer_version(self, latest: str, current: str) -> bool:
        """Check if latest version is newer than current"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def update_package(self, force: bool = False) -> bool:
        """Update the package to latest version"""
        try:
            print("🔄 Updating Nocturnal Archive...")
            
            # Check if update is needed
            if not force:
                update_info = self.check_for_updates()
                if not update_info or not update_info["available"]:
                    print("✅ No updates available")
                    return True
            
            # Perform update
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", self.package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                new_version = self.get_current_version()
                print(f"✅ Updated to version {new_version}")
                return True
            else:
                print(f"❌ Update failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Update error: {e}")
            return False
    
    def show_update_status(self):
        """Show current update status"""
        print(f"📦 Current version: {self.current_version}")
        
        update_info = self.check_for_updates()
        if update_info:
            if update_info["available"]:
                print(f"🆕 Latest version: {update_info['latest']} (available)")
                print(f"📥 Download: {update_info['download_url']}")
            else:
                print(f"✅ Up to date: {update_info['latest']}")
        else:
            print("⚠️ Could not check for updates")

def main():
    """CLI for updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nocturnal Archive Updater")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--update", action="store_true", help="Update to latest version")
    parser.add_argument("--force", action="store_true", help="Force update even if up to date")
    parser.add_argument("--status", action="store_true", help="Show update status")
    
    args = parser.parse_args()
    
    updater = NocturnalUpdater()
    
    if args.check:
        update_info = updater.check_for_updates()
        if update_info and update_info["available"]:
            print(f"🆕 Update available: {update_info['current']} → {update_info['latest']}")
        else:
            print("✅ No updates available")
    
    elif args.update:
        updater.update_package(force=args.force)
    
    elif args.status:
        updater.show_update_status()
    
    else:
        # Default: check and offer update
        update_info = updater.check_for_updates()
        if update_info and update_info["available"]:
            print(f"🆕 Update available: {update_info['current']} → {update_info['latest']}")
            response = input("Update now? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                updater.update_package()
        else:
            print("✅ No updates available")

if __name__ == "__main__":
    main()
