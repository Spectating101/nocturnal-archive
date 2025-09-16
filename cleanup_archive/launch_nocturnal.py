#!/usr/bin/env python3
"""
Nocturnal Archive - Launch System
Comprehensive research automation platform with citation tracking and consensus building
"""

import asyncio
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nocturnal_launch.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("nocturnal_launch")

class NocturnalLauncher:
    """Main launcher for Nocturnal Archive system"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.processes = []
        self.services = {
            "api_server": None,
            "chatbot_ui": None,
            "database": None,
            "redis": None
        }
        
    async def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("🔍 Checking system dependencies...")
        
        # Check Python packages
        required_packages = [
            "fastapi", "uvicorn", "pymongo", "redis", "aiohttp",
            "pandas", "numpy", "scikit-learn", "transformers"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
            logger.info("💡 Run: pip install -r requirements.txt")
            return False
        
        # Check Node.js for chatbot UI
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Node.js not found. Please install Node.js 18+")
                return False
            logger.info(f"✅ Node.js version: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("❌ Node.js not found. Please install Node.js 18+")
            return False
        
        # Check if chatbot-ui dependencies are installed
        chatbot_ui_dir = self.base_dir / "chatbot-ui"
        if not (chatbot_ui_dir / "node_modules").exists():
            logger.warning("⚠️  Chatbot UI dependencies not installed. Installing...")
            try:
                subprocess.run(["npm", "install"], cwd=chatbot_ui_dir, check=True)
                logger.info("✅ Chatbot UI dependencies installed")
            except subprocess.CalledProcessError:
                logger.error("❌ Failed to install chatbot UI dependencies")
                return False
        
        logger.info("✅ All dependencies checked")
        return True
    
    async def start_database_services(self) -> bool:
        """Start database services (MongoDB, Redis)"""
        logger.info("🗄️  Starting database services...")
        
        # Check if Docker is available
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("🐳 Docker detected - using docker-compose for databases")
                return await self._start_docker_services()
            else:
                logger.warning("⚠️  Docker not available - assuming local database services")
                return await self._check_local_services()
        except FileNotFoundError:
            logger.warning("⚠️  Docker not available - assuming local database services")
            return await self._check_local_services()
    
    async def _start_docker_services(self) -> bool:
        """Start services using docker-compose"""
        try:
            docker_compose_file = self.base_dir / "docker-compose.yml"
            if docker_compose_file.exists():
                logger.info("🚀 Starting services with docker-compose...")
                process = subprocess.Popen(
                    ["docker-compose", "up", "-d"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.processes.append(process)
                
                # Wait for services to start
                await asyncio.sleep(5)
                logger.info("✅ Docker services started")
                return True
            else:
                logger.error("❌ docker-compose.yml not found")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to start Docker services: {e}")
            return False
    
    async def _check_local_services(self) -> bool:
        """Check if local database services are running"""
        logger.info("🔍 Checking local database services...")
        
        # Check MongoDB
        try:
            import pymongo
            client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
            client.server_info()
            logger.info("✅ MongoDB is running")
        except Exception:
            logger.warning("⚠️  MongoDB not running - please start MongoDB service")
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
            r.ping()
            logger.info("✅ Redis is running")
        except Exception:
            logger.warning("⚠️  Redis not running - please start Redis service")
        
        return True
    
    async def start_api_server(self) -> bool:
        """Start the FastAPI server"""
        logger.info("🚀 Starting Nocturnal Archive API server...")
        
        try:
            # Start the API server
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], cwd=self.base_dir)
            
            self.processes.append(process)
            self.services["api_server"] = process
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test if server is running
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/docs") as response:
                        if response.status == 200:
                            logger.info("✅ API server started successfully")
                            return True
            except Exception:
                logger.warning("⚠️  API server may still be starting...")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")
            return False
    
    async def start_chatbot_ui(self) -> bool:
        """Start the chatbot UI"""
        logger.info("🎨 Starting Nocturnal Archive Chatbot UI...")
        
        try:
            chatbot_ui_dir = self.base_dir / "chatbot-ui"
            
            # Start the Next.js development server
            process = subprocess.Popen([
                "npm", "run", "dev"
            ], cwd=chatbot_ui_dir)
            
            self.processes.append(process)
            self.services["chatbot_ui"] = process
            
            # Wait for UI to start
            await asyncio.sleep(5)
            
            logger.info("✅ Chatbot UI started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Chatbot UI: {e}")
            return False
    
    async def open_browser(self):
        """Open browser to the application"""
        logger.info("🌐 Opening Nocturnal Archive in browser...")
        
        # Wait a bit more for services to fully start
        await asyncio.sleep(2)
        
        try:
            # Open the chatbot UI
            webbrowser.open("http://localhost:3000")
            logger.info("✅ Browser opened to http://localhost:3000")
            
            # Also open API docs
            webbrowser.open("http://localhost:8000/docs")
            logger.info("✅ API documentation opened at http://localhost:8000/docs")
            
        except Exception as e:
            logger.error(f"❌ Failed to open browser: {e}")
    
    async def show_system_status(self):
        """Show current system status"""
        logger.info("📊 Nocturnal Archive System Status")
        logger.info("=" * 50)
        
        # Check API server
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health") as response:
                    if response.status == 200:
                        logger.info("✅ API Server: Running (http://localhost:8000)")
                    else:
                        logger.warning("⚠️  API Server: Status unknown")
        except Exception:
            logger.warning("⚠️  API Server: Not responding")
        
        # Check Chatbot UI
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3000") as response:
                    if response.status == 200:
                        logger.info("✅ Chatbot UI: Running (http://localhost:3000)")
                    else:
                        logger.warning("⚠️  Chatbot UI: Status unknown")
        except Exception:
            logger.warning("⚠️  Chatbot UI: Not responding")
        
        logger.info("=" * 50)
    
    async def launch_system(self):
        """Launch the complete Nocturnal Archive system"""
        logger.info("🚀 Launching Nocturnal Archive Research Platform")
        logger.info("=" * 60)
        
        # Check dependencies
        if not await self.check_dependencies():
            logger.error("❌ Dependency check failed. Please install missing dependencies.")
            return
        
        # Start database services
        if not await self.start_database_services():
            logger.warning("⚠️  Database services may not be available")
        
        # Start API server
        if not await self.start_api_server():
            logger.error("❌ Failed to start API server")
            return
        
        # Start chatbot UI
        if not await self.start_chatbot_ui():
            logger.error("❌ Failed to start Chatbot UI")
            return
        
        # Show status
        await self.show_system_status()
        
        # Open browser
        await self.open_browser()
        
        logger.info("🎉 Nocturnal Archive launched successfully!")
        logger.info("")
        logger.info("📚 Available Features:")
        logger.info("   • Research paper analysis and synthesis")
        logger.info("   • Citation tracking and consensus building")
        logger.info("   • LLM-powered research assistance")
        logger.info("   • Academic export with proper formatting")
        logger.info("   • Interactive chatbot interface")
        logger.info("")
        logger.info("🌐 Access Points:")
        logger.info("   • Chatbot UI: http://localhost:3000")
        logger.info("   • API Documentation: http://localhost:8000/docs")
        logger.info("   • API Health Check: http://localhost:8000/health")
        logger.info("")
        logger.info("🛑 To stop the system, press Ctrl+C")
        
        try:
            # Keep the system running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down Nocturnal Archive...")
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("🛑 Shutting down services...")
        
        # Stop all processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                process.kill()
        
        # Stop Docker services if running
        try:
            subprocess.run(["docker-compose", "down"], cwd=self.base_dir, check=True)
            logger.info("✅ Docker services stopped")
        except Exception:
            pass
        
        logger.info("✅ Nocturnal Archive shutdown complete")

async def main():
    """Main entry point"""
    launcher = NocturnalLauncher()
    await launcher.launch_system()

if __name__ == "__main__":
    asyncio.run(main())
