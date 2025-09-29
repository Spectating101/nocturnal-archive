"""
Enhanced Main Application - Integrated with all new capabilities
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import existing services
from src.services.auth_service.auth_manager import auth_manager
from src.services.billing_service.subscription_manager import subscription_manager, SubscriptionTier
from src.services.analytics_service.usage_tracker import usage_tracker, UsageType
from src.services.research_service.enhanced_research import EnhancedResearchService
from src.services.research_service.chatbot import ChatbotResearchSession
from src.services.search_service.search_engine import SearchEngine
from src.services.paper_service.openalex import OpenAlexClient
from src.storage.db.operations import DatabaseOperations

# Import new enhanced capabilities
from src.services.reasoning_engine.reasoning_engine import ReasoningEngine
from src.services.tool_framework.tool_manager import ToolManager
from src.services.context_manager.advanced_context import AdvancedContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nocturnal Archive API - Enhanced",
    description="Production-grade AI-powered research platform with advanced reasoning capabilities",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced services
tool_manager = ToolManager()
context_manager = AdvancedContextManager()
reasoning_engine = ReasoningEngine()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_advanced_reasoning: Optional[bool] = True

class ResearchRequest(BaseModel):
    topic: str
    max_results: Optional[int] = 10
    use_advanced_reasoning: Optional[bool] = True

class ReasoningRequest(BaseModel):
    problem_description: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class ToolExecutionRequest(BaseModel):
    tool_name: Optional[str] = None
    task_description: str
    context: Optional[Dict[str, Any]] = None
    auto_select_tool: Optional[bool] = True

class AuthRequest(BaseModel):
    email: str
    password: str

class SubscriptionRequest(BaseModel):
    tier: str
    payment_method_id: Optional[str] = None

class UsageRequest(BaseModel):
    usage_type: str
    amount: int = 1
    metadata: Optional[Dict[str, Any]] = None

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Nocturnal Archive API - Enhanced",
        "version": "3.0.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "capabilities": [
            "Advanced Reasoning Engine",
            "Dynamic Tool Framework", 
            "Code Execution Environment",
            "Advanced Context Management",
            "Academic Research & Synthesis",
            "Multi-LLM Integration"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "reasoning_engine": "operational",
            "tool_framework": "operational",
            "context_manager": "operational",
            "research_service": "operational"
        }
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "services": {
            "auth": "operational",
            "research": "operational",
            "reasoning": "operational",
            "tools": "operational",
            "context": "operational",
            "billing": "operational",
            "analytics": "operational"
        }
    }

# Enhanced Reasoning Endpoints
@app.post("/api/reasoning/solve")
async def solve_problem(request: ReasoningRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Solve complex problems using advanced reasoning."""
    try:
        user_id = current_user.get("id")
        
        # Check usage limits
        subscription = await auth_manager.get_user_subscription(user_id)
        subscription_tier = subscription.get("tier", "free") if subscription else "free"
        
        within_limits = await usage_tracker.check_usage_limit(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            subscription_tier=subscription_tier
        )
        
        if not within_limits:
            raise HTTPException(status_code=429, detail="Usage limit exceeded. Please upgrade your plan.")
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            amount=1,
            metadata={"problem": request.problem_description, "reasoning": True}
        )
        
        # Solve the problem using reasoning engine
        result = await reasoning_engine.solve_problem(
            problem_description=request.problem_description,
            context=request.context,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "result": result,
            "usage_tracked": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reasoning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")

@app.get("/api/reasoning/session/{session_id}")
async def get_reasoning_session(session_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get status of a reasoning session."""
    try:
        status = await reasoning_engine.get_session_status(session_id)
        return {
            "status": "success",
            "session_status": status
        }
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

# Enhanced Tool Framework Endpoints
@app.post("/api/tools/execute")
async def execute_tool(request: ToolExecutionRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Execute a tool with dynamic selection."""
    try:
        user_id = current_user.get("id")
        
        # Check usage limits
        subscription = await auth_manager.get_user_subscription(user_id)
        subscription_tier = subscription.get("tier", "free") if subscription else "free"
        
        within_limits = await usage_tracker.check_usage_limit(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            subscription_tier=subscription_tier
        )
        
        if not within_limits:
            raise HTTPException(status_code=429, detail="Usage limit exceeded. Please upgrade your plan.")
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            amount=1,
            metadata={"tool_execution": True, "task": request.task_description}
        )
        
        # Execute tool
        if request.auto_select_tool:
            result = await tool_manager.execute_with_auto_selection(
                task_description=request.task_description,
                context=request.context
            )
        else:
            if not request.tool_name:
                raise HTTPException(status_code=400, detail="Tool name required when auto_select_tool is False")
            
            result = await tool_manager.execute_tool(
                tool_name=request.tool_name,
                task_description=request.task_description,
                context=request.context
            )
        
        return {
            "status": "success",
            "result": result,
            "usage_tracked": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.get("/api/tools/available")
async def get_available_tools(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get list of available tools."""
    try:
        tools = tool_manager.get_available_tools()
        tool_capabilities = {}
        
        for tool in tools:
            tool_capabilities[tool] = tool_manager.get_tool_capabilities(tool)
        
        return {
            "status": "success",
            "tools": tools,
            "capabilities": tool_capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get available tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available tools: {str(e)}")

@app.get("/api/tools/performance")
async def get_tool_performance(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get tool performance statistics."""
    try:
        tools = tool_manager.get_available_tools()
        performance_stats = {}
        
        for tool in tools:
            performance_stats[tool] = tool_manager.get_tool_performance_stats(tool)
        
        return {
            "status": "success",
            "performance_stats": performance_stats
        }
    except Exception as e:
        logger.error(f"Failed to get tool performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool performance: {str(e)}")

# Enhanced Context Management Endpoints
@app.post("/api/context/process")
async def process_context(request: ChatRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Process interaction and update context."""
    try:
        user_id = current_user.get("id")
        session_id = request.session_id or "default_session"
        
        # Generate response (this would integrate with existing chat logic)
        response = f"Enhanced response to: {request.message}"
        
        # Process interaction in context manager
        result = await context_manager.process_interaction(
            user_input=request.message,
            response=response,
            session_id=session_id,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "response": response,
            "context_result": result
        }
        
    except Exception as e:
        logger.error(f"Context processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context processing failed: {str(e)}")

@app.get("/api/context/retrieve")
async def retrieve_context(query: str, session_id: Optional[str] = None, 
                         current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Retrieve relevant context for a query."""
    try:
        user_id = current_user.get("id")
        
        result = await context_manager.retrieve_relevant_context(
            query=query,
            session_id=session_id,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")

@app.get("/api/context/session/{session_id}")
async def get_session_context(session_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get current session context."""
    try:
        result = await context_manager.get_session_context(session_id)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to get session context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session context: {str(e)}")

# Enhanced Chat Endpoint with Advanced Reasoning
@app.post("/api/enhanced-chat")
async def enhanced_chat_endpoint(request: ChatRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Enhanced chat endpoint with advanced reasoning capabilities."""
    try:
        user_id = current_user.get("id")
        session_id = request.session_id or "enhanced_session"
        
        # Check usage limits
        subscription = await auth_manager.get_user_subscription(user_id)
        subscription_tier = subscription.get("tier", "free") if subscription else "free"
        
        within_limits = await usage_tracker.check_usage_limit(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            subscription_tier=subscription_tier
        )
        
        if not within_limits:
            raise HTTPException(status_code=429, detail="Usage limit exceeded. Please upgrade your plan.")
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=user_id,
            usage_type=UsageType.API_CALL,
            amount=1,
            metadata={"message_length": len(request.message), "enhanced": True}
        )
        
        # Use advanced reasoning if requested
        if request.use_advanced_reasoning:
            # Solve as a reasoning problem
            reasoning_result = await reasoning_engine.solve_problem(
                problem_description=request.message,
                context={"session_id": session_id, "user_id": user_id},
                user_id=user_id
            )
            
            response = reasoning_result.get("solution", "No solution generated")
        else:
            # Use existing chat logic
            response = f"Standard response to: {request.message}"
        
        # Process interaction in context manager
        await context_manager.process_interaction(
            user_input=request.message,
            response=str(response),
            session_id=session_id,
            user_id=user_id
        )
        
        return {
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "enhanced_reasoning" if request.use_advanced_reasoning else "standard",
            "usage_tracked": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Keep all existing endpoints for backward compatibility
# (All the original endpoints from the main.py file would be included here)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
