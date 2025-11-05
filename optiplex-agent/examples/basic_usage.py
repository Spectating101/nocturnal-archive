#!/usr/bin/env python3
"""Basic usage example for Optiplex Agent"""
from optiplex import OptiplexAgent

def main():
    # Initialize agent with default model (Grok)
    agent = OptiplexAgent(
        root_dir=".",
        model_name="grok-beta"
    )

    print("Example 1: Simple question")
    response = agent.chat("What files are in the current directory?")
    print(f"Response: {response.content}\n")

    print("Example 2: With context file")
    response = agent.chat(
        "Explain what this file does",
        context_files=["examples/basic_usage.py"]
    )
    print(f"Response: {response.content}\n")

    print("Example 3: File operation")
    response = agent.chat("Create a file called test.txt with content 'Hello World'")
    print(f"Response: {response.content}")
    if response.tool_calls:
        print(f"Tools used: {[t['name'] for t in response.tool_calls]}\n")

    print("Example 4: Git status")
    response = agent.chat("What's the current git status?")
    print(f"Response: {response.content}\n")

    print("Example 5: Reset conversation")
    agent.reset_conversation()
    print("Conversation history cleared\n")


if __name__ == "__main__":
    main()
