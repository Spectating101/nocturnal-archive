"""
Admin Statistics Dashboard
Shows user activity, token usage, queries, etc.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import structlog
from datetime import datetime, timedelta

from src.database import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Simple admin key (set in Heroku config)
ADMIN_KEY = "admin-key-for-stats-2024"

@router.get("/stats")
async def admin_stats(admin_key: Optional[str] = Header(None)):
    """Get comprehensive system statistics"""
    
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db = next(get_db())
    
    try:
        # User stats
        total_users = db.execute("SELECT COUNT(*) FROM users").scalar()
        users_list = db.execute("""
            SELECT email, created_at, query_limit 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 50
        """).fetchall()
        
        # Query stats
        total_queries = db.execute("SELECT COUNT(*) FROM queries").scalar()
        queries_today = db.execute("""
            SELECT COUNT(*) FROM queries 
            WHERE created_at >= NOW() - INTERVAL '1 day'
        """).scalar()
        
        queries_last_7d = db.execute("""
            SELECT COUNT(*) FROM queries 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """).scalar()
        
        # Token usage by user
        token_usage = db.execute("""
            SELECT u.email, 
                   COUNT(q.id) as query_count,
                   SUM(q.tokens_used) as total_tokens,
                   MAX(q.created_at) as last_active
            FROM users u
            LEFT JOIN queries q ON u.user_id = q.user_id
            GROUP BY u.email
            ORDER BY total_tokens DESC
        """).fetchall()
        
        # Recent queries
        recent_queries = db.execute("""
            SELECT u.email, q.query, q.tokens_used, q.created_at
            FROM queries q
            JOIN users u ON q.user_id = u.user_id
            ORDER BY q.created_at DESC
            LIMIT 20
        """).fetchall()
        
        # Citation stats
        papers_cited = db.execute("SELECT COUNT(*) FROM citation_details").scalar()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
                "list": [
                    {
                        "email": row[0],
                        "created_at": row[1].isoformat() if row[1] else None,
                        "query_limit": row[2]
                    }
                    for row in users_list
                ]
            },
            "queries": {
                "total": total_queries,
                "today": queries_today,
                "last_7_days": queries_last_7d,
                "recent": [
                    {
                        "email": row[0],
                        "query": row[1][:100] if row[1] else "",
                        "tokens": row[2],
                        "timestamp": row[3].isoformat() if row[3] else None
                    }
                    for row in recent_queries
                ]
            },
            "token_usage": [
                {
                    "email": row[0],
                    "queries": row[1],
                    "total_tokens": row[2],
                    "last_active": row[3].isoformat() if row[3] else None
                }
                for row in token_usage
            ],
            "papers_cited": papers_cited
        }
    
    except Exception as e:
        logger.error("Admin stats failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

