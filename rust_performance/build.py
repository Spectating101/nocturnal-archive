#!/usr/bin/env python3
"""
Build script for the Rust performance module.
This script compiles the Rust code and installs it as a Python package.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def check_rust():
    """Check if Rust is installed."""
    if not run_command(["rustc", "--version"]):
        print("❌ Rust is not installed. Please install Rust from https://rustup.rs/")
        return False
    return True

def check_maturin():
    """Check if maturin is installed."""
    if not run_command([sys.executable, "-m", "pip", "show", "maturin"]):
        print("❌ Maturin is not installed. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "maturin"]):
            print("❌ Failed to install maturin")
            return False
    return True

def build_rust_module():
    """Build the Rust performance module."""
    rust_dir = Path(__file__).parent
    
    print("🔨 Building Rust performance module...")
    
    # Build the module
    if not run_command(["maturin", "build", "--release"], cwd=rust_dir):
        print("❌ Failed to build Rust module")
        return False
    
    # Find the built wheel
    target_dir = rust_dir / "target" / "wheels"
    if not target_dir.exists():
        print("❌ Build directory not found")
        return False
    
    wheels = list(target_dir.glob("*.whl"))
    if not wheels:
        print("❌ No wheel file found")
        return False
    
    wheel_path = wheels[0]
    print(f"📦 Found wheel: {wheel_path}")
    
    # Install the wheel
    print("📥 Installing wheel...")
    if not run_command([sys.executable, "-m", "pip", "install", str(wheel_path), "--force-reinstall"]):
        print("❌ Failed to install wheel")
        return False
    
    print("✅ Rust performance module built and installed successfully!")
    return True

def test_rust_module():
    """Test the Rust module."""
    print("🧪 Testing Rust module...")
    
    test_code = """
import nocturnal_performance

# Test basic functionality
scraper = nocturnal_performance.HighPerformanceScraper()
print("✅ Rust module imported successfully")

# Test text cleaning
cleaned = nocturnal_performance.fast_text_clean("Hello, world!   This is a test.")
print(f"✅ Text cleaning: {cleaned}")

# Test URL validation
is_valid = nocturnal_performance.fast_url_validation("https://example.com")
print(f"✅ URL validation: {is_valid}")

print("✅ All tests passed!")
"""
    
    if run_command([sys.executable, "-c", test_code]):
        print("✅ Rust module tests passed!")
        return True
    else:
        print("❌ Rust module tests failed!")
        return False

def main():
    """Main build function."""
    print("🚀 Building Nocturnal Archive Rust Performance Module")
    print("=" * 60)
    
    # Check prerequisites
    if not check_rust():
        sys.exit(1)
    
    if not check_maturin():
        sys.exit(1)
    
    # Build the module
    if not build_rust_module():
        sys.exit(1)
    
    # Test the module
    if not test_rust_module():
        sys.exit(1)
    
    print("\n🎉 Rust performance module is ready!")
    print("You can now use the high-performance features in your Python code.")

if __name__ == "__main__":
    main()
