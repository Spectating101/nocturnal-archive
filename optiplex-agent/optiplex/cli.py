#!/usr/bin/env python3
"""Command-line interface for Optiplex Agent"""
import sys
import argparse
from pathlib import Path
from typing import Optional

from .agent import OptiplexAgent
from .config import OptiplexConfig
from .router import AdaptiveAgent

class OptiplexCLI:
    """CLI for Optiplex Agent"""

    def __init__(
        self,
        root_dir: Optional[str] = None,
        model: Optional[str] = None,
        auto_route: bool = True,
        interactive_diffs: bool = True,
        auto_apply: bool = False
    ):
        self.root_dir = root_dir or "."
        self.model = model
        self.auto_route = auto_route
        self.interactive_diffs = interactive_diffs
        self.auto_apply = auto_apply
        self.agent: Optional[OptiplexAgent] = None
        self.adaptive_agent: Optional[AdaptiveAgent] = None

    def init_agent(self, prompt_type: str = "default"):
        """Initialize the agent"""
        self.agent = OptiplexAgent(
            root_dir=self.root_dir,
            model_name=self.model,
            system_prompt_type=prompt_type,
            interactive_diffs=self.interactive_diffs,
            auto_apply=self.auto_apply
        )

        # Wrap with adaptive routing if enabled
        if self.auto_route:
            self.adaptive_agent = AdaptiveAgent(self.agent, enable_routing=True)
        else:
            self.adaptive_agent = None

    def chat_mode(self):
        """Interactive chat mode"""
        if not self.agent:
            self.init_agent()

        print(f"🤖 Optiplex Agent ({self.agent.model_config.name})")
        print(f"📁 Working directory: {self.agent.root_dir}")
        if self.auto_route:
            print("🔀 Auto-routing: ENABLED (switches models based on task complexity)")
        print("Type 'exit' to quit, 'reset' to clear history, 'help' for commands\n")

        while True:
            try:
                user_input = input("You> ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    print("👋 Goodbye!")
                    break

                if user_input.lower() == "reset":
                    self.agent.reset_conversation()
                    print("🔄 Conversation reset")
                    continue

                if user_input.lower() == "help":
                    self.show_help()
                    continue

                if user_input.lower() == "stats":
                    if self.adaptive_agent:
                        stats = self.adaptive_agent.get_routing_stats()
                        print("\n📊 Routing Statistics:")
                        print(f"Total requests: {stats['total_requests']}")
                        if stats['total_requests'] > 0:
                            print("\nModel usage:")
                            for model, count in stats['model_usage'].items():
                                print(f"  {model}: {count}")
                            print("\nComplexity distribution:")
                            for complexity, count in stats['complexity_distribution'].items():
                                print(f"  {complexity}: {count}")
                    else:
                        print("Auto-routing is disabled")
                    continue

                if user_input.lower() == "index":
                    print("📇 Indexing codebase...")
                    stats = self.agent.indexer.index_directory()
                    print(f"✅ Indexed {stats['files_indexed']} files")
                    print(f"   Created {stats['chunks_created']} code chunks")
                    if stats['files_skipped'] > 0:
                        print(f"   Skipped {stats['files_skipped']} files")
                    continue

                if user_input.lower() == "summary":
                    summary = self.agent.indexer.get_codebase_summary()
                    print("\n📊 Codebase Summary:")
                    print(f"Files: {summary['total_files']}")
                    print(f"Code chunks: {summary['total_chunks']}")
                    print(f"Classes: {summary['total_classes']}")
                    print(f"Functions: {summary['total_functions']}")
                    print(f"\nFile types: {summary['file_types']}")
                    continue

                # Check for context files
                context_files = []
                if user_input.startswith("@"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) > 1:
                        context_files = [parts[0][1:]]  # Remove @
                        user_input = parts[1]

                # Send message (with auto-routing if enabled)
                if self.adaptive_agent:
                    response = self.adaptive_agent.chat(user_input, context_files=context_files or None)
                else:
                    response = self.agent.chat(user_input, context_files=context_files or None)

                if not response.success:
                    print(f"❌ Error: {response.error}")
                    continue

                # Display response
                print(f"\n🤖 Agent> {response.content}")

                # Display tool calls
                if response.tool_calls:
                    print(f"\n🔧 Tools used:")
                    for tool in response.tool_calls:
                        print(f"  - {tool['name']}: {tool['arguments']}")
                        if "error" in tool["result"]:
                            print(f"    ❌ {tool['result']['error']}")
                        else:
                            print(f"    ✅ Success")

                print(f"\n📊 Tokens: {response.tokens_used}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def single_command(self, command: str, context_files: Optional[list] = None):
        """Execute a single command"""
        if not self.agent:
            self.init_agent()

        response = self.agent.chat(command, context_files=context_files)

        if not response.success:
            print(f"❌ Error: {response.error}", file=sys.stderr)
            sys.exit(1)

        print(response.content)

        if response.tool_calls:
            print(f"\n🔧 Tools used:")
            for tool in response.tool_calls:
                print(f"  - {tool['name']}")

    def show_help(self):
        """Show help message"""
        help_text = """
Available commands:
  exit          - Exit the chat
  reset         - Clear conversation history
  help          - Show this help message
  stats         - Show routing statistics (if auto-routing enabled)
  index         - Index codebase for fast search
  summary       - Show codebase summary (files, classes, functions)

Special syntax:
  @file.py msg  - Include file.py as context for your message

Codebase Search (ask the agent):
  "search for authentication functions"    → Searches indexed code
  "find all files importing flask"         → Finds import usage
  "where is UserModel called?"             → Finds function calls
  "summarize the codebase"                 → Get high-level overview

Auto-Routing (if enabled):
  Simple tasks   → llama-4-scout-17b (lightweight, fast)
  General tasks  → llama-3.3-70b (default, balanced)
  Coding tasks   → qwen-3-32b (fast coding model)
  Heavy tasks    → qwen-3-coder-480b (480B specialist)

Examples:
  > help me refactor this function
  > @src/main.py explain this file
  > what's the git status?
  > commit these changes with message "fix bug"
  > search for all error handling code
"""
        print(help_text)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Optiplex Agent - Personal AI coding assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Working directory (default: current directory)"
    )

    parser.add_argument(
        "-m", "--model",
        choices=list(OptiplexConfig.MODELS.keys()),
        default=OptiplexConfig.DEFAULT_MODEL,
        help=f"LLM model to use (default: {OptiplexConfig.DEFAULT_MODEL})"
    )

    parser.add_argument(
        "-p", "--prompt-type",
        choices=list(OptiplexConfig.SYSTEM_PROMPTS.keys()),
        default="default",
        help="System prompt type (default: default)"
    )

    parser.add_argument(
        "-c", "--command",
        help="Execute a single command and exit"
    )

    parser.add_argument(
        "-f", "--file",
        action="append",
        help="Include file as context (can be used multiple times)"
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models"
    )

    parser.add_argument(
        "--no-auto-route",
        action="store_true",
        help="Disable automatic model routing (stick to one model)"
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive diff confirmation (apply immediately)"
    )

    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Auto-apply all edits without confirmation (dangerous!)"
    )

    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Run in autonomous mode (work independently on tasks)"
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for file changes and trigger autonomous actions"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Max iterations for autonomous mode (default: 50)"
    )

    parser.add_argument(
        "--portfolio",
        type=str,
        help="Path to project portfolio root (for portfolio-wide tasks)"
    )

    parser.add_argument(
        "--scan-portfolio",
        action="store_true",
        help="Scan entire portfolio for tasks (TODOs, uncommitted changes, etc.)"
    )

    args = parser.parse_args()

    if args.list_models:
        print("Available models:")
        for name, config in OptiplexConfig.MODELS.items():
            print(f"  {name:20} - {config.provider:12} (context: {config.context_window})")
        sys.exit(0)

    # Initialize CLI
    auto_route = not args.no_auto_route
    interactive_diffs = not args.no_interactive
    auto_apply = args.auto_apply

    cli = OptiplexCLI(
        root_dir=args.directory,
        model=args.model,
        auto_route=auto_route,
        interactive_diffs=interactive_diffs,
        auto_apply=auto_apply
    )

    # Portfolio scan
    if args.scan_portfolio:
        from .portfolio import PortfolioScanner
        from pathlib import Path
        
        portfolio_path = Path(args.portfolio) if args.portfolio else Path.home() / "Downloads/llm_automation/project_portfolio"
        
        if not portfolio_path.exists():
            print(f"❌ Portfolio path not found: {portfolio_path}")
            sys.exit(1)
        
        print(f"🔍 Scanning portfolio: {portfolio_path}")
        scanner = PortfolioScanner(portfolio_path)
        
        print("📁 Finding projects...")
        projects = scanner.find_all_projects()
        print(f"   Found {len(projects)} projects: {[p.name for p in projects]}")
        
        print("\n📋 Scanning for tasks...")
        tasks = scanner.scan_for_tasks()
        print(f"   Found {len(tasks)} tasks")
        
        # Save to master task list
        output_file = Path(args.directory) / "portfolio_tasks.json"
        scanner.create_master_task_list(output_file)
        print(f"\n✅ Task list saved to: {output_file}")
        print(f"\n💡 Run with --autonomous to execute these tasks")
        
        sys.exit(0)
    
    # Autonomous mode
    if args.autonomous or args.watch:
        from .autonomous import AutonomousMode, WatchMode
        
        cli.init_agent(args.prompt_type)
        
        if args.watch:
            watch = WatchMode(cli.agent)
            watch.run()
        else:
            autonomous = AutonomousMode(cli.agent, max_iterations=args.max_iterations)
            autonomous.run()
        
        sys.exit(0)
    cli.init_agent(prompt_type=args.prompt_type)

    # Execute command or enter chat mode
    if args.command:
        cli.single_command(args.command, context_files=args.file)
    else:
        cli.chat_mode()


if __name__ == "__main__":
    main()
