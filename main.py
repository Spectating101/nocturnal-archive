"""
Simplified Nocturnal Archive FastAPI Application for Railway Deployment
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Nocturnal Archive API",
    description="AI-powered academic research platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nocturnal Archive API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nocturnal-archive"}

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Simplified chat endpoint for testing"""
    try:
        # Basic response for testing
        return {
            "response": "Nocturnal Archive is working! This is a test response.",
            "status": "success",
            "message": "Chat endpoint is functional"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify deployment"""
    return {
        "message": "Nocturnal Archive API is deployed successfully!",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "port": os.getenv("PORT", "8000")
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
