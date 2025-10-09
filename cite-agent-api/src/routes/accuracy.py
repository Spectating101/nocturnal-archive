"""
Accuracy Analytics Endpoints
Track truth-seeking metrics: UCR, FCR, quality scores
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import asyncpg
import os
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/analytics/accuracy", tags=["accuracy"])

async def get_db():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/cite_agent")
    return await asyncpg.connect(db_url)


@router.get("/stats")
async def get_accuracy_stats(days: int = 7):
    """
    Get overall accuracy statistics
    
    Metrics:
    - Unsupported Claim Rate (UCR): % of responses without citations
    - False Citation Rate (FCR): % of citations that are broken
    - Quality Score: 0-1, based on citation verification
    - Citation Rate: % of responses that have citations
    
    Target:
    - UCR < 2%
    - FCR ~ 0%
    - Quality Score > 0.9
    """
    conn = await get_db()
    try:
        result = await conn.fetchval(
            "SELECT get_accuracy_stats($1)",
            days
        )
        return result
    finally:
        await conn.close()


@router.get("/daily")
async def get_daily_accuracy(limit: int = 30):
    """Get daily accuracy metrics"""
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM accuracy_metrics
            ORDER BY date DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.get("/weekly")
async def get_weekly_accuracy(limit: int = 12):
    """Get weekly accuracy summary"""
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM accuracy_weekly
            ORDER BY week_start DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.get("/leaderboard")
async def get_user_accuracy_leaderboard(limit: int = 50):
    """
    Get users ranked by accuracy/quality
    Useful for identifying power users or problem queries
    """
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM user_accuracy
            ORDER BY avg_quality_score DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.get("/citations/{query_id}")
async def get_citation_details(query_id: str):
    """Get detailed citation verification for a specific query"""
    conn = await get_db()
    try:
        # Get response quality
        quality = await conn.fetchrow(
            """
            SELECT rq.*, q.query_text, q.response_text
            FROM response_quality rq
            JOIN queries q ON rq.query_id = q.query_id
            WHERE rq.query_id = $1
            """,
            query_id
        )
        
        if not quality:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get citation details
        citations = await conn.fetch(
            """
            SELECT *
            FROM citation_details
            WHERE response_id = $1
            ORDER BY created_at
            """,
            quality['response_id']
        )
        
        return {
            "query_id": query_id,
            "quality": dict(quality),
            "citations": [dict(c) for c in citations]
        }
    finally:
        await conn.close()


@router.get("/trends")
async def get_accuracy_trends(days: int = 30):
    """
    Get accuracy trends over time
    Shows if quality is improving/declining
    """
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT
                DATE(created_at) as date,
                AVG(citation_quality_score) as quality_score,
                COUNT(*) as responses,
                SUM(CASE WHEN NOT has_citations THEN 1 ELSE 0 END)::float / COUNT(*) as ucr,
                SUM(broken_citations)::float / NULLIF(SUM(total_citations), 0) as fcr
            FROM response_quality
            WHERE created_at > NOW() - $1::INTERVAL
            GROUP BY DATE(created_at)
            ORDER BY date ASC
            """,
            f"{days} days"
        )
        
        # Calculate trend direction
        if len(rows) >= 2:
            recent_avg = sum(r['quality_score'] or 0 for r in rows[-7:]) / min(7, len(rows))
            older_avg = sum(r['quality_score'] or 0 for r in rows[:7]) / min(7, len(rows))
            trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "data": [dict(row) for row in rows]
        }
    finally:
        await conn.close()


@router.post("/record")
async def record_response_quality(
    query_id: str,
    response_id: str,
    citation_results: dict
):
    """
    Internal endpoint to record quality metrics
    Called after each query
    """
    conn = await get_db()
    try:
        # Insert response quality
        await conn.execute(
            """
            INSERT INTO response_quality (
                response_id,
                query_id,
                has_citations,
                total_citations,
                verified_citations,
                broken_citations,
                citation_quality_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (response_id) DO UPDATE SET
                has_citations = EXCLUDED.has_citations,
                total_citations = EXCLUDED.total_citations,
                verified_citations = EXCLUDED.verified_citations,
                broken_citations = EXCLUDED.broken_citations,
                citation_quality_score = EXCLUDED.citation_quality_score
            """,
            response_id,
            query_id,
            citation_results['has_citations'],
            citation_results['total_citations'],
            citation_results['url_verification']['verified'],
            citation_results['url_verification']['broken'],
            citation_results['quality_score']
        )
        
        # Insert citation details
        for url_result in citation_results['url_verification']['details']:
            await conn.execute(
                """
                INSERT INTO citation_details (
                    response_id,
                    citation_type,
                    citation_text,
                    verification_status,
                    http_status_code
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                response_id,
                'url',
                url_result['url'],
                url_result['status'],
                url_result.get('status_code')
            )
        
        return {"status": "recorded"}
        
    finally:
        await conn.close()

