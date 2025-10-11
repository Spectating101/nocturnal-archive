#!/usr/bin/env python3
"""
Personal Code Agent - CLI tool for AI-assisted coding
Uses Cerebras API (free tier) for unlimited coding assistance

Usage:
    code-agent "fix the bug in main.py"
    code-agent chat "add error handling"
    code-agent diff "optimize this function"
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import requests

# Cerebras API configuration
CEREBRAS_API_KEYS = [
    os.getenv("CEREBRAS_API_KEY_1", "csk-34cp53294pcmrexym8h2r4x5cyy2npnrd344928yhf2hpctj"),
    os.getenv("CEREBRAS_API_KEY_2", "csk-edrc3v63k43fe4hdt529ynt4h9mfd9k9wjpjj3nn5pcvm2t4"),
    os.getenv("CEREBRAS_API_KEY_3", "csk-ek3cj5jv26hpnd2h65d8955pjmvxctdjknfv6pwehr82pnhr"),
]
CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"

# Model selection - uncomment the one you want
MODEL = "qwen-3-coder-480b"      # Best for coding (480B params, 100 req/day)
# MODEL = "qwen-3-235b-a22b-instruct-2507"  # Best general (235B params, 14.4k req/day)
# MODEL = "llama-3.3-70b"          # Fast fallback (70B params, 14.4k req/day)

# Current API key index (rotates on rate limits)
current_key_index = 0


class CodeAgent:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.context_files: List[Path] = []

    def gather_context(self, max_files: int = 10) -> str:
        """
        Gather relevant files from the project for context.
        Priority: recently modified files, Python files, small files.
        """
        context = []

        # Get all Python files, sorted by modification time
        py_files = sorted(
            self.project_root.rglob("*.py"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Filter out common non-code directories
        exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'dist', 'build'}
        py_files = [
            f for f in py_files
            if not any(part in exclude_dirs for part in f.parts)
        ]

        # Take top N files, prioritize small files
        selected_files = []
        total_size = 0
        max_total_size = 50_000  # ~50KB max context

        for file in py_files[:max_files * 2]:  # Check more files than we need
            try:
                size = file.stat().st_size
                if size > 10_000:  # Skip files >10KB
                    continue
                if total_size + size > max_total_size:
                    break
                selected_files.append(file)
                total_size += size
                if len(selected_files) >= max_files:
                    break
            except:
                continue

        # Build context string
        self.context_files = selected_files
        for file in selected_files:
            try:
                content = file.read_text()
                relative_path = file.relative_to(self.project_root)
                context.append(f"# File: {relative_path}\n{content}\n")
            except:
                continue

        return "\n".join(context)

    def call_cerebras(self, prompt: str, context: str = None) -> str:
        """Call Cerebras API with prompt and optional context."""
        global current_key_index

        # Build system message
        system_msg = """You are an expert coding assistant. Your job is to help write, fix, and improve code.

When making changes:
1. Show ONLY the changes, not the entire file
2. Use clear diff format or describe changes precisely
3. Explain your reasoning briefly
4. Be concise but complete

Example output format:
```python
# In file: main.py, line 45
# Change:
- def old_function():
+ def new_function():
    # Add error handling
+   try:
        original_code()
+   except Exception as e:
+       logger.error(f"Error: {e}")
```
"""

        # Build user message
        user_msg = prompt
        if context:
            user_msg = f"Project context:\n{context}\n\n{prompt}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        # Try each API key
        for attempt in range(len(CEREBRAS_API_KEYS)):
            api_key = CEREBRAS_API_KEYS[current_key_index]

            try:
                response = requests.post(
                    CEREBRAS_API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "temperature": 0.3,  # Lower for more deterministic code
                        "max_tokens": 4000,
                        "stream": False
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    # Rate limited, try next key
                    current_key_index = (current_key_index + 1) % len(CEREBRAS_API_KEYS)
                    continue
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return None

            except Exception as e:
                print(f"Request failed: {e}")
                current_key_index = (current_key_index + 1) % len(CEREBRAS_API_KEYS)
                continue

        print("All API keys exhausted. Try again later.")
        return None

    def chat(self, prompt: str, with_context: bool = True) -> str:
        """
        Chat with the code agent.

        Args:
            prompt: Your question or request
            with_context: Include project context (slower but smarter)
        """
        print(f"🤖 Code Agent: Processing your request...\n")

        context = None
        if with_context:
            print("📂 Gathering project context...")
            context = self.gather_context()
            if self.context_files:
                print(f"✅ Loaded {len(self.context_files)} files for context\n")

        print("💭 Thinking...\n")
        response = self.call_cerebras(prompt, context)

        if response:
            print("=" * 60)
            print(response)
            print("=" * 60)
            return response
        else:
            print("❌ Failed to get response from API")
            return None

    def apply_changes(self, response: str) -> bool:
        """
        Parse response and apply changes to files.
        This is a simple implementation - you can make it smarter.
        """
        print("\n⚠️  Apply changes manually for now.")
        print("Automatic application coming in v2!")
        return False

    def git_status(self) -> str:
        """Get current git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout
        except:
            return "Not a git repository"

    def git_diff(self) -> str:
        """Get current git diff."""
        try:
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout
        except:
            return "Not a git repository"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Personal Code Agent - AI-assisted coding with Cerebras"
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Your coding question or request"
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Don't include project files in context (faster)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show git status and recent changes"
    )
    parser.add_argument(
        "--model",
        choices=["coder", "general", "fast"],
        default="coder",
        help="Model to use: coder (480B, 100/day), general (235B, 14k/day), fast (70B, 14k/day)"
    )

    args = parser.parse_args()

    # Select model based on flag
    global MODEL
    if args.model == "coder":
        MODEL = "qwen-3-coder-480b"
    elif args.model == "general":
        MODEL = "qwen-3-235b-a22b-instruct-2507"
    elif args.model == "fast":
        MODEL = "llama-3.3-70b"

    # Initialize agent
    agent = CodeAgent()

    # Handle --status
    if args.status:
        print("Git Status:")
        print(agent.git_status())
        print("\nRecent changes:")
        print(agent.git_diff()[:1000])  # Show first 1000 chars
        return

    # Get prompt
    if not args.prompt:
        print("Error: Please provide a prompt")
        print("\nUsage:")
        print("  code-agent 'fix the bug in main.py'")
        print("  code-agent 'add error handling to api.py'")
        print("  code-agent --status")
        sys.exit(1)

    prompt = " ".join(args.prompt)

    # Chat with agent
    agent.chat(prompt, with_context=not args.no_context)


if __name__ == "__main__":
    main()
