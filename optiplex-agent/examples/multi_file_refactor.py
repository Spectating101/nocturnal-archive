#!/usr/bin/env python3
"""Multi-file refactoring example"""
from optiplex import OptiplexAgent

def main():
    # Initialize agent with refactoring prompt
    agent = OptiplexAgent(
        root_dir=".",
        model_name="grok-beta",
        system_prompt_type="refactoring"
    )

    print("Multi-file refactoring workflow\n")

    # Step 1: Analyze current structure
    print("Step 1: Analyzing project structure...")
    response = agent.chat(
        "Analyze the structure of the optiplex module and suggest improvements",
        context_files=[
            "optiplex/__init__.py",
            "optiplex/config.py",
            "optiplex/agent.py"
        ]
    )
    print(f"Analysis:\n{response.content}\n")

    # Step 2: Review specific areas
    print("Step 2: Reviewing error handling...")
    response = agent.chat(
        "Review the error handling in the agent module and suggest improvements",
        context_files=["optiplex/agent.py"]
    )
    print(f"Suggestions:\n{response.content}\n")

    # Step 3: Make changes (example - not actual execution)
    print("Step 3: Making suggested changes...")
    response = agent.chat(
        "Add better error handling to the _call_llm method with specific exceptions"
    )
    print(f"Changes:\n{response.content}\n")

    # Step 4: Review changes
    print("Step 4: Reviewing changes...")
    if agent.git_ops:
        response = agent.chat("Show me the git diff of changes")
        print(f"Diff:\n{response.content}\n")

    print("Refactoring complete!")


if __name__ == "__main__":
    main()
