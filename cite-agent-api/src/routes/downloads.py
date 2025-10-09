"""
Download tracking endpoint
Logs downloads and redirects to GitHub releases
"""

from datetime import datetime, timezone
from typing import Optional
import structlog
from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
import asyncpg
import os
import secrets

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/download", tags=["downloads"])

# GitHub release URLs (update these when you create releases)
GITHUB_RELEASE_BASE = "https://github.com/yourusername/nocturnal-archive/releases/download"
VERSION = "v0.9.0-beta"

DOWNLOAD_URLS = {
    "windows": f"{GITHUB_RELEASE_BASE}/{VERSION}/nocturnal-archive-setup.exe",
    "macos": f"{GITHUB_RELEASE_BASE}/{VERSION}/nocturnal-archive.dmg",
    "linux": f"{GITHUB_RELEASE_BASE}/{VERSION}/nocturnal-archive.tar.gz"
}

# Database connection
async def get_db():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/nocturnal_archive")
    return await asyncpg.connect(db_url)

@router.get("/{platform}")
async def track_download(platform: str, request: Request):
    """
    Track download and redirect to file
    
    Usage:
    - https://api.nocturnal.dev/download/windows
    - https://api.nocturnal.dev/download/macos
    - https://api.nocturnal.dev/download/linux
    """
    # Validate platform
    if platform not in DOWNLOAD_URLS:
        return Response(
            content=f"Invalid platform. Choose: {', '.join(DOWNLOAD_URLS.keys())}",
            status_code=400
        )
    
    # Extract client info
    client_ip = request.headers.get("x-forwarded-for") or (
        request.client.host if request.client else "unknown"
    )
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", "direct")
    
    # Log download
    conn = await get_db()
    try:
        download_id = secrets.token_urlsafe(16)
        
        await conn.execute(
            """
            INSERT INTO downloads (download_id, platform, ip, user_agent, referrer, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            download_id,
            platform,
            client_ip,
            user_agent,
            referrer,
            datetime.now(timezone.utc)
        )
        
        logger.info(
            "Download tracked",
            download_id=download_id,
            platform=platform,
            ip=client_ip[:10] + "...",  # Truncate for privacy
        )
        
    except Exception as e:
        logger.error("Failed to track download", error=str(e), platform=platform)
        # Continue anyway - don't block download
    
    finally:
        await conn.close()
    
    # Redirect to actual file
    return RedirectResponse(
        url=DOWNLOAD_URLS[platform],
        status_code=302
    )

@router.get("/stats/summary")
async def download_stats():
    """
    Get download statistics
    Public endpoint for transparency
    """
    conn = await get_db()
    try:
        # Total downloads
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM downloads"
        )
        
        # By platform
        by_platform = await conn.fetch(
            """
            SELECT platform, COUNT(*) as count
            FROM downloads
            GROUP BY platform
            ORDER BY count DESC
            """
        )
        
        # Last 7 days
        last_7_days = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM downloads
            WHERE timestamp > NOW() - INTERVAL '7 days'
            """
        )
        
        # Last 24 hours
        last_24_hours = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM downloads
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            """
        )
        
        return {
            "total_downloads": total or 0,
            "last_7_days": last_7_days or 0,
            "last_24_hours": last_24_hours or 0,
            "by_platform": {row['platform']: row['count'] for row in by_platform}
        }
        
    finally:
        await conn.close()

