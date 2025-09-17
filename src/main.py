#!/usr/bin/env python3
"""
Nocturnal Archive - Main FastAPI Application
Production deployment entry point
"""

import os
import logging
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import our services
from src.services.auth_service.auth_manager import auth_manager
from src.services.billing_service.subscription_manager import subscription_manager, SubscriptionTier
from src.services.analytics_service.usage_tracker import usage_tracker, UsageType
from src.services.research_service.enhanced_research import EnhancedResearchService
from src.services.research_service.chatbot import ChatbotResearchSession
from src.services.search_service.search_engine import SearchEngine
from src.services.paper_service.openalex import OpenAlexClient
from src.storage.db.operations import DatabaseOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nocturnal Archive API",
    description="Production-grade AI-powered research platform",
    version="2.0.0",
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

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ResearchRequest(BaseModel):
    topic: str
    max_results: Optional[int] = 10

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
        "service": "Nocturnal Archive",
        "version": "2.0.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-08-26T00:00:00Z"}

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "services": {
            "auth": "operational",
            "research": "operational",
            "billing": "operational",
            "analytics": "operational"
        }
    }

# Authentication endpoints
@app.post("/api/auth/signup")
async def signup(request: AuthRequest):
    """Create a new user account."""
    try:
        # Create user in Supabase
        user_data = await auth_manager.create_user(
            email=request.email,
            password=request.password,
            user_metadata={"source": "api"}
        )
        
        # Create Stripe customer
        customer_id = await subscription_manager.create_customer(
            email=request.email,
            name=user_data.get("user", {}).get("user_metadata", {}).get("name")
        )
        
        # Create free subscription
        subscription = await subscription_manager.create_subscription(
            customer_id=customer_id,
            tier=SubscriptionTier.FREE
        )
        
        return {
            "status": "success",
            "message": "Account created successfully",
            "user_id": user_data.get("user", {}).get("id"),
            "customer_id": customer_id,
            "subscription": subscription
        }
        
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.post("/api/auth/signin")
async def signin(request: AuthRequest):
    """Sign in user."""
    try:
        auth_response = await auth_manager.sign_in(
            email=request.email,
            password=request.password
        )
        
        return {
            "status": "success",
            "message": "Signed in successfully",
            "access_token": auth_response.get("access_token"),
            "refresh_token": auth_response.get("refresh_token"),
            "user": auth_response.get("user")
        }
        
    except Exception as e:
        logger.error(f"Signin failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    try:
        auth_response = await auth_manager.refresh_token(refresh_token)
        
        return {
            "status": "success",
            "access_token": auth_response.get("access_token"),
            "refresh_token": auth_response.get("refresh_token")
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# Subscription management endpoints
@app.post("/api/subscriptions/create")
async def create_subscription(request: SubscriptionRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Create or update user subscription."""
    try:
        user_id = current_user.get("id")
        
        # Get user's current subscription
        user_subscription = await auth_manager.get_user_subscription(user_id)
        
        if user_subscription:
            # Update existing subscription
            subscription = await subscription_manager.update_subscription(
                subscription_id=user_subscription.get("subscription_id"),
                tier=SubscriptionTier(request.tier)
            )
        else:
            # Create new subscription
            customer_id = await subscription_manager.create_customer(
                email=current_user.get("email")
            )
            subscription = await subscription_manager.create_subscription(
                customer_id=customer_id,
                tier=SubscriptionTier(request.tier),
                payment_method_id=request.payment_method_id
            )
        
        return {
            "status": "success",
            "subscription": subscription
        }
        
    except Exception as e:
        logger.error(f"Subscription creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Subscription creation failed: {str(e)}")

@app.get("/api/subscriptions/current")
async def get_current_subscription(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get user's current subscription."""
    try:
        user_id = current_user.get("id")
        subscription = await auth_manager.get_user_subscription(user_id)
        
        if subscription:
            subscription_details = await subscription_manager.get_subscription(
                subscription_id=subscription.get("subscription_id")
            )
            return {
                "status": "success",
                "subscription": subscription_details
            }
        else:
            return {
                "status": "success",
                "subscription": None
            }
            
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")

@app.post("/api/subscriptions/cancel")
async def cancel_subscription(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Cancel user subscription."""
    try:
        user_id = current_user.get("id")
        subscription = await auth_manager.get_user_subscription(user_id)
        
        if subscription:
            success = await subscription_manager.cancel_subscription(
                subscription_id=subscription.get("subscription_id")
            )
            
            return {
                "status": "success" if success else "failed",
                "message": "Subscription cancelled successfully" if success else "Failed to cancel subscription"
            }
        else:
            raise HTTPException(status_code=404, detail="No active subscription found")
            
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")

# Usage tracking endpoints
@app.post("/api/usage/track")
async def track_usage(request: UsageRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Track user usage."""
    try:
        user_id = current_user.get("id")
        
        # Track usage
        success = await usage_tracker.track_usage(
            user_id=user_id,
            usage_type=UsageType(request.usage_type),
            amount=request.amount,
            metadata=request.metadata
        )
        
        return {
            "status": "success" if success else "failed",
            "message": "Usage tracked successfully" if success else "Failed to track usage"
        }
        
    except Exception as e:
        logger.error(f"Failed to track usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track usage: {str(e)}")

@app.get("/api/usage/current")
async def get_current_usage(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get user's current usage statistics."""
    try:
        user_id = current_user.get("id")
        usage_data = await usage_tracker.get_user_usage(user_id=user_id)
        
        return {
            "status": "success",
            "usage": usage_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")

@app.get("/api/usage/report")
async def get_usage_report(month: Optional[str] = None, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get detailed usage report."""
    try:
        user_id = current_user.get("id")
        report = await usage_tracker.generate_usage_report(user_id=user_id, month=month)
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Failed to generate usage report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate usage report: {str(e)}")

# Enhanced research endpoints with authentication and usage tracking
@app.post("/api/research")
async def start_research(request: ResearchRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Start a research session using real academic databases with usage tracking."""
    try:
        user_id = current_user.get("id")
        
        # Check usage limits
        subscription = await auth_manager.get_user_subscription(user_id)
        subscription_tier = subscription.get("tier", "free") if subscription else "free"
        
        within_limits = await usage_tracker.check_usage_limit(
            user_id=user_id,
            usage_type=UsageType.SEARCH,
            subscription_tier=subscription_tier
        )
        
        if not within_limits:
            raise HTTPException(status_code=429, detail="Usage limit exceeded. Please upgrade your plan.")
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=user_id,
            usage_type=UsageType.SEARCH,
            amount=1,
            metadata={"topic": request.topic, "max_results": request.max_results}
        )
        
        # Initialize database operations
        db_ops = DatabaseOperations(
            os.environ.get('MONGODB_URL', os.environ.get('MONGO_URL', 'mongodb://localhost:27017/nocturnal_archive')),
            os.environ.get('REDIS_URL', 'redis://localhost:6379')
        )

        # Initialize search engine
        search_engine = SearchEngine(db_ops, os.environ.get('REDIS_URL', 'redis://localhost:6379'))

        # Get web search results
        web_results = await search_engine.web_search(request.topic, num_results=min(request.max_results, 5))

        # Get academic search results
        academic_results = []
        try:
            async with OpenAlexClient() as openalex:
                academic_data = await openalex.search_works(request.topic, per_page=min(request.max_results, 10))
                if academic_data and "results" in academic_data:
                    academic_results = academic_data["results"]
        except Exception as e:
            logger.warning(f"OpenAlex search failed: {e}")

        # Combine results
        combined_results = {
            "topic": request.topic,
            "web_results": web_results,
            "academic_results": academic_results,
            "total_results": len(web_results) + len(academic_results),
            "status": "completed"
        }

        return {
            "status": "success",
            "topic": request.topic,
            "results": combined_results,
            "usage_tracked": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/api/real-chat")
async def real_chat_endpoint(request: ChatRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Real chat endpoint with authentication and usage tracking."""
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
            metadata={"message_length": len(request.message)}
        )
        
        # Import here to avoid circular imports
        from src.services.llm_service.llm_manager import LLMManager
        from src.services.research_service.synthesizer import ResearchSynthesizer
        from src.services.research_service.context_manager import ResearchContextManager

        # Initialize components with proper error handling
        db_ops = None
        llm_manager = None
        synthesizer = None
        context_manager = None

        try:
            db_ops = DatabaseOperations(
                os.environ.get('MONGODB_URL', os.environ.get('MONGO_URL', 'mongodb://localhost:27017/nocturnal_archive')),
                os.environ.get('REDIS_URL', 'redis://localhost:6379')
            )
            llm_manager = LLMManager(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            synthesizer = ResearchSynthesizer(db_ops, llm_manager, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            context_manager = ResearchContextManager(db_ops, synthesizer, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise HTTPException(status_code=500, detail="System initialization failed")

        # Create session with real components
        session = ChatbotResearchSession(context_manager, synthesizer, db_ops)

        # Process the message with real research capabilities
        response = await session.chat_turn(request.message)

        return {
            "response": response,
            "session_id": request.session_id or "new_session",
            "timestamp": "2024-08-26T00:00:00Z",
            "mode": "real_research",
            "usage_tracked": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Real chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Legacy endpoints for backward compatibility
@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Legacy chat endpoint for backward compatibility."""
    try:
        data = await request.json()
        message = data.get("message", "")
        session_id = data.get("session_id", None)

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Import here to avoid circular imports
        from src.services.research_service.chatbot import ChatbotResearchSession
        from src.storage.db.operations import DatabaseOperations
        from src.services.llm_service.llm_manager import LLMManager
        from src.services.research_service.synthesizer import ResearchSynthesizer
        from src.services.research_service.context_manager import ResearchContextManager

        # Initialize components with proper error handling
        db_ops = None
        llm_manager = None
        synthesizer = None
        context_manager = None

        try:
            db_ops = DatabaseOperations(
                os.environ.get('MONGODB_URL', os.environ.get('MONGO_URL', 'mongodb://localhost:27017/nocturnal_archive')),
                os.environ.get('REDIS_URL', 'redis://localhost:6379')
            )
            llm_manager = LLMManager(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            synthesizer = ResearchSynthesizer(db_ops, llm_manager, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            context_manager = ResearchContextManager(db_ops, synthesizer, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise HTTPException(status_code=500, detail="System initialization failed")

        # Create session with real components
        session = ChatbotResearchSession(context_manager, synthesizer, db_ops)

        # Process the message with real research capabilities
        response = await session.chat_turn(message)

        return {
            "response": response,
            "session_id": session_id or "new_session",
            "timestamp": "2024-08-26T00:00:00Z",
            "mode": "real_research"
        }

    except Exception as e:
        logger.error(f"Real chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Admin endpoints (protected by admin role)
@app.get("/api/admin/analytics")
async def get_admin_analytics(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get system-wide analytics (admin only)."""
    try:
        # Check if user has admin permissions
        if not auth_manager.has_permission(current_user, "admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics = await usage_tracker.get_usage_analytics()
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get admin analytics: {str(e)}")

# Academic Research Endpoints
class AcademicResearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = {}
    sortBy: str = "relevance"
    maxResults: int = 50

class SynthesisRequest(BaseModel):
    papers: list
    synthesisType: str = "comprehensive"

@app.post("/api/academic-research")
async def academic_research(request: AcademicResearchRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Perform comprehensive academic research"""
    try:
        # Check usage limits
        if not await usage_tracker.check_usage_limit(current_user['id'], UsageType.RESEARCH_QUERY):
            raise HTTPException(status_code=429, detail="Usage limit exceeded")
        
        # Initialize enhanced research service
        enhanced_research = EnhancedResearchService()
        
        # Perform research
        results = await enhanced_research.perform_comprehensive_research(
            query=request.query,
            filters=request.filters,
            sort_by=request.sortBy,
            max_results=request.maxResults
        )
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=current_user['id'],
            usage_type=UsageType.RESEARCH_QUERY,
            metadata={"query": request.query, "results_count": len(results)}
        )
        
        return JSONResponse(content={"results": results})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Academic research failed: {e}")
        raise HTTPException(status_code=500, detail="Research failed")

@app.post("/api/synthesis")
async def generate_synthesis(request: SynthesisRequest, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Generate knowledge synthesis from selected papers"""
    try:
        # Check usage limits
        if not await usage_tracker.check_usage_limit(current_user['id'], UsageType.SYNTHESIS):
            raise HTTPException(status_code=429, detail="Usage limit exceeded")
        
        # Initialize enhanced research service
        enhanced_research = EnhancedResearchService()
        
        # Generate synthesis
        synthesis = await enhanced_research.generate_synthesis(
            papers=request.papers,
            synthesis_type=request.synthesisType
        )
        
        # Track usage
        await usage_tracker.track_usage(
            user_id=current_user['id'],
            usage_type=UsageType.SYNTHESIS,
            metadata={"papers_count": len(request.papers), "synthesis_type": request.synthesisType}
        )
        
        return JSONResponse(content=synthesis)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis generation failed: {e}")
        raise HTTPException(status_code=500, detail="Synthesis failed")

# Document Library Endpoints
@app.get("/api/documents")
async def get_documents(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get user's document library"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return empty list - the frontend will show sample data
        return JSONResponse(content={"documents": []})
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get documents")

@app.post("/api/documents/{document_id}/bookmark")
async def bookmark_document(document_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Bookmark/unbookmark a document"""
    try:
        # In a real implementation, this would update the database
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Failed to bookmark document: {e}")
        raise HTTPException(status_code=500, detail="Failed to bookmark document")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Delete a document from library"""
    try:
        # In a real implementation, this would delete from database
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

# Research History Endpoints
@app.get("/api/research/history")
async def get_research_history(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get user's research history"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return empty list - the frontend will show sample data
        return JSONResponse(content={"sessions": []})
    except Exception as e:
        logger.error(f"Failed to get research history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get research history")

@app.post("/api/research/history/{session_id}/bookmark")
async def bookmark_session(session_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Bookmark/unbookmark a research session"""
    try:
        # In a real implementation, this would update the database
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Failed to bookmark session: {e}")
        raise HTTPException(status_code=500, detail="Failed to bookmark session")

@app.delete("/api/research/history/{session_id}")
async def delete_session(session_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Delete a research session"""
    try:
        # In a real implementation, this would delete from database
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@app.post("/api/research/history/{session_id}/export")
async def export_session(session_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Export research session results"""
    try:
        # In a real implementation, this would generate and return a PDF
        # For now, return a placeholder response
        return JSONResponse(content={"message": "Export functionality coming soon"})
    except Exception as e:
        logger.error(f"Failed to export session: {e}")
        raise HTTPException(status_code=500, detail="Failed to export session")

# Knowledge Synthesis Endpoints
@app.get("/api/synthesis/projects")
async def get_synthesis_projects(current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Get user's synthesis projects"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return empty list - the frontend will show sample data
        return JSONResponse(content={"syntheses": []})
    except Exception as e:
        logger.error(f"Failed to get synthesis projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get synthesis projects")

@app.post("/api/synthesis/projects")
async def create_synthesis_project(request: dict, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Create a new synthesis project"""
    try:
        # In a real implementation, this would create in database
        synthesis = {
            "id": f"synthesis_{int(time.time())}",
            "title": request.get("title", "New Synthesis"),
            "description": request.get("description", ""),
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "status": "draft",
            "documents": [],
            "synthesis": {},
            "analytics": {},
            "tags": []
        }
        return JSONResponse(content={"synthesis": synthesis})
    except Exception as e:
        logger.error(f"Failed to create synthesis project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create synthesis project")

@app.delete("/api/synthesis/projects/{project_id}")
async def delete_synthesis_project(project_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Delete a synthesis project"""
    try:
        # In a real implementation, this would delete from database
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Failed to delete synthesis project: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete synthesis project")

@app.post("/api/synthesis/projects/{project_id}/export")
async def export_synthesis_project(project_id: str, current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)):
    """Export synthesis project"""
    try:
        # In a real implementation, this would generate and return a PDF
        # For now, return a placeholder response
        return JSONResponse(content={"message": "Export functionality coming soon"})
    except Exception as e:
        logger.error(f"Failed to export synthesis project: {e}")
        raise HTTPException(status_code=500, detail="Failed to export synthesis project")

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
    uvicorn.run(app, host="127.0.0.1", port=8002)
