#!/usr/bin/env python3
"""
RStudio Integration for R/SQL Assistant Server
Provides seamless integration with RStudio terminal and R environment
"""

import os
import sys
import subprocess
import json
import requests
from typing import Optional, Dict, Any
import time

class RStudioAssistant:
    """RStudio-integrated assistant that works with the server"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or os.getenv('ASSISTANT_SERVER_URL', 'http://localhost:8000')
        self.session = requests.Session()
        self.session.timeout = 30
        self.r_available = self._check_r_availability()
        self.rstudio_available = self._check_rstudio_available()
        
    def _check_r_availability(self) -> bool:
        """Check if R is available in the system"""
        try:
            result = subprocess.run(['R', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_rstudio_available(self) -> bool:
        """Check if RStudio is available"""
        return 'RSTUDIO' in os.environ or 'RSTUDIO_PANDOC' in os.environ
    
    def ask_question(self, question: str, context: str = None) -> str:
        """Ask a question to the server with R/RStudio context"""
        try:
            # Enhance question with context
            enhanced_question = self._enhance_question_with_context(question, context)
            
            payload = {
                "question": enhanced_question,
                "user_id": f"rstudio_{os.getenv('USER', 'unknown')}",
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.1,
                "max_tokens": 1500
            }
            
            response = self.session.post(
                f"{self.server_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._format_response(data["response"])
            else:
                return f"❌ Server error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"❌ Connection error: {e}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _enhance_question_with_context(self, question: str, context: str = None) -> str:
        """Enhance question with R/RStudio context"""
        context_info = []
        
        if self.r_available:
            context_info.append("R is available on this system")
        
        if self.rstudio_available:
            context_info.append("Running in RStudio environment")
        
        if context:
            context_info.append(f"Additional context: {context}")
        
        # Add current working directory
        try:
            cwd = os.getcwd()
            context_info.append(f"Current directory: {cwd}")
        except:
            pass
        
        # Add R version if available
        if self.r_available:
            try:
                result = subprocess.run(['R', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    context_info.append(f"R version: {version_line}")
            except:
                pass
        
        if context_info:
            enhanced = f"Context: {'; '.join(context_info)}\n\nQuestion: {question}"
        else:
            enhanced = question
            
        return enhanced
    
    def _format_response(self, response: str) -> str:
        """Format response for RStudio terminal"""
        # Add RStudio-specific formatting
        formatted = f"🤖 R/SQL Assistant:\n{response}\n"
        
        # Add helpful commands if response contains R code
        if "```r" in response.lower() or "library(" in response.lower():
            formatted += "\n💡 Tip: You can copy R code directly from this response!"
        
        return formatted
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about the current workspace"""
        info = {
            "r_available": self.r_available,
            "rstudio_available": self.rstudio_available,
            "working_directory": os.getcwd(),
            "server_url": self.server_url
        }
        
        # Get R version
        if self.r_available:
            try:
                result = subprocess.run(['R', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info["r_version"] = result.stdout.split('\n')[0]
            except:
                pass
        
        # Get installed R packages (if R is available)
        if self.r_available:
            try:
                result = subprocess.run([
                    'R', '--slave', '-e', 
                    'cat(paste(installed.packages()[,1], collapse=", "))'
                ], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    info["r_packages"] = result.stdout.strip()
            except:
                pass
        
        return info
    
    def test_server_connection(self) -> bool:
        """Test connection to the server"""
        try:
            response = self.session.get(f"{self.server_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False

def main():
    """Main interactive loop for RStudio integration"""
    print("🤖 R/SQL Assistant - RStudio Integration")
    print("=" * 50)
    
    # Initialize assistant
    assistant = RStudioAssistant()
    
    # Test server connection
    if not assistant.test_server_connection():
        print("❌ Cannot connect to server!")
        print(f"🔧 Server URL: {assistant.server_url}")
        print("💡 Make sure the server is running")
        return
    
    print("✅ Connected to server")
    
    # Show workspace info
    info = assistant.get_workspace_info()
    print(f"📊 R Available: {'✅' if info['r_available'] else '❌'}")
    print(f"📊 RStudio: {'✅' if info['rstudio_available'] else '❌'}")
    print(f"📁 Working Directory: {info['working_directory']}")
    
    if 'r_version' in info:
        print(f"🔢 R Version: {info['r_version']}")
    
    print("\n💡 Ask me anything about R or SQL!")
    print("📝 Type 'quit' to exit, 'info' for workspace info")
    print()
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'info':
                info = assistant.get_workspace_info()
                print(f"\n📊 Workspace Information:")
                print(f"  R Available: {'✅' if info['r_available'] else '❌'}")
                print(f"  RStudio: {'✅' if info['rstudio_available'] else '❌'}")
                print(f"  Working Directory: {info['working_directory']}")
                print(f"  Server URL: {info['server_url']}")
                if 'r_version' in info:
                    print(f"  R Version: {info['r_version']}")
                print()
                continue
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            response = assistant.ask_question(question)
            print(f"\n{response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
