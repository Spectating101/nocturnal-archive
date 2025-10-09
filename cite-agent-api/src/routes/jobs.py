"""
Job management API routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.jobs.queue import enqueue_synthesis, get_job_status, cancel_job, init_job_queue

router = APIRouter(prefix="/v1/api/jobs", tags=["Jobs"])

class JobRequest(BaseModel):
    context: Dict[str, Any]
    claims: list
    max_words: int = 400
    style: str = "markdown"

@router.post("/synthesis")
async def create_synthesis_job(req: JobRequest):
    """
    Create a new synthesis job (async)
    
    Returns 202 with job ID for polling
    """
    try:
        payload = {
            "context": req.context,
            "claims": req.claims,
            "max_words": req.max_words,
            "style": req.style
        }
        
        job_id = enqueue_synthesis(payload)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Synthesis job created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.get("/{job_id}")
async def get_job(job_id: str):
    """
    Get job status and result
    
    Returns job status: queued, started, finished, failed, not_found
    """
    try:
        status = get_job_status(job_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.delete("/{job_id}")
async def cancel_job_endpoint(job_id: str):
    """
    Cancel a queued job
    """
    try:
        cancelled = cancel_job(job_id)
        
        if cancelled:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled (already started or not found)")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")

@router.get("/")
async def list_jobs(limit: int = Query(10, ge=1, le=100)):
    """
    List recent jobs (placeholder - would need job storage)
    """
    return {
        "message": "Job listing not implemented yet",
        "limit": limit
    }
