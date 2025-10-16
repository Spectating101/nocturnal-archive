"""
Admin Statistics Dashboard
Shows user activity, token usage, queries, etc.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import structlog
import os
import asyncpg

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Simple admin key
ADMIN_KEY = "admin-key-for-stats-2024"

async def get_db():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    return await asyncpg.connect(db_url)

@router.get("/stats")
async def admin_stats(admin_key: Optional[str] = Header(None)):
    """Get comprehensive system statistics"""
    
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db = await get_db()
    
    try:
        # User stats
        total_users = await db.fetchval("SELECT COUNT(*) FROM users")
        users_list = await db.fetch("""
            SELECT email, created_at, tokens_used_today
            FROM users
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        # Query stats
        total_queries = await db.fetchval("SELECT COUNT(*) FROM queries")
        queries_today = await db.fetchval("""
            SELECT COUNT(*) FROM queries
            WHERE timestamp >= NOW() - INTERVAL '1 day'
        """)

        queries_last_7d = await db.fetchval("""
            SELECT COUNT(*) FROM queries
            WHERE timestamp >= NOW() - INTERVAL '7 days'
        """)
        
        # Token usage by user
        token_usage = await db.fetch("""
            SELECT u.email,
                   COUNT(q.query_id) as query_count,
                   COALESCE(SUM(q.tokens_used), 0) as total_tokens,
                   MAX(q.timestamp) as last_active
            FROM users u
            LEFT JOIN queries q ON u.user_id = q.user_id
            GROUP BY u.email
            ORDER BY total_tokens DESC
        """)
        
        # Recent queries
        recent_queries = await db.fetch("""
            SELECT u.email, q.query_text, q.tokens_used, q.timestamp
            FROM queries q
            JOIN users u ON q.user_id = u.user_id
            ORDER BY q.timestamp DESC
            LIMIT 20
        """)
        
        # Citation stats
        papers_cited = await db.fetchval("SELECT COUNT(*) FROM citation_details")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
                "list": [
                    {
                        "email": row[0],
                        "created_at": row[1].isoformat() if row[1] else None,
                        "tokens_used_today": row[2]
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
    finally:
        await db.close()

