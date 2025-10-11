#!/usr/bin/env python3
"""
Nocturnal Archive CLI - Command Line Interface
Provides a terminal interface similar to cursor-agent
"""

import argparse
import asyncio
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest
from .setup_config import NocturnalConfig, DEFAULT_QUERY_LIMIT, MANAGED_SECRETS
from .telemetry import TelemetryManager
from .updater import NocturnalUpdater

class NocturnalCLI:
    """Command Line Interface for Nocturnal Archive"""
    
    def __init__(self):
        self.agent: Optional[EnhancedNocturnalAgent] = None
        self.session_id = f"cli_{os.getpid()}"
        self.telemetry = None
        self.console = Console(theme=Theme({
            "banner": "bold magenta",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
        }))
        self._tips = [
            "Use [bold]nocturnal --setup[/] to rerun the onboarding wizard anytime.",
            "Run [bold]nocturnal tips[/] when you need a refresher on power moves.",
            "Pass a one-off question directly: [bold]nocturnal \"summarize the latest 10-Q\"[/].",
            "Enable verbose logging by exporting [bold]NOCTURNAL_DEBUG=1[/] before launching.",
            "Use [bold]/plan[/] inside the chat to nudge the agent toward structured research steps.",
            "Hit [bold]Ctrl+C[/] to stop a long-running call; the agent will clean up gracefully.",
            "Remember the sandbox: prefix shell commands with [bold]![/] to execute safe utilities only.",
            "If you see an auto-update notice, the CLI will restart itself to load the latest build.",
        ]
    
    async def initialize(self):
        """Initialize the agent with automatic updates"""
        # Check for update notifications from previous runs
        self._check_update_notification()
        self._show_intro_panel()

        self._enforce_latest_build()

        config = NocturnalConfig()
        had_config = config.setup_environment()
        TelemetryManager.refresh()
        self.telemetry = TelemetryManager.get()

        if not config.check_setup():
            self.console.print("\n[warning]👋 Hey there, looks like this machine hasn't met Nocturnal yet.[/warning]")
            self.console.print("[banner]Let's get you signed in — this only takes a minute.[/banner]")
            try:
                if not config.interactive_setup():
                    self.console.print("[error]❌ Setup was cancelled. Exiting without starting the agent.[/error]")
                    return False
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[error]❌ Setup interrupted. Exiting without starting the agent.[/error]")
                return False
            config.setup_environment()
            TelemetryManager.refresh()
            self.telemetry = TelemetryManager.get()
        elif not had_config:
            # config.setup_environment() may have populated env vars from file silently
            self.console.print("[success]⚙️  Loaded saved credentials for this device.[/success]")
        
        self.agent = EnhancedNocturnalAgent()
        success = await self.agent.initialize()
        
        if not success:
            self.console.print("[error]❌ Failed to initialize agent. Please check your configuration.[/error]")
            self.console.print("\n💡 Setup help:")
            self.console.print("   • Run `cite-agent --setup` to configure your account")
            self.console.print("   • Ensure you're logged in with valid credentials")
            self.console.print("   • Check your internet connection to the backend")
            return False
        
        self._show_ready_panel()
        self._show_beta_banner()
        return True

    def _show_beta_banner(self):
        account_email = os.getenv("NOCTURNAL_ACCOUNT_EMAIL", "")
        configured_limit = DEFAULT_QUERY_LIMIT
        if configured_limit <= 0:
            limit_text = "Unlimited"
        else:
            limit_text = f"{configured_limit}"
        details = [
            f"Daily limit: [bold]{limit_text}[/] queries",
            "Telemetry streaming: [bold]enabled[/] (control plane)",
            "Auto-update: [bold]enforced[/] on launch",
            "Sandbox: safe shell commands only • SQL workflows supported",
        ]
        if account_email:
            details.insert(0, f"Signed in as: [bold]{account_email}[/]")

        panel = Panel(
            "\n".join(details),
            title="🎟️  Beta Access Active",
            border_style="magenta",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def _show_intro_panel(self):
        message = (
            "Warming up your research cockpit…\n"
            "[dim]Loading config, telemetry, and background update checks.[/dim]"
        )
        panel = Panel(
            message,
            title="🌙  Initializing Nocturnal Archive",
            border_style="magenta",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def _show_ready_panel(self):
        panel = Panel(
            "Systems check complete.\n"
            "Type [bold]help[/] for commands or [bold]tips[/] for power moves.",
            title="✅ Nocturnal Archive ready!",
            border_style="green",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)
    
    def _enforce_latest_build(self):
        """Ensure the CLI is running the most recent published build."""
        try:
            updater = NocturnalUpdater()
            update_info = updater.check_for_updates()
        except Exception:
            return

        if not update_info or not update_info.get("available"):
            return

        latest_version = update_info.get("latest", "latest")
        self.console.print(f"[banner]⬆️  Updating Nocturnal Archive to {latest_version} before launch...[/banner]")

        if updater.update_package():
            self._save_update_notification(latest_version)
            self.console.print("[warning]♻️  Restarting to finish applying the update...[/warning]")
            self._restart_cli()

    def _restart_cli(self):
        """Re-exec the CLI using the current interpreter and arguments."""
        try:
            argv = [sys.executable, "-m", "nocturnal_archive.cli", *sys.argv[1:]]
            os.execv(sys.executable, argv)
        except Exception:
            # If restart fails just continue in the current process.
            pass
    
    def _save_update_notification(self, new_version):
        """Save update notification for next run"""
        try:
            import json
            from pathlib import Path
            
            notify_file = Path.home() / ".nocturnal_archive" / "update_notification.json"
            notify_file.parent.mkdir(exist_ok=True)
            
            with open(notify_file, 'w') as f:
                json.dump({
                    "updated_to": new_version,
                    "timestamp": time.time()
                }, f)
        except Exception:
            pass
    
    def _check_update_notification(self):
        """Check if we should show update notification"""
        try:
            import json
            import time
            from pathlib import Path
            
            notify_file = Path.home() / ".nocturnal_archive" / "update_notification.json"
            if notify_file.exists():
                with open(notify_file, 'r') as f:
                    data = json.load(f)
                
                # Show notification if update happened in last 24 hours
                if time.time() - data.get("timestamp", 0) < 86400:
                    self.console.print(f"[success]🎉 Updated to version {data['updated_to']}![/success]")
                    
                # Clean up notification
                notify_file.unlink()
                
        except Exception:
            pass
    
    async def interactive_mode(self):
        """Interactive chat mode"""
        if not await self.initialize():
            return
        
        self.console.print("\n[bold]🤖 Interactive Mode[/] — Type your questions or 'quit' to exit")
        self.console.rule(style="magenta")
        
        try:
            while True:
                try:
                    user_input = self.console.input("\n[bold cyan]👤 You[/]: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    if user_input.lower() == 'tips':
                        self.show_tips()
                        continue
                    if user_input.lower() == 'feedback':
                        self.collect_feedback()
                        continue
                    
                    if not user_input:
                        continue
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n[warning]👋 Goodbye![/warning]")
                    break
                
                self.console.print("[bold violet]🤖 Agent[/]: ", end="", highlight=False)
                
                try:
                    request = ChatRequest(
                        question=user_input,
                        user_id="cli_user",
                        conversation_id=self.session_id
                    )
                    
                    response = await self.agent.process_request(request)
                    
                    # Print response with proper formatting
                    self.console.print(response.response)
                    
                    # Show usage stats occasionally
                    if hasattr(self.agent, 'daily_token_usage') and self.agent.daily_token_usage > 0:
                        stats = self.agent.get_usage_stats()
                        if stats['usage_percentage'] > 10:  # Show if >10% used
                            self.console.print(f"\n📊 Usage: {stats['usage_percentage']:.1f}% of daily limit")
                
                except Exception as e:
                    self.console.print(f"\n[error]❌ Error: {e}[/error]")
        
        finally:
            if self.agent:
                await self.agent.close()
    
    async def single_query(self, question: str):
        """Process a single query"""
        if not await self.initialize():
            return
        
        try:
            self.console.print(f"🤖 [bold]Processing[/]: {question}")
            self.console.rule(style="magenta")
            
            request = ChatRequest(
                question=question,
                user_id="cli_user",
                conversation_id=self.session_id
            )
            
            response = await self.agent.process_request(request)
            
            self.console.print(f"\n📝 [bold]Response[/]:\n{response.response}")
            
            if response.tools_used:
                self.console.print(f"\n🔧 Tools used: {', '.join(response.tools_used)}")
            
            if response.tokens_used > 0:
                stats = self.agent.get_usage_stats()
                self.console.print(
                    f"\n📊 Tokens used: {response.tokens_used} "
                    f"(Daily usage: {stats['usage_percentage']:.1f}%)"
                )
        
        finally:
            if self.agent:
                await self.agent.close()
    
    def setup_wizard(self):
        """Interactive setup wizard"""
        config = NocturnalConfig()
        return config.interactive_setup()

    def show_tips(self):
        """Display a rotating set of CLI power tips"""
        sample_count = 4 if len(self._tips) >= 4 else len(self._tips)
        tips = random.sample(self._tips, sample_count)
        table = Table(show_header=False, box=box.MINIMAL_DOUBLE_HEAD, padding=(0, 1))
        for tip in tips:
            table.add_row(f"• {tip}")

        self.console.print(Panel(table, title="✨ Quick Tips", border_style="cyan", padding=(1, 2)))
        self.console.print("[dim]Run `nocturnal tips` again for a fresh batch.[/dim]")

    def collect_feedback(self) -> int:
        """Collect feedback from the user and store it locally"""
        self.console.print(
            Panel(
                "Share what’s working, what feels rough, or any paper/finance workflows you wish existed.\n"
                "Press Enter on an empty line to finish.",
                title="📝 Beta Feedback",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        lines = []
        while True:
            try:
                line = self.console.input("[dim]> [/]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("[warning]Feedback capture cancelled.[/warning]")
                return 1

            if not line.strip():
                break
            lines.append(line)

        if not lines:
            self.console.print("[warning]No feedback captured — nothing was saved.[/warning]")
            return 1

        feedback_dir = Path.home() / ".nocturnal_archive" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        feedback_path = feedback_dir / f"feedback-{timestamp}.md"

        content = "\n".join(lines)
        with open(feedback_path, "w", encoding="utf-8") as handle:
            handle.write("# Nocturnal Archive Beta Feedback\n")
            handle.write(f"timestamp = {timestamp}Z\n")
            handle.write("\n")
            handle.write(content)
            handle.write("\n")

        self.console.print(
            f"[success]Thanks for the intel! Saved to[/success] [bold]{feedback_path}[/bold]"
        )
        self.console.print("[dim]Attach that file when you send feedback to the team.[/dim]")
        return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Nocturnal Archive - AI Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nocturnal                    # Interactive mode
  nocturnal "find papers on ML" # Single query
  nocturnal --setup            # Setup wizard
  nocturnal --version          # Show version
        """
    )
    
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Single query to process (if not provided, starts interactive mode)'
    )
    
    parser.add_argument(
        '--setup', 
        action='store_true', 
        help='Run setup wizard for API keys'
    )
    
    parser.add_argument(
        '--version', 
        action='store_true', 
        help='Show version information'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Force interactive mode even with query'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='Check for and install updates'
    )
    
    parser.add_argument(
        '--check-updates',
        action='store_true',
        help='Check for available updates'
    )
    
    # Auto-update is now enforced; no CLI flag provided to disable it.

    parser.add_argument(
        '--tips',
        action='store_true',
        help='Show quick CLI tips and exit'
    )

    parser.add_argument(
        '--feedback',
        action='store_true',
        help='Capture beta feedback and save it locally'
    )

    parser.add_argument(
        '--import-secrets',
        metavar='PATH',
        help='Import API keys from a .env style file'
    )

    parser.add_argument(
        '--no-plaintext',
        action='store_true',
        help='Fail secret import if keyring is unavailable'
    )
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print("Cite-Agent v1.0.4")
        print("AI Research Assistant - Backend-Only Distribution")
        return

    if args.tips or (args.query and args.query.lower() == "tips" and not args.interactive):
        cli = NocturnalCLI()
        cli.show_tips()
        return

    if args.feedback or (args.query and args.query.lower() == "feedback" and not args.interactive):
        cli = NocturnalCLI()
        exit_code = cli.collect_feedback()
        sys.exit(exit_code)
    
    # Handle secret import before setup as it can be used non-interactively
    if args.import_secrets:
        config = NocturnalConfig()
        try:
            results = config.import_from_env_file(args.import_secrets, allow_plaintext=not args.no_plaintext)
        except FileNotFoundError as exc:
            print(f"❌ {exc}")
            sys.exit(1)
        if not results:
            print("⚠️ No supported secrets found in the provided file.")
            sys.exit(1)
        overall_success = True
        for key, (status, message) in results.items():
            label = MANAGED_SECRETS.get(key, {}).get('label', key)
            icon = "✅" if status else "⚠️"
            print(f"{icon} {label}: {message}")
            if not status:
                overall_success = False
        sys.exit(0 if overall_success else 1)

    # Handle setup
    if args.setup:
        cli = NocturnalCLI()
        success = cli.setup_wizard()
        sys.exit(0 if success else 1)
    
    # Handle updates
    if args.update or args.check_updates:
        updater = NocturnalUpdater()
        if args.update:
            success = updater.update_package()
            sys.exit(0 if success else 1)
        else:
            updater.show_update_status()
            sys.exit(0)
    
    # Handle query or interactive mode
    async def run_cli():
        cli = NocturnalCLI()
        
        if args.query and not args.interactive:
            await cli.single_query(args.query)
        else:
            await cli.interactive_mode()
    
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
