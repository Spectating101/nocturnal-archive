#!/usr/bin/env python3
"""
Dashboard CLI - Start the developer dashboard
"""

import sys
import os
from nocturnal_archive.dashboard import run_dashboard

if __name__ == '__main__':
    # Check for admin password
    admin_password = os.getenv('NOCTURNAL_ADMIN_PASSWORD')
    
    if not admin_password:
        print("⚠️  Warning: NOCTURNAL_ADMIN_PASSWORD not set. Using default 'admin123'")
        print("   Set it with: export NOCTURNAL_ADMIN_PASSWORD=your_secure_password")
        print()
    
    # Parse command line args
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    run_dashboard(port=port, debug='--debug' in sys.argv)
