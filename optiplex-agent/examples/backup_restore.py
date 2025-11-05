#!/usr/bin/env python3
"""Example of backup and restore functionality"""
from optiplex import OptiplexAgent
from pathlib import Path

def main():
    agent = OptiplexAgent(root_dir=".")

    test_file = "test_backup.py"

    # Create a test file
    print(f"Creating test file: {test_file}")
    Path(test_file).write_text("# Original version\nprint('Hello')\n")

    # Make some edits through the agent
    print("Making first edit...")
    agent.file_ops.write_file(test_file, "# Version 2\nprint('Hello World')\n")

    print("Making second edit...")
    agent.file_ops.write_file(test_file, "# Version 3\nprint('Hello World!')\n")

    print("Making third edit...")
    agent.file_ops.write_file(test_file, "# Version 4\nprint('Goodbye World')\n")

    # List backups
    print(f"\nBackups for {test_file}:")
    backups = agent.list_backups(test_file)
    for i, backup in enumerate(backups):
        print(f"  {i}: {backup.name} (modified: {backup.stat().st_mtime})")

    # Restore from backup
    if backups:
        print(f"\nRestoring from backup: {backups[0].name}")
        agent.restore_backup(test_file, str(backups[0]))

        print(f"\nRestored content:")
        print(Path(test_file).read_text())

    # Cleanup
    print("\nCleaning up...")
    Path(test_file).unlink(missing_ok=True)
    print("Done!")


if __name__ == "__main__":
    main()
