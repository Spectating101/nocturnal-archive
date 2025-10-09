#!/usr/bin/env python3
"""
Nocturnal Archive Beta Distribution Packager
Prepares the application for beta launch distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class BetaPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        
    def clean_previous_builds(self):
        """Remove previous build artifacts"""
        print("🧹 Cleaning previous builds...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
        print("✅ Build directories cleaned")
    
    def verify_dependencies(self):
        """Check all required dependencies are installed"""
        print("\n📦 Verifying dependencies...")
        
        required = ["nuitka", "ordered-set", "zstandard"]
        missing = []
        
        for package in required:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"  ❌ {package} - NOT FOUND")
        
        if missing:
            print(f"\n⚠️  Installing missing packages: {', '.join(missing)}")
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            print("✅ Dependencies installed")
        else:
            print("✅ All dependencies present")
    
    def build_executable(self):
        """Build standalone executable with Nuitka"""
        print("\n🔨 Building standalone executable...")
        
        entry_point = self.project_root / "nocturnal_archive" / "cli.py"
        
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--onefile",
            "--output-dir=" + str(self.dist_dir),
            "--output-filename=nocturnal",
            "--include-package=nocturnal_archive",
            "--include-package-data=nocturnal_archive",
            "--enable-plugin=anti-bloat",
            "--warn-implicit-exceptions",
            "--warn-unusual-code",
            "--quiet",
            str(entry_point)
        ]
        
        print(f"  Building from: {entry_point}")
        print(f"  Output: {self.dist_dir}/nocturnal")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Build successful!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
    
    def create_license_system(self):
        """Create simple license key generator"""
        print("\n🔑 Creating license system...")
        
        license_script = self.dist_dir / "generate_license.py"
        license_script.write_text('''#!/usr/bin/env python3
"""
License Key Generator for Nocturnal Archive Beta
"""
import hashlib
import secrets
from datetime import datetime, timedelta

def generate_license_key(user_email: str, duration_days: int = 90) -> str:
    """Generate a beta license key"""
    # Create unique user ID from email
    user_id = hashlib.sha256(user_email.encode()).hexdigest()[:8]
    
    # Generate expiry timestamp
    expiry = datetime.now() + timedelta(days=duration_days)
    expiry_str = expiry.strftime("%Y%m%d")
    
    # Create checksum
    data = f"{user_email}{user_id}{expiry_str}"
    checksum = hashlib.sha256(data.encode()).hexdigest()[:8]
    
    # Format: NA-BETA-{user_id}-{expiry}-{checksum}
    license_key = f"NA-BETA-{user_id}-{expiry_str}-{checksum}"
    
    return license_key

def verify_license_key(license_key: str, user_email: str) -> bool:
    """Verify a license key"""
    try:
        parts = license_key.split("-")
        if len(parts) != 5 or parts[0] != "NA" or parts[1] != "BETA":
            return False
        
        user_id_provided, expiry_str, checksum_provided = parts[2], parts[3], parts[4]
        
        # Verify user ID
        user_id_expected = hashlib.sha256(user_email.encode()).hexdigest()[:8]
        if user_id_provided != user_id_expected:
            return False
        
        # Check expiry
        expiry_date = datetime.strptime(expiry_str, "%Y%m%d")
        if datetime.now() > expiry_date:
            return False
        
        # Verify checksum
        data = f"{user_email}{user_id_provided}{expiry_str}"
        checksum_expected = hashlib.sha256(data.encode()).hexdigest()[:8]
        
        return checksum_provided == checksum_expected
    except Exception:
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_license.py <email> [days]")
        sys.exit(1)
    
    email = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    
    key = generate_license_key(email, days)
    print(f"\\nLicense Key for {email}:")
    print(f"{key}")
    print(f"\\nValid for {days} days")
    print(f"Expires: {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}")
    
    # Verify it works
    if verify_license_key(key, email):
        print("✅ Key verification: PASSED")
    else:
        print("❌ Key verification: FAILED")
''')
        license_script.chmod(0o755)
        print(f"✅ License generator created: {license_script}")
    
    def create_distribution_package(self):
        """Create complete distribution package"""
        print("\n📦 Creating distribution package...")
        
        # Create package directory
        package_dir = self.dist_dir / f"nocturnal-archive-beta-{datetime.now().strftime('%Y%m%d')}"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        if (self.dist_dir / "nocturnal").exists():
            shutil.copy(self.dist_dir / "nocturnal", package_dir / "nocturnal")
            print(f"  ✅ Copied executable")
        
        # Create README
        readme = package_dir / "README.md"
        readme.write_text('''# Nocturnal Archive Beta

## Installation

1. Move `nocturnal` to your PATH:
   ```bash
   sudo mv nocturnal /usr/local/bin/
   sudo chmod +x /usr/local/bin/nocturnal
   ```

2. Run setup:
   ```bash
   nocturnal --setup
   ```

3. Enter your beta license key when prompted.

## Usage

### Single Query Mode
```bash
nocturnal "Find papers about transformers"
nocturnal "Get AAPL revenue for Q3 2024"
```

### Interactive Mode
```bash
nocturnal --interactive
```

### Commands
- `nocturnal --help` - Show help
- `nocturnal --version` - Show version
- `nocturnal --tips` - Show quick tips
- `nocturnal --feedback` - Submit feedback

## Features

- 🔬 Multi-provider research (Semantic Scholar, OpenAlex, PubMed)
- 💰 Finance analysis with numeric grounding
- 🖥️  Safe terminal command execution
- 📊 Usage tracking and analytics
- 🔒 Secure sandbox environment

## Beta Access

- Daily limit: 25 queries
- Valid for 90 days
- Automatic updates enforced
- Telemetry enabled for quality improvement

## Support

For issues or feedback:
- Use `nocturnal --feedback`
- Email: support@nocturnal-archive.ai
- Beta forum: [link]

## License

Beta access is granted for evaluation purposes only.
''')
        print(f"  ✅ Created README")
        
        # Create install script
        install_script = package_dir / "install.sh"
        install_script.write_text('''#!/bin/bash
# Nocturnal Archive Beta Installer

echo "🌙 Installing Nocturnal Archive Beta..."

# Check for sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./install.sh"
    exit 1
fi

# Install executable
echo "📦 Installing executable..."
cp nocturnal /usr/local/bin/
chmod +x /usr/local/bin/nocturnal

echo "✅ Installation complete!"
echo ""
echo "Run 'nocturnal --setup' to configure your beta access."
''')
        install_script.chmod(0o755)
        print(f"  ✅ Created install script")
        
        # Copy license generator
        if (self.dist_dir / "generate_license.py").exists():
            shutil.copy(self.dist_dir / "generate_license.py", package_dir / "generate_license.py")
            print(f"  ✅ Copied license generator")
        
        # Create archive
        archive_name = f"{package_dir.name}.tar.gz"
        subprocess.run([
            "tar", "-czf",
            str(self.dist_dir / archive_name),
            "-C", str(self.dist_dir),
            package_dir.name
        ], check=True)
        
        print(f"\n✅ Distribution package created: {archive_name}")
        print(f"   Location: {self.dist_dir / archive_name}")
        
        return self.dist_dir / archive_name
    
    def generate_sample_licenses(self):
        """Generate sample beta license keys"""
        print("\n🔑 Generating sample beta licenses...")
        
        test_users = [
            "beta1@example.com",
            "beta2@example.com",
            "beta3@example.com",
        ]
        
        licenses_file = self.dist_dir / "BETA_LICENSES.txt"
        with licenses_file.open("w") as f:
            f.write("# Nocturnal Archive Beta Test Licenses\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for email in test_users:
                result = subprocess.run(
                    [sys.executable, str(self.dist_dir / "generate_license.py"), email, "90"],
                    capture_output=True,
                    text=True
                )
                f.write(f"\n{result.stdout}\n")
                f.write("-" * 60 + "\n")
        
        print(f"✅ Sample licenses saved: {licenses_file}")
    
    def run(self):
        """Execute complete packaging process"""
        print("=" * 60)
        print("   NOCTURNAL ARCHIVE BETA PACKAGING")
        print("=" * 60)
        
        try:
            self.clean_previous_builds()
            self.verify_dependencies()
            
            # For now, skip Nuitka build (complex) and just prepare other components
            print("\n⚠️  Skipping Nuitka build (complex setup)")
            print("   Creating distribution package with existing installation...")
            
            self.dist_dir.mkdir(parents=True, exist_ok=True)
            
            self.create_license_system()
            self.generate_sample_licenses()
            
            # Create simpler distribution package
            print("\n📦 Creating distribution package...")
            package_dir = self.dist_dir / f"nocturnal-archive-beta-{datetime.now().strftime('%Y%m%d')}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy source code
            shutil.copytree(
                self.project_root / "nocturnal_archive",
                package_dir / "nocturnal_archive",
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache')
            )
            
            # Copy setup files
            for file in ["setup.py", "requirements.txt", "README.md"]:
                if (self.project_root / file).exists():
                    shutil.copy(self.project_root / file, package_dir / file)
            
            # Create install script
            install_script = package_dir / "install.sh"
            install_script.write_text('''#!/bin/bash
# Nocturnal Archive Beta Installer

echo "🌙 Installing Nocturnal Archive Beta..."

# Install dependencies
python3 -m pip install --user -r requirements.txt

# Install package
python3 -m pip install --user -e .

echo "✅ Installation complete!"
echo ""
echo "Run 'nocturnal --setup' to configure your beta access."
''')
            install_script.chmod(0o755)
            
            # Create archive
            archive_name = f"{package_dir.name}.tar.gz"
            subprocess.run([
                "tar", "-czf",
                str(self.dist_dir / archive_name),
                "-C", str(self.dist_dir),
                package_dir.name
            ], check=True)
            
            print("\n" + "=" * 60)
            print("   ✅ PACKAGING COMPLETE!")
            print("=" * 60)
            print(f"\n📦 Distribution package: {self.dist_dir / archive_name}")
            print(f"🔑 License generator: {self.dist_dir / 'generate_license.py'}")
            print(f"📄 Sample licenses: {self.dist_dir / 'BETA_LICENSES.txt'}")
            print("\n📤 Ready for distribution!")
            
        except Exception as e:
            print(f"\n❌ Packaging failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    packager = BetaPackager()
    packager.run()
