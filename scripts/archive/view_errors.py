#!/usr/bin/env python3
"""
Simple error viewer for developers
Just run this to see what's broken
"""

from pathlib import Path
import sys

def view_errors():
    """Show recent errors"""
    log_file = Path.home() / ".nocturnal_archive" / "errors.log"
    
    if not log_file.exists():
        print("✅ No errors logged yet - everything's working!")
        return
    
    # Read last 50 lines (most recent errors)
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    recent = lines[-200:] if len(lines) > 200 else lines
    
    print("=" * 60)
    print("RECENT ERRORS")
    print("=" * 60)
    print("".join(recent))
    print("=" * 60)
    print(f"\nTotal lines in log: {len(lines)}")
    print(f"Log file: {log_file}")

if __name__ == "__main__":
    view_errors()
