#!/usr/bin/env python3
"""Code review example using specialized prompt"""
from optiplex import OptiplexAgent

def main():
    # Initialize agent with code review prompt
    agent = OptiplexAgent(
        root_dir=".",
        model_name="claude-3-5-sonnet",
        system_prompt_type="code_review"
    )

    # Review a specific file
    files_to_review = [
        "optiplex/agent.py",
        "optiplex/file_ops.py"
    ]

    for filepath in files_to_review:
        print(f"\n{'='*60}")
        print(f"Reviewing: {filepath}")
        print('='*60)

        response = agent.chat(
            f"Please review this file for code quality, security, and best practices",
            context_files=[filepath]
        )

        print(response.content)
        print(f"\nTokens used: {response.tokens_used}\n")


if __name__ == "__main__":
    main()
