# scripts/test_llm_integration.py

import asyncio
import json
import os
import sys
import logging

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm_service.model_dispatcher import ModelDispatcher
from src.services.llm_service.llm_manager import LLMManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test document
TEST_DOCUMENT = {
    "id": "test-doc-001",
    "title": "Test Document: PET Plastic Recycling for 3D Printing",
    "content": """
    Abstract:
    This study investigates the feasibility of recycling post-consumer PET bottles into 3D printing filament. 
    We examined various processing parameters including extrusion temperature (230-270°C), cooling rate, 
    and the addition of virgin material (0-30%) to optimize filament quality. Results indicate that a 
    temperature of 255°C with 20% virgin PET addition produces filament with tensile strength comparable 
    to commercial products (48.5 MPa). Challenges identified include moisture sensitivity, diameter 
    consistency, and potential contamination from additives. Our process achieves a 75% reduction in 
    carbon footprint compared to virgin PET filament production.
    
    Introduction:
    Plastic waste represents a growing environmental challenge, with only 9% of all plastic waste being 
    recycled globally. 3D printing offers a promising avenue for plastic reuse, particularly for high-value 
    applications. PET (Polyethylene terephthalate) is among the most commonly used plastics, with billions 
    of bottles produced annually. This research focuses on developing an economical and environmentally 
    sustainable process to convert waste PET bottles into high-quality 3D printing filament.
    
    Methodology:
    Post-consumer PET bottles were collected, cleaned, and shredded into 3-5mm flakes. The flakes were 
    dried at 105°C for 4 hours to reduce moisture content below 0.005% w/w. Extrusion was performed using 
    a twin-screw extruder with a temperature gradient of 230-270°C across five zones. Virgin PET was added 
    in proportions of 0%, 10%, 20%, and 30% to improve mechanical properties. The extruded filament was 
    cooled using a water bath maintained at 25°C, followed by air drying. Filament diameter was controlled 
    to 1.75±0.05mm using a precision winding system with laser diameter monitoring.
    
    Results:
    Extrusion temperature significantly affected filament quality. Temperatures below 240°C resulted in 
    incomplete melting, while temperatures above 265°C led to material degradation and discoloration. 
    Optimal extrusion was achieved at 255°C. The addition of virgin PET improved mechanical properties, 
    with 20% addition providing the best balance between recycled content and performance. Tensile testing 
    showed that filament with 20% virgin PET achieved a tensile strength of 48.5±2.3 MPa, comparable to 
    commercial PET filament (50-55 MPa). DSC analysis revealed that recycled PET had lower crystallinity 
    (23.8%) compared to virgin PET (31.5%), affecting printing temperature requirements.
    
    Limitations:
    The process is sensitive to contamination from labels, adhesives, and other additives present in 
    post-consumer bottles. Moisture absorption remains a challenge, requiring proper storage and drying 
    before printing. Batch-to-batch variation in source materials affects consistency. Long-term durability 
    of printed objects may be compromised due to polymer chain degradation during the recycling process.
    
    Conclusion:
    This study demonstrates the technical feasibility of converting waste PET bottles into functional 3D 
    printing filament. The addition of virgin material improves quality while maintaining a significant 
    recycled content. Further research is needed to address contamination and moisture sensitivity issues. 
    Life cycle assessment shows that recycled PET filament production reduces energy consumption by 68% 
    and CO2 emissions by 75% compared to virgin filament production. Future work should focus on improving 
    the filtration process and investigating additives to enhance moisture resistance.
    """
}

async def test_model_dispatcher():
    """Test the model dispatcher with a sample document."""
    logger.info("Testing ModelDispatcher...")
    
    dispatcher = ModelDispatcher()
    
    # Check enabled services
    logger.info(f"Enabled services: {dispatcher.service_priorities}")
    
    if not dispatcher.clients:
        logger.error("No LLM clients enabled. Check your API keys and configuration.")
        return False
        
    try:
        # Process test document
        logger.info("Processing test document...")
        result = await dispatcher.dispatch_document(TEST_DOCUMENT)
        
        # Print result
        logger.info("Processing result:")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        logger.error(f"Error testing model dispatcher: {str(e)}")
        return False

async def test_llm_manager():
    """Test the LLM manager with Redis."""
    logger.info("Testing LLMManager...")
    
    # Use a test Redis URL - update this as needed
    redis_url = "redis://localhost:6379/0"
    
    manager = LLMManager(redis_url)
    
    try:
        # Process document directly (without queue)
        logger.info("Processing test document directly...")
        result = await manager.process_document(TEST_DOCUMENT)
        
        # Print result
        logger.info("Processing result:")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        logger.error(f"Error testing LLM manager: {str(e)}")
        return False

async def main():
    """Run test functions."""
    # Test model dispatcher first
    dispatcher_success = await test_model_dispatcher()
    
    if dispatcher_success:
        logger.info("ModelDispatcher test passed!")
    else:
        logger.error("ModelDispatcher test failed!")
        return
    
    # Only test LLM manager if Redis is available
    try:
        import redis
        redis.Redis(host='localhost', port=6379, db=0).ping()
        
        # Test LLM manager
        manager_success = await test_llm_manager()
        
        if manager_success:
            logger.info("LLMManager test passed!")
        else:
            logger.error("LLMManager test failed!")
    except Exception:
        logger.warning("Redis not available, skipping LLMManager test")

if __name__ == "__main__":
    asyncio.run(main())