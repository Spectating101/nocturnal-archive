"""
Nocturnal Archive - Production-ready AI Research Assistant

A sophisticated research assistant with access to real financial data (SEC EDGAR)
and academic research (OpenAlex, PubMed) through natural conversation.
"""

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest, ChatResponse

__version__ = "1.0.0"
__author__ = "Nocturnal Archive Team"
__email__ = "contact@nocturnal.dev"

__all__ = [
    "EnhancedNocturnalAgent",
    "ChatRequest", 
    "ChatResponse"
]

# Package metadata
PACKAGE_NAME = "nocturnal-archive"
PACKAGE_VERSION = __version__
PACKAGE_DESCRIPTION = "Production-ready AI Research Assistant with real data integration"
PACKAGE_URL = "https://github.com/Spectating101/nocturnal-archive"

def get_version():
    """Get the package version"""
    return __version__

def quick_start():
    """Print quick start instructions"""
    print("""
🚀 Nocturnal Archive Quick Start
================================

1. Install the package:
   pip install nocturnal-archive

2. Get your API keys:
   - Groq API: https://console.groq.com/keys
   - Archive API: Included (uses public academic sources)

3. Create your first agent:
   ```python
   import asyncio
   from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest
   
   async def main():
       agent = EnhancedNocturnalAgent()
       await agent.initialize()
       
       request = ChatRequest(
           question="Find papers on machine learning and get Apple revenue data",
           user_id="user123",
           conversation_id="conv1"
       )
       
       response = await agent.process_request(request)
       print(response.response)
       
       await agent.close()
   
   asyncio.run(main())
   ```

4. For more examples, visit: https://github.com/Spectating101/nocturnal-archive
""")

if __name__ == "__main__":
    quick_start()
