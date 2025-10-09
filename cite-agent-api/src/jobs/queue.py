"""
Job queue management using RQ (Redis Queue)
"""

import json
from uuid import uuid4
from typing import Dict, Any, Optional
import time
import structlog

logger = structlog.get_logger(__name__)

# RQ components (will be initialized when available)
Queue = None
Redis = None
redis_conn = None
job_queue = None
_per_key_inflight: Dict[str, int] = {}
_max_inflight_per_key: int = 3
_max_queue_length: int = 500
_result_ttl_seconds: int = 24 * 3600

def init_job_queue(redis_url: str = "redis://localhost:6379/1"):
    """Initialize job queue with Redis"""
    global Queue, Redis, redis_conn, job_queue
    
    try:
        import rq
        import redis
        
        Queue = rq.Queue
        Redis = redis.Redis
        redis_conn = redis.from_url(redis_url)
        job_queue = Queue("synth", connection=redis_conn)
        
        logger.info("Job queue initialized", redis_url=redis_url)
        return True
        
    except ImportError:
        logger.warning("RQ not available, job queue disabled")
        return False
    except Exception as e:
        logger.error("Failed to initialize job queue", error=str(e))
        return False

def enqueue_synthesis(payload: Dict[str, Any]) -> str:
    """
    Enqueue a synthesis job
    
    Args:
        payload: Job payload containing synthesis parameters
    
    Returns:
        Job ID for tracking
    """
    if job_queue is None:
        raise RuntimeError("Job queue not initialized")
    
    # Enforce queue length cap
    try:
        if job_queue.count > _max_queue_length:
            raise RuntimeError("queue_full")
    except Exception:
        pass

    # Enforce per-key concurrency
    api_key = payload.get("api_key", "unknown")
    inflight = _per_key_inflight.get(api_key, 0)
    if inflight >= _max_inflight_per_key:
        raise RuntimeError("too_many_inflight")
    _per_key_inflight[api_key] = inflight + 1

    job_id = str(uuid4())
    
    try:
        job = job_queue.enqueue(
            "src.jobs.workers.run_synthesis",
            payload,
            job_id=job_id,
            timeout="10m",  # 10 minute timeout
            result_ttl=_result_ttl_seconds
        )
        
        logger.info("Job enqueued", job_id=job_id, queue="synth")
        return job_id
        
    except Exception as e:
        # Decrement inflight on failure
        _per_key_inflight[api_key] = max(0, _per_key_inflight.get(api_key, 1) - 1)
        logger.error("Failed to enqueue job", job_id=job_id, error=str(e))
        raise

def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get job status and result
    
    Args:
        job_id: Job ID to check
    
    Returns:
        Job status information
    """
    if job_queue is None:
        return {"status": "error", "message": "Job queue not available"}
    
    try:
        job = job_queue.fetch_job(job_id)
        
        if job is None:
            return {"status": "not_found", "message": "Job not found"}
        
        if job.is_finished:
            return {
                "status": "finished",
                "result": job.result,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None
            }
        elif job.is_failed:
            return {
                "status": "failed",
                "error": str(job.exc_info),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None
            }
        elif job.is_started:
            return {
                "status": "started",
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None
            }
        else:
            return {
                "status": "queued",
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        return {"status": "error", "message": str(e)}

def cancel_job(job_id: str) -> bool:
    """
    Cancel a queued job
    
    Args:
        job_id: Job ID to cancel
    
    Returns:
        True if cancelled, False otherwise
    """
    if job_queue is None:
        return False
    
    try:
        job = job_queue.fetch_job(job_id)
        if job and not job.is_started:
            job.cancel()
            logger.info("Job cancelled", job_id=job_id)
            return True
        return False
        
    except Exception as e:
        logger.error("Failed to cancel job", job_id=job_id, error=str(e))
        return False
