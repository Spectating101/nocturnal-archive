#!/usr/bin/env python3
"""
Quick Demo - Shows what the UI actually looks like
Run this to see the beautiful terminal interface!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from nocturnal_archive.ui import NocturnalUI, console
from rich.panel import Panel
from rich.text import Text
import time

def demo():
    console.clear()
    
    # Show welcome screen
    print("\n" + "="*70)
    print("DEMO 1: Welcome Screen")
    print("="*70)
    time.sleep(1)
    NocturnalUI.show_welcome_screen()
    time.sleep(2)
    
    # Show tips
    print("\n" + "="*70)
    print("DEMO 2: Quick Tips")
    print("="*70)
    time.sleep(1)
    NocturnalUI.show_tips()
    time.sleep(2)
    
    # Show query result
    print("\n" + "="*70)
    print("DEMO 3: Query Result")
    print("="*70)
    time.sleep(1)
    
    result = """I found 3 recent papers about transformer models:

1. **"Attention Is All You Need"** (2023 update)
   Authors: Vaswani et al.
   arXiv: 2301.12345
   
   This foundational paper introduces the transformer architecture, 
   which has revolutionized natural language processing.

2. **"Vision Transformers at Scale"** (2024)
   Authors: Dosovitskiy et al.
   arXiv: 2402.56789
   
   Explores how to scale vision transformers for high-resolution images
   while maintaining computational efficiency.

3. **"Efficient Transformers: A Survey"** (2024)
   Authors: Tay et al.
   arXiv: 2403.11111
   
   Comprehensive survey of methods to reduce transformer computational
   costs through various optimization techniques.

Would you like me to:
• Get full text of any paper
• Find implementation code  
• Summarize a specific paper
• Search for related work"""

    NocturnalUI.show_query_result(
        result=result,
        tools_used=["arxiv_search", "paper_filter", "summarize"],
        tokens=342
    )
    time.sleep(3)
    
    # Show main interface
    print("\n" + "="*70)
    print("DEMO 4: Main Interface (Status Bar)")
    print("="*70)
    time.sleep(1)
    NocturnalUI.show_main_interface(
        email="demo@nocturnal.dev",
        daily_limit=25,
        queries_used=3
    )
    time.sleep(2)
    
    # Show success message
    print("\n" + "="*70)
    print("DEMO 5: Success Message")
    print("="*70)
    time.sleep(1)
    NocturnalUI.show_success("Registration successful! Welcome aboard! 🎉")
    time.sleep(2)
    
    # Show error message
    print("\n" + "="*70)
    print("DEMO 6: Error Message")
    print("="*70)
    time.sleep(1)
    NocturnalUI.show_error(
        "Daily limit reached (25 queries).\n"
        "Please try again tomorrow or upgrade your plan."
    )
    time.sleep(2)
    
    # Show loading spinner
    print("\n" + "="*70)
    print("DEMO 7: Loading Spinner")
    print("="*70)
    time.sleep(1)
    
    with NocturnalUI.show_loading("Processing your query..."):
        time.sleep(2)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nThis is what users will see when they use Nocturnal Archive!")
    print("Beautiful, modern, and way better than ancient black terminals.\n")

if __name__ == '__main__':
    try:
        demo()
    except KeyboardInterrupt:
        console.print("\n\n👋 Demo interrupted!")
