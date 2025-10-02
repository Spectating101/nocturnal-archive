#!/usr/bin/env python3
"""
Nocturnal Archive CLI - Command Line Interface
Provides a terminal interface similar to cursor-agent
"""

import asyncio
import sys
import argparse
import os
import time
from pathlib import Path
from typing import Optional

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest
from .setup_config import NocturnalConfig
from .updater import NocturnalUpdater

class NocturnalCLI:
    """Command Line Interface for Nocturnal Archive"""
    
    def __init__(self):
        self.agent: Optional[EnhancedNocturnalAgent] = None
        self.session_id = f"cli_{os.getpid()}"
    
    async def initialize(self, auto_update=True):
        """Initialize the agent with automatic updates"""
        print("🌙 Initializing Nocturnal Archive...")
        
        # Check for update notifications from previous runs
        self._check_update_notification()
        
        # Check for updates automatically (background, non-blocking)
        if auto_update:
            await self._check_and_update_background()
        
        self.agent = EnhancedNocturnalAgent()
        # Disable agent's auto-update if CLI auto-update is disabled
        if not auto_update:
            self.agent._auto_update_enabled = False
        success = await self.agent.initialize()
        
        if not success:
            print("❌ Failed to initialize agent. Please check your API keys.")
            print("\n💡 Setup help:")
            print("   1. Create .env.local file with GROQ_API_KEY")
            print("   2. Or run: nocturnal --setup")
            return False
        
        print("✅ Nocturnal Archive ready!")
        return True
    
    async def _check_and_update_background(self):
        """Check for updates in background without blocking user experience"""
        import asyncio
        import threading
        
        def update_check():
            try:
                updater = NocturnalUpdater()
                update_info = updater.check_for_updates()
                
                if update_info and update_info["available"]:
                    # Silent update - no user interruption
                    success = updater.update_package()
                    if success:
                        # Only notify on next run
                        self._save_update_notification(update_info['latest'])
                        
            except Exception:
                # Completely silent - don't interrupt user experience
                pass
        
        # Run update check in separate thread (non-blocking)
        threading.Thread(target=update_check, daemon=True).start()
    
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
                    print(f"🎉 Updated to version {data['updated_to']}!")
                    
                # Clean up notification
                notify_file.unlink()
                
        except Exception:
            pass
    
    async def interactive_mode(self, auto_update=True):
        """Interactive chat mode"""
        if not await self.initialize(auto_update):
            return
        
        print("\n🤖 Interactive Mode - Type your questions or 'quit' to exit")
        print("=" * 60)
        
        try:
            while True:
                try:
                    user_input = input("\n👤 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue
                except (EOFError, KeyboardInterrupt):
                    print("\n👋 Goodbye!")
                    break
                
                print("🤖 Agent: ", end="", flush=True)
                
                try:
                    request = ChatRequest(
                        question=user_input,
                        user_id="cli_user",
                        conversation_id=self.session_id
                    )
                    
                    response = await self.agent.process_request(request)
                    
                    # Print response with proper formatting
                    print(response.response)
                    
                    # Show usage stats occasionally
                    if hasattr(self.agent, 'daily_token_usage') and self.agent.daily_token_usage > 0:
                        stats = self.agent.get_usage_stats()
                        if stats['usage_percentage'] > 10:  # Show if >10% used
                            print(f"\n📊 Usage: {stats['usage_percentage']:.1f}% of daily limit")
                
                except Exception as e:
                    print(f"\n❌ Error: {e}")
        
        finally:
            if self.agent:
                await self.agent.close()
    
    async def single_query(self, question: str, auto_update=True):
        """Process a single query"""
        if not await self.initialize(auto_update):
            return
        
        try:
            print(f"🤖 Processing: {question}")
            print("=" * 50)
            
            request = ChatRequest(
                question=question,
                user_id="cli_user",
                conversation_id=self.session_id
            )
            
            response = await self.agent.process_request(request)
            
            print(f"\n📝 Response:\n{response.response}")
            
            if response.tools_used:
                print(f"\n🔧 Tools used: {', '.join(response.tools_used)}")
            
            if response.tokens_used > 0:
                stats = self.agent.get_usage_stats()
                print(f"\n📊 Tokens used: {response.tokens_used} (Daily usage: {stats['usage_percentage']:.1f}%)")
        
        finally:
            if self.agent:
                await self.agent.close()
    
    def setup_wizard(self):
        """Interactive setup wizard"""
        print("🚀 Nocturnal Archive Setup Wizard")
        print("=" * 40)
        
        config = NocturnalConfig()
        
        if config.check_setup():
            print("✅ Nocturnal Archive is already configured!")
            try:
                response = input("Do you want to reconfigure? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    return True
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Setup cancelled")
                return False
        
        print("\n📋 Let's set up your API keys:")
        
        # Groq API key (required)
        try:
            groq_key = input("Enter your Groq API key (required): ").strip()
            if not groq_key:
                print("❌ Groq API key is required for the AI agent")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Setup cancelled")
            return False
        
        # Optional keys
        print("\n📚 Optional API keys (press Enter to skip):")
        try:
            openalex_key = input("OpenAlex API key: ").strip()
            pubmed_key = input("PubMed API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Setup cancelled")
            return False
        
        # Save configuration
        config_data = {
            'GROQ_API_KEY': groq_key,
            'OPENALEX_API_KEY': openalex_key,
            'PUBMED_API_KEY': pubmed_key,
        }
        
        config.save_config(config_data)
        config.setup_environment()
        
        print("\n✅ Configuration saved!")
        print("🎉 You can now run: nocturnal")
        
        return True

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
    
    parser.add_argument(
        '--no-auto-update',
        action='store_true',
        help='Disable automatic background updates'
    )
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print("Nocturnal Archive v1.0.0")
        print("AI Research Assistant with real data integration")
        return
    
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
        
        # Pass auto_update flag
        auto_update = not args.no_auto_update
        
        if args.query and not args.interactive:
            await cli.single_query(args.query, auto_update)
        else:
            await cli.interactive_mode(auto_update)
    
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
