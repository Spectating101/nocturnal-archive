#!/usr/bin/env python3
"""
Nocturnal Archive - Interactive Chatbot Launcher
Provides conversational research planning and execution
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Launch the interactive chatbot."""
    try:
        print("🚀 Launching Nocturnal Archive Interactive Chatbot...")
        print("="*60)
        
        # Import the chatbot function
        from src.services.research_service.chatbot import run_cli_chatbot
        
        # Check if environment is set up
        if not os.path.exists(".env.local"):
            print("⚠️  Warning: .env.local not found. Using default settings.")
            print("   For best results, create .env.local with your API keys.")
        
        # Launch the chatbot
        await run_cli_chatbot()
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error launching chatbot: {str(e)}")
        logger.error(f"Chatbot launch failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
