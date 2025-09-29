#!/usr/bin/env python3
"""
Check FinSight data sources health and status
"""

import asyncio
import aiohttp
import yaml
import time
from pathlib import Path
from typing import Dict, List, Any
import structlog

logger = structlog.get_logger(__name__)

class SourceChecker:
    """Check health and status of FinSight data sources"""
    
    def __init__(self, sources_config_path: str = "config/sources.yaml"):
        self.sources_config_path = Path(sources_config_path)
        self.sources = []
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Nocturnal Archive Source Checker (contact@nocturnal.dev)",
                "Accept": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def load_sources(self):
        """Load sources configuration"""
        try:
            if not self.sources_config_path.exists():
                logger.error("Sources config file not found", path=self.sources_config_path)
                return
            
            with open(self.sources_config_path, 'r') as f:
                self.sources = yaml.safe_load(f)
            
            logger.info("Loaded sources configuration", count=len(self.sources))
            
        except Exception as e:
            logger.error("Failed to load sources config", error=str(e))
            raise
    
    async def check_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single source"""
        source_id = source.get("id", "unknown")
        status = source.get("status", "unknown")
        base_url = source.get("base_url", "")
        
        result = {
            "source_id": source_id,
            "status": status,
            "base_url": base_url,
            "jurisdiction": source.get("jurisdiction", ""),
            "authority": source.get("authority", ""),
            "type": source.get("type", ""),
            "health_check": {
                "status": "unknown",
                "latency_ms": None,
                "error": None
            },
            "rate_limit": {
                "rpm_soft": source.get("etiquette", {}).get("rpm_soft", 0),
                "backoff_on": source.get("etiquette", {}).get("backoff_on", [])
            }
        }
        
        # Skip health check for planned sources
        if status == "planned":
            result["health_check"]["status"] = "planned"
            return result
        
        # Skip health check for sources without base_url
        if not base_url:
            result["health_check"]["status"] = "no_url"
            return result
        
        try:
            start_time = time.time()
            
            # Simple health check - try to access base URL
            async with self.session.get(base_url) as response:
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result["health_check"]["status"] = "healthy"
                    result["health_check"]["latency_ms"] = round(latency_ms, 2)
                elif response.status in [403, 429]:
                    result["health_check"]["status"] = "rate_limited"
                    result["health_check"]["latency_ms"] = round(latency_ms, 2)
                    result["health_check"]["error"] = f"HTTP {response.status}"
                else:
                    result["health_check"]["status"] = "unhealthy"
                    result["health_check"]["latency_ms"] = round(latency_ms, 2)
                    result["health_check"]["error"] = f"HTTP {response.status}"
        
        except Exception as e:
            result["health_check"]["status"] = "unhealthy"
            result["health_check"]["error"] = str(e)
        
        return result
    
    async def check_all_sources(self) -> List[Dict[str, Any]]:
        """Check health of all sources"""
        if not self.sources:
            self.load_sources()
        
        results = []
        
        for source in self.sources:
            result = await self.check_source(source)
            results.append(result)
            
            # Small delay between checks to be polite
            await asyncio.sleep(0.1)
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]]):
        """Print formatted results"""
        print("🔍 FinSight Data Sources Health Check")
        print("=" * 50)
        print()
        
        # Group by status
        by_status = {}
        for result in results:
            status = result["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
        
        # Print by status
        for status in ["ready", "planned", "blocked"]:
            if status not in by_status:
                continue
            
            status_emoji = {
                "ready": "✅",
                "planned": "📋", 
                "blocked": "🚫"
            }
            
            print(f"{status_emoji[status]} {status.upper()} ({len(by_status[status])} sources)")
            print("-" * 30)
            
            for result in by_status[status]:
                source_id = result["source_id"]
                jurisdiction = result["jurisdiction"]
                authority = result["authority"]
                source_type = result["type"]
                
                print(f"  {source_id}")
                print(f"    Jurisdiction: {jurisdiction}")
                print(f"    Authority: {authority}")
                print(f"    Type: {source_type}")
                
                if status == "ready":
                    health = result["health_check"]
                    health_status = health["status"]
                    
                    if health_status == "healthy":
                        latency = health["latency_ms"]
                        print(f"    Health: ✅ Healthy ({latency}ms)")
                    elif health_status == "rate_limited":
                        print(f"    Health: ⚠️  Rate Limited")
                    elif health_status == "unhealthy":
                        error = health["error"]
                        print(f"    Health: ❌ Unhealthy ({error})")
                    else:
                        print(f"    Health: ❓ {health_status}")
                    
                    # Rate limit info
                    rpm = result["rate_limit"]["rpm_soft"]
                    if rpm > 0:
                        print(f"    Rate Limit: {rpm} req/min")
                
                print()
        
        # Summary
        total_sources = len(results)
        ready_sources = len([r for r in results if r["status"] == "ready"])
        healthy_sources = len([r for r in results if r["status"] == "ready" and r["health_check"]["status"] == "healthy"])
        
        print("📊 Summary")
        print("-" * 20)
        print(f"Total sources: {total_sources}")
        print(f"Ready sources: {ready_sources}")
        print(f"Healthy sources: {healthy_sources}")
        print(f"Health rate: {(healthy_sources/ready_sources*100):.1f}%" if ready_sources > 0 else "Health rate: N/A")
        print()
        
        # Recommendations
        print("💡 Recommendations")
        print("-" * 20)
        
        if healthy_sources < ready_sources:
            print("  - Some sources are unhealthy, check network connectivity")
            print("  - Verify API keys and authentication for sources that require them")
        
        planned_sources = len([r for r in results if r["status"] == "planned"])
        if planned_sources > 0:
            print(f"  - {planned_sources} sources are planned for future implementation")
            print("  - Consider implementing high-priority sources first")
        
        print("  - Monitor rate limits and implement backoff strategies")
        print("  - Set up alerts for source health degradation")

async def main():
    """Main function"""
    async with SourceChecker() as checker:
        results = await checker.check_all_sources()
        checker.print_results(results)

if __name__ == "__main__":
    asyncio.run(main())

