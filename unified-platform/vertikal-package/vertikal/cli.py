#!/usr/bin/env python3
"""
Vertikal CLI - Entry point for the package
"""

import sys
import os
from pathlib import Path

# Add the package directory to the path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir))

# Import the main function from the package
from vertikal import main

if __name__ == "__main__":
    main()
