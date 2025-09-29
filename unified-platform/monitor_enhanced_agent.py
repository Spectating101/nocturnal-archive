#!/usr/bin/env python3
"""
Enhanced Agent Monitor - Real-time monitoring for the enhanced interactive agent
Run this in a separate terminal to monitor the agent's performance
"""

import time
import requests
import json
from datetime import datetime
from typing import Dict, Any
import os

class EnhancedAgentMonitor:
    """Monitor the enhanced interactive agent"""
    
    def __init__(self, agent_url: str = "http://localhost:8002"):
        self.agent_url = agent_url
        self.session = requests.Session()
        self.session.timeout = 5
        
    def check_health(self) -> Dict[str, Any]:
        """Check agent health status"""
        try:
            response = self.session.get(f"{self.agent_url}/enhanced/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_r_status(self) -> Dict[str, Any]:
        """Get R session status"""
        try:
            response = self.session.get(f"{self.agent_url}/enhanced/r/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_files(self, path: str = None) -> Dict[str, Any]:
        """List files in directory"""
        try:
            params = {"path": path} if path else {}
            response = self.session.get(f"{self.agent_url}/enhanced/files/list", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def test_chat(self, question: str) -> Dict[str, Any]:
        """Test chat functionality"""
        try:
            payload = {
                "question": question,
                "use_planning": True,
                "execute_code": True
            }
            response = self.session.post(f"{self.agent_url}/enhanced/chat", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def monitor_continuous(self, interval: int = 10):
        """Continuous monitoring with real-time updates"""
        print("🔍 Enhanced Agent Monitor Started")
        print("=" * 60)
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] Monitoring Enhanced Agent...")
                
                # Health check
                health = self.check_health()
                if health["status"] == "healthy":
                    print("✅ Agent Status: HEALTHY")
                    
                    # R status
                    r_status = self.get_r_status()
                    if r_status.get("available"):
                        print(f"✅ R Status: {r_status['version']}")
                    else:
                        print(f"❌ R Status: {r_status.get('error', 'Not available')}")
                    
                    # Component status
                    components = health.get("components", {})
                    for component, status in components.items():
                        status_icon = "✅" if status else "❌"
                        print(f"{status_icon} {component.title()}: {'OK' if status else 'FAILED'}")
                    
                else:
                    print(f"❌ Agent Status: {health['status']}")
                    if "error" in health:
                        print(f"   Error: {health['error']}")
                
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
            
            time.sleep(interval)
    
    def run_interactive_test(self):
        """Interactive testing mode"""
        print("🧪 Enhanced Agent Interactive Test Mode")
        print("=" * 50)
        
        while True:
            try:
                print("\nAvailable commands:")
                print("1. health - Check agent health")
                print("2. r - Check R status")
                print("3. files [path] - List files")
                print("4. chat <question> - Test chat")
                print("5. monitor - Start continuous monitoring")
                print("6. quit - Exit")
                
                command = input("\nEnter command: ").strip().lower()
                
                if command == "quit" or command == "q":
                    break
                elif command == "health":
                    result = self.check_health()
                    print(json.dumps(result, indent=2))
                elif command == "r":
                    result = self.get_r_status()
                    print(json.dumps(result, indent=2))
                elif command.startswith("files"):
                    parts = command.split(" ", 1)
                    path = parts[1] if len(parts) > 1 else None
                    result = self.list_files(path)
                    print(json.dumps(result, indent=2))
                elif command.startswith("chat"):
                    question = command[5:].strip()
                    if question:
                        result = self.test_chat(question)
                        print(f"Response: {result.get('response', 'No response')}")
                        if result.get('tools_used'):
                            print(f"Tools used: {', '.join(result['tools_used'])}")
                    else:
                        print("Please provide a question")
                elif command == "monitor":
                    self.monitor_continuous(5)
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                print("\n🛑 Test mode stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Agent Monitor")
    parser.add_argument("--url", default="http://localhost:8002", help="Agent URL")
    parser.add_argument("--mode", choices=["monitor", "test"], default="test", help="Monitor mode")
    parser.add_argument("--interval", type=int, default=10, help="Monitor interval (seconds)")
    
    args = parser.parse_args()
    
    monitor = EnhancedAgentMonitor(args.url)
    
    if args.mode == "monitor":
        monitor.monitor_continuous(args.interval)
    else:
        monitor.run_interactive_test()

if __name__ == "__main__":
    main()