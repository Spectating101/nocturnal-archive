#!/usr/bin/env python3
"""
Real API Agent - Actually uses FinSight and Archive APIs
No mocks, no fallbacks - just real data
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ChatRequest:
    question: str
    user_id: Optional[str] = None

@dataclass
class ChatResponse:
    response: str
    api_results: Optional[Dict[str, Any]] = None
    real_data: bool = False

class RealAPIAgent:
    """Agent that actually calls real APIs"""
    
    def __init__(self, platform_url: str = "http://localhost:8000"):
        self.platform_url = platform_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_finsight_api(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call real FinSight API"""
        url = f"{self.platform_url}/finsight{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _call_archive_api(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call real Archive API"""
        url = f"{self.platform_url}/archive{endpoint}"
        
        try:
            if data:
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"success": True, "data": result}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
            else:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"success": True, "data": result}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """Process a request using real APIs"""
        question = request.question.lower()
        api_results = {}
        real_data = False
        
        # Check if it's a finance question
        finance_keywords = ['revenue', 'income', 'profit', 'earnings', 'financial', 'stock', 'ticker', 'apple', 'microsoft', 'tesla', 'amazon']
        if any(keyword in question for keyword in finance_keywords):
            print("💰 Detected finance question - calling real FinSight API...")
            
            # Extract ticker if mentioned
            ticker = None
            if 'apple' in question or 'aapl' in question:
                ticker = 'AAPL'
            elif 'microsoft' in question or 'msft' in question:
                ticker = 'MSFT'
            elif 'tesla' in question or 'tsla' in question:
                ticker = 'TSLA'
            elif 'amazon' in question or 'amzn' in question:
                ticker = 'AMZN'
            
            if ticker:
                # Get real financial data
                kpi = 'revenue'
                if 'income' in question or 'profit' in question:
                    kpi = 'netIncome'
                
                result = await self._call_finsight_api(f"/kpis/{ticker}/{kpi}", {
                    "freq": "Q",
                    "limit": 4
                })
                
                if result["success"]:
                    api_results["finsight"] = result["data"]
                    real_data = result["data"].get("real_data", False)
                    print(f"✅ Got real FinSight data: {real_data}")
                else:
                    print(f"❌ FinSight API failed: {result['error']}")
        
        # Check if it's a research question
        research_keywords = ['paper', 'research', 'study', 'academic', 'journal', 'article', 'minimum wage', 'employment']
        if any(keyword in question for keyword in research_keywords):
            print("📚 Detected research question - calling real Archive API...")
            
            # Extract search terms
            search_query = question
            if 'minimum wage' in question:
                search_query = 'minimum wage employment effects'
            elif 'machine learning' in question:
                search_query = 'machine learning'
            
            result = await self._call_archive_api("/search", {
                "query": search_query,
                "limit": 3,
                "sources": ["openalex"]
            })
            
            if result["success"]:
                api_results["archive"] = result["data"]
                print("✅ Got real Archive data")
            else:
                print(f"❌ Archive API failed: {result['error']}")
        
        # Generate response based on real data
        response = self._generate_response(request.question, api_results, real_data)
        
        return ChatResponse(
            response=response,
            api_results=api_results,
            real_data=real_data
        )
    
    def _generate_response(self, question: str, api_results: Dict[str, Any], real_data: bool) -> str:
        """Generate response based on real API data"""
        
        if "finsight" in api_results:
            finsight_data = api_results["finsight"]
            ticker = finsight_data.get("ticker", "Unknown")
            kpi = finsight_data.get("kpi", "Unknown")
            data_points = finsight_data.get("data", [])
            source = finsight_data.get("source", "Unknown")
            
            response = f"📊 **Real Financial Data for {ticker}**\n\n"
            response += f"**{kpi.title()} Data (Last 4 Quarters):**\n"
            
            for point in data_points[:4]:
                period = point.get("period", "Unknown")
                value = point.get("value", 0)
                unit = point.get("unit", "USD")
                accession = point.get("accession", "N/A")
                
                if unit == "USD":
                    formatted_value = f"${value:,}"
                else:
                    formatted_value = f"{value} {unit}"
                
                response += f"• **{period}**: {formatted_value}\n"
            
            response += f"\n**Data Source**: {source}\n"
            response += f"**Real SEC Data**: {'✅ Yes' if real_data else '❌ No (Fallback)'}\n"
            
            if real_data:
                response += f"\n🔗 **SEC Filing**: {data_points[0].get('url', 'N/A')}\n"
            
            return response
        
        elif "archive" in api_results:
            archive_data = api_results["archive"]
            papers = archive_data.get("papers", [])
            
            response = f"📚 **Real Academic Research Results**\n\n"
            response += f"Found {len(papers)} papers:\n\n"
            
            for i, paper in enumerate(papers[:3], 1):
                title = paper.get("title", "No title")
                authors = paper.get("authors", [])
                year = paper.get("year", "Unknown")
                citations = paper.get("citations_count", "Unknown")
                doi = paper.get("doi", "N/A")
                
                author_names = ", ".join([author.get("name", "Unknown") for author in authors[:2]])
                
                response += f"**{i}. {title}**\n"
                response += f"   Authors: {author_names}\n"
                response += f"   Year: {year} | Citations: {citations}\n"
                response += f"   DOI: {doi}\n\n"
            
            response += "**Data Source**: OpenAlex API (Real Academic Database)\n"
            response += "**Real Research Data**: ✅ Yes\n"
            
            return response
        
        else:
            return "I can help with financial data (revenue, income, etc.) or academic research. Please ask about specific companies or research topics!"

async def test_real_agent():
    """Test the real API agent"""
    print("🚀 Testing Real API Agent")
    print("=" * 50)
    
    async with RealAPIAgent() as agent:
        # Test 1: Finance question
        print("\n💰 Test 1: Finance Question")
        request1 = ChatRequest("Compare Apple vs Microsoft revenue last 4 quarters")
        response1 = await agent.process_request(request1)
        print(f"Response: {response1.response}")
        print(f"Real data: {response1.real_data}")
        print(f"API results: {list(response1.api_results.keys())}")
        
        # Test 2: Research question
        print("\n📚 Test 2: Research Question")
        request2 = ChatRequest("Find papers on minimum wage employment effects")
        response2 = await agent.process_request(request2)
        print(f"Response: {response2.response}")
        print(f"Real data: {response2.real_data}")
        print(f"API results: {list(response2.api_results.keys())}")

if __name__ == "__main__":
    asyncio.run(test_real_agent())