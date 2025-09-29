"""
Assistant routes for R/SQL programming help
Simplified version of the R/SQL Assistant integrated into unified platform
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import structlog
from datetime import datetime

from config.settings import Settings, get_settings
from services.groq_service import get_groq_service

logger = structlog.get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat assistance"""
    question: str
    context: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.5
    max_tokens: int = 1200
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat assistance"""
    answer: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    timestamp: str
    user_id: Optional[str] = None


class CodeExampleRequest(BaseModel):
    """Request model for code examples"""
    language: str  # "r" or "sql"
    task: str
    context: Optional[str] = None
    user_id: Optional[str] = None


class CodeExampleResponse(BaseModel):
    """Response model for code examples"""
    code: str
    explanation: str
    language: str
    task: str
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat_assistance(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
) -> ChatResponse:
    """Get R/SQL programming assistance"""
    
    if not settings.assistant_enabled:
        raise HTTPException(status_code=503, detail="Assistant module is disabled")
    
    groq_service = get_groq_service()
    
    try:
        # Get assistance from Groq
        response = await groq_service.r_sql_assistance(
            question=request.question,
            context=request.context or "",
            user_id=request.user_id
        )
        
        return ChatResponse(
            answer=response["content"],
            model=response["model"],
            usage=response.get("usage"),
            timestamp=response["timestamp"],
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Chat assistance failed: {e}")
        raise HTTPException(status_code=500, detail="Chat assistance failed")


@router.get("/chat")
async def chat_assistance_get(
    question: str = Query(..., description="Your question about R or SQL"),
    context: Optional[str] = Query(None, description="Additional context"),
    model: Optional[str] = Query(None, description="Model to use"),
    temperature: float = Query(0.5, description="Temperature for response"),
    max_tokens: int = Query(1200, description="Maximum tokens"),
    user_id: Optional[str] = Query(None, description="User ID"),
    settings: Settings = Depends(get_settings)
) -> ChatResponse:
    """Get R/SQL programming assistance via GET request"""
    
    request = ChatRequest(
        question=question,
        context=context,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id
    )
    
    return await chat_assistance(request, settings)


@router.post("/code-example", response_model=CodeExampleResponse)
async def get_code_example(
    request: CodeExampleRequest,
    settings: Settings = Depends(get_settings)
) -> CodeExampleResponse:
    """Get code example for R or SQL"""
    
    if not settings.assistant_enabled:
        raise HTTPException(status_code=503, detail="Assistant module is disabled")
    
    if request.language.lower() not in ["r", "sql"]:
        raise HTTPException(status_code=400, detail="Language must be 'r' or 'sql'")
    
    groq_service = get_groq_service()
    
    # Create specialized prompt for code examples
    system_prompt = f"""You are a {request.language.upper()} programming expert. Provide a clear code example for the requested task.

    For {request.language.upper()} code:
    - Provide complete, runnable code
    - Include comments explaining key parts
    - Use best practices and modern syntax
    - Include example data if helpful
    
    Format your response as:
    CODE:
    [your code here]
    
    EXPLANATION:
    [explanation of what the code does and how it works]"""
    
    user_prompt = f"Task: {request.task}"
    if request.context:
        user_prompt += f"\nContext: {request.context}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await groq_service.chat_completion(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=1500,
            user_id=request.user_id
        )
        
        content = response["content"]
        
        # Parse code and explanation
        code = ""
        explanation = ""
        
        if "CODE:" in content and "EXPLANATION:" in content:
            parts = content.split("EXPLANATION:")
            code_part = parts[0].replace("CODE:", "").strip()
            explanation_part = parts[1].strip()
            
            code = code_part
            explanation = explanation_part
        else:
            # Fallback: use entire content as explanation
            explanation = content
            code = "See explanation for code details"
        
        return CodeExampleResponse(
            code=code,
            explanation=explanation,
            language=request.language.upper(),
            task=request.task,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Code example generation failed: {e}")
        raise HTTPException(status_code=500, detail="Code example generation failed")


@router.get("/r-example")
async def get_r_example(
    task: str = Query(..., description="R programming task"),
    context: Optional[str] = Query(None, description="Additional context"),
    user_id: Optional[str] = Query(None, description="User ID"),
    settings: Settings = Depends(get_settings)
) -> CodeExampleResponse:
    """Get R code example"""
    
    request = CodeExampleRequest(
        language="r",
        task=task,
        context=context,
        user_id=user_id
    )
    
    return await get_code_example(request, settings)


@router.get("/sql-example")
async def get_sql_example(
    task: str = Query(..., description="SQL task"),
    context: Optional[str] = Query(None, description="Additional context"),
    user_id: Optional[str] = Query(None, description="User ID"),
    settings: Settings = Depends(get_settings)
) -> CodeExampleResponse:
    """Get SQL code example"""
    
    request = CodeExampleRequest(
        language="sql",
        task=task,
        context=context,
        user_id=user_id
    )
    
    return await get_code_example(request, settings)


@router.get("/status")
async def assistant_status(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get assistant module status"""
    
    groq_service = get_groq_service()
    groq_status = groq_service.get_status()
    
    return {
        "module": "assistant",
        "enabled": settings.assistant_enabled,
        "status": "healthy" if settings.assistant_enabled else "disabled",
        "groq_service": {
            "healthy_keys": groq_status["healthy_keys"],
            "total_keys": groq_status["total_keys"]
        },
        "endpoints": [
            "POST /api/v1/assistant/chat",
            "GET /api/v1/assistant/chat",
            "POST /api/v1/assistant/code-example",
            "GET /api/v1/assistant/r-example",
            "GET /api/v1/assistant/sql-example"
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/help")
async def assistant_help() -> Dict[str, Any]:
    """Get assistant help and examples"""
    
    return {
        "module": "assistant",
        "description": "R and SQL programming assistance",
        "features": [
            "Chat-based R/SQL help",
            "Code examples with explanations",
            "Best practices guidance",
            "Interactive assistance"
        ],
        "examples": {
            "chat": {
                "endpoint": "POST /api/v1/assistant/chat",
                "example": {
                    "question": "How do I create a scatter plot in R?",
                    "context": "I have data with x and y variables"
                }
            },
            "r_example": {
                "endpoint": "GET /api/v1/assistant/r-example",
                "example": {
                    "task": "Create a scatter plot with ggplot2",
                    "context": "Data has columns 'x' and 'y'"
                }
            },
            "sql_example": {
                "endpoint": "GET /api/v1/assistant/sql-example",
                "example": {
                    "task": "Join two tables and filter results",
                    "context": "Tables: users and orders"
                }
            }
        },
        "supported_languages": ["R", "SQL"],
        "timestamp": datetime.now().isoformat()
    }
