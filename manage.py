#!/usr/bin/env python3
"""
Nocturnal Archive - Unified Management Tool
Consolidates all scattered scripts into one CLI interface
"""

import argparse
import os
import subprocess
import sys
import shutil
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}{title}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")

def run_command(cmd, check=True, cwd=None):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, check=check, cwd=cwd,
                          capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr

def get_directory_size(path="."):
    """Get directory size in human readable format"""
    result = run_command(f"du -sh {path}", check=False)
    return result.split()[0] if result else "Unknown"

# ============================================================================
# CLEANUP COMMANDS
# ============================================================================

def cleanup_all(args):
    """Clean up virtual environments, cache, and generated files"""
    print_section("🧹 Repository Cleanup")

    before_size = get_directory_size(".")
    print(f"{Colors.YELLOW}Current size: {before_size}{Colors.NC}\n")

    items_to_remove = [
        (".venv", "Root virtual environment"),
        ("nocturnal-archive-api/.venv", "Nested virtual environment"),
    ]

    # Remove virtual environments
    for path, description in items_to_remove:
        if os.path.exists(path):
            print(f"Removing {description}...")
            shutil.rmtree(path)
            print(f"{Colors.GREEN}✓ Removed {path}{Colors.NC}")

    # Remove Python cache
    print("\nRemoving Python cache files...")
    run_command("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true", check=False)
    run_command("find . -type f -name '*.pyc' -delete 2>/dev/null || true", check=False)
    print(f"{Colors.GREEN}✓ Removed Python cache{Colors.NC}")

    # Remove test artifacts
    print("\nRemoving test artifacts...")
    for item in ["htmlcov", ".coverage", ".pytest_cache"]:
        for root, dirs, _ in os.walk("."):
            if item in dirs:
                shutil.rmtree(os.path.join(root, item))
    print(f"{Colors.GREEN}✓ Removed test artifacts{Colors.NC}")

    after_size = get_directory_size(".")
    print(f"\n{Colors.GREEN}Cleanup complete!{Colors.NC}")
    print(f"Before: {before_size}")
    print(f"After:  {after_size}")

def cleanup_cache(args):
    """Clean only Python cache files"""
    print_section("🗑️  Cleaning Python Cache")
    run_command("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true", check=False)
    run_command("find . -type f -name '*.pyc' -delete 2>/dev/null || true", check=False)
    print(f"{Colors.GREEN}✓ Cache cleaned{Colors.NC}")

# ============================================================================
# SETUP COMMANDS
# ============================================================================

def setup_dev(args):
    """Set up development environment"""
    print_section("🚀 Development Setup")

    api_dir = Path("nocturnal-archive-api")
    venv_path = api_dir / ".venv"

    # Create virtual environment
    if not venv_path.exists():
        print("Creating virtual environment...")
        run_command(f"python3 -m venv {venv_path}")
        print(f"{Colors.GREEN}✓ Virtual environment created{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}Virtual environment already exists{Colors.NC}")

    # Install dependencies
    install_type = args.type or "minimal"
    pip_cmd = f"{venv_path}/bin/pip"

    print(f"\nInstalling {install_type} dependencies...")

    if install_type == "minimal":
        run_command(f"{pip_cmd} install -r {api_dir}/requirements.txt")
    elif install_type == "dev":
        run_command(f"{pip_cmd} install -r {api_dir}/requirements.txt -r {api_dir}/requirements-dev.txt")
    elif install_type == "full":
        run_command(f"{pip_cmd} install -r {api_dir}/requirements.txt -r {api_dir}/requirements-dev.txt -r {api_dir}/requirements-ml.txt")

    print(f"{Colors.GREEN}✓ Dependencies installed{Colors.NC}")
    print(f"\n{Colors.BLUE}Activate with:{Colors.NC} source nocturnal-archive-api/.venv/bin/activate")

def setup_env(args):
    """Set up environment variables"""
    print_section("⚙️  Environment Setup")

    env_example = Path("nocturnal-archive-api/env.example")
    env_file = Path("nocturnal-archive-api/.env")

    if env_file.exists() and not args.force:
        print(f"{Colors.YELLOW}.env file already exists{Colors.NC}")
        print("Use --force to overwrite")
        return

    if env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"{Colors.GREEN}✓ Created .env from template{Colors.NC}")
        print(f"\n{Colors.YELLOW}Edit .env with your API keys:{Colors.NC}")
        print(f"  nano {env_file}")
    else:
        print(f"{Colors.RED}env.example not found{Colors.NC}")

# ============================================================================
# TESTING COMMANDS
# ============================================================================

def test_api(args):
    """Run API tests"""
    print_section("🧪 Running API Tests")

    os.chdir("nocturnal-archive-api")
    venv_python = ".venv/bin/python"

    if not Path(venv_python).exists():
        print(f"{Colors.RED}Virtual environment not found. Run: ./manage.py setup dev{Colors.NC}")
        return

    cmd = f"{venv_python} -m pytest tests/"
    if args.verbose:
        cmd += " -v"
    if args.coverage:
        cmd += " --cov=src --cov-report=html"

    run_command(cmd)
    print(f"{Colors.GREEN}✓ Tests completed{Colors.NC}")

def test_stress(args):
    """Run stress tests"""
    print_section("⚡ Running Stress Tests")

    if not Path("stress_test_diverse_tickers.py").exists():
        print(f"{Colors.RED}Stress test script not found{Colors.NC}")
        return

    run_command("python3 stress_test_diverse_tickers.py")
    print(f"{Colors.GREEN}✓ Stress test completed{Colors.NC}")

def test_smoke(args):
    """Run smoke tests"""
    print_section("💨 Running Smoke Tests")

    smoke_script = Path("scripts/smoke_test.py")
    if smoke_script.exists():
        run_command(f"python3 {smoke_script}")
    else:
        # Inline smoke test
        print("Starting API server...")
        # This would start the server and run basic health checks
        print(f"{Colors.YELLOW}Full smoke test requires server setup{Colors.NC}")

# ============================================================================
# SERVER COMMANDS
# ============================================================================

def server_start(args):
    """Start the API server"""
    print_section("🚀 Starting API Server")

    os.chdir("nocturnal-archive-api")
    venv_python = ".venv/bin/python"

    if not Path(venv_python).exists():
        print(f"{Colors.RED}Virtual environment not found. Run: ./manage.py setup dev{Colors.NC}")
        return

    reload_flag = "--reload" if args.reload else ""
    port = args.port or 8000

    cmd = f"{venv_python} -m uvicorn src.main:app --host 0.0.0.0 --port {port} {reload_flag}"
    print(f"Running: {cmd}")
    print(f"\n{Colors.GREEN}Server will be available at:{Colors.NC}")
    print(f"  • API: http://localhost:{port}")
    print(f"  • Docs: http://localhost:{port}/docs")
    print(f"  • Health: http://localhost:{port}/api/health\n")

    subprocess.run(cmd, shell=True)

def server_stop(args):
    """Stop the API server"""
    print_section("🛑 Stopping API Server")

    # Find and kill uvicorn processes
    result = run_command("pgrep -f 'uvicorn.*src.main:app'", check=False)
    if result.strip():
        pids = result.strip().split('\n')
        for pid in pids:
            run_command(f"kill {pid}", check=False)
        print(f"{Colors.GREEN}✓ Stopped server (PIDs: {', '.join(pids)}){Colors.NC}")
    else:
        print(f"{Colors.YELLOW}No running server found{Colors.NC}")

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

def status(args):
    """Show repository status"""
    print_section("📊 Repository Status")

    # Size
    total_size = get_directory_size(".")
    git_size = get_directory_size(".git")
    print(f"Total size: {total_size}")
    print(f"Git size: {git_size}")

    # Virtual environments
    print("\nVirtual Environments:")
    for venv in [".venv", "nocturnal-archive-api/.venv"]:
        if Path(venv).exists():
            size = get_directory_size(venv)
            print(f"  • {venv}: {size}")
        else:
            print(f"  • {venv}: {Colors.YELLOW}Not found{Colors.NC}")

    # Git status
    print("\nGit Status:")
    git_status = run_command("git status --short", check=False)
    if git_status.strip():
        print(git_status)
    else:
        print(f"  {Colors.GREEN}Working tree clean{Colors.NC}")

    # Environment
    print("\nEnvironment:")
    env_file = Path("nocturnal-archive-api/.env")
    if env_file.exists():
        print(f"  • .env: {Colors.GREEN}Found{Colors.NC}")
    else:
        print(f"  • .env: {Colors.YELLOW}Not found{Colors.NC}")

def security_audit(args):
    """Run security audit"""
    print_section("🔒 Security Audit")

    audit_script = Path("scripts/security_audit.py")
    if audit_script.exists():
        run_command(f"python3 {audit_script}")
    else:
        print(f"{Colors.YELLOW}Security audit script not found{Colors.NC}")
        print("Performing basic checks...")

        # Check for exposed secrets
        print("\nChecking for exposed secrets...")
        result = run_command("git log --all -S 'API_KEY' --oneline | head -5", check=False)
        if result.strip():
            print(f"{Colors.YELLOW}Found API_KEY mentions in git history{Colors.NC}")
        else:
            print(f"{Colors.GREEN}No obvious secrets in git history{Colors.NC}")

# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Nocturnal Archive - Unified Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./manage.py cleanup               Clean up virtual environments and cache
  ./manage.py setup dev --type dev  Set up development environment
  ./manage.py test api --coverage   Run tests with coverage
  ./manage.py server start --reload Start dev server with auto-reload
  ./manage.py status                Show repository status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Cleanup commands
    cleanup = subparsers.add_parser('cleanup', help='Cleanup commands')
    cleanup_subs = cleanup.add_subparsers(dest='subcommand')
    cleanup_subs.add_parser('all', help='Clean everything').set_defaults(func=cleanup_all)
    cleanup_subs.add_parser('cache', help='Clean only cache').set_defaults(func=cleanup_cache)
    cleanup.set_defaults(func=cleanup_all)

    # Setup commands
    setup = subparsers.add_parser('setup', help='Setup commands')
    setup_subs = setup.add_subparsers(dest='subcommand')

    setup_dev_cmd = setup_subs.add_parser('dev', help='Set up development environment')
    setup_dev_cmd.add_argument('--type', choices=['minimal', 'dev', 'full'], default='minimal',
                              help='Installation type (default: minimal)')
    setup_dev_cmd.set_defaults(func=setup_dev)

    setup_env_cmd = setup_subs.add_parser('env', help='Set up environment variables')
    setup_env_cmd.add_argument('--force', action='store_true', help='Overwrite existing .env')
    setup_env_cmd.set_defaults(func=setup_env)

    # Test commands
    test = subparsers.add_parser('test', help='Testing commands')
    test_subs = test.add_subparsers(dest='subcommand')

    test_api_cmd = test_subs.add_parser('api', help='Run API tests')
    test_api_cmd.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    test_api_cmd.add_argument('--coverage', '-c', action='store_true', help='Generate coverage report')
    test_api_cmd.set_defaults(func=test_api)

    test_subs.add_parser('stress', help='Run stress tests').set_defaults(func=test_stress)
    test_subs.add_parser('smoke', help='Run smoke tests').set_defaults(func=test_smoke)

    # Server commands
    server = subparsers.add_parser('server', help='Server commands')
    server_subs = server.add_subparsers(dest='subcommand')

    server_start_cmd = server_subs.add_parser('start', help='Start API server')
    server_start_cmd.add_argument('--reload', '-r', action='store_true', help='Enable auto-reload')
    server_start_cmd.add_argument('--port', '-p', type=int, help='Port number (default: 8000)')
    server_start_cmd.set_defaults(func=server_start)

    server_subs.add_parser('stop', help='Stop API server').set_defaults(func=server_stop)

    # Utility commands
    subparsers.add_parser('status', help='Show repository status').set_defaults(func=status)
    subparsers.add_parser('security', help='Run security audit').set_defaults(func=security_audit)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        print(f"{Colors.RED}No handler for command: {args.command}{Colors.NC}")
        parser.print_help()

if __name__ == "__main__":
    main()
