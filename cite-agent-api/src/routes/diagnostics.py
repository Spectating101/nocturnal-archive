"""
Diagnostics and self-test endpoint for system health monitoring
"""

import time
import os
import subprocess
import structlog
from fastapi import APIRouter, Query
from typing import Dict, Any, List
from datetime import datetime, timezone

from src.engine.research_engine import sophisticated_engine
from src.services.performance_integration import performance_integration

logger = structlog.get_logger(__name__)
router = APIRouter()

def get_current_commit() -> str:
    """Get current git commit hash"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
    except:
        return "unknown"

def check_component(name: str, check_fn, checks: List[Dict[str, Any]]) -> None:
    """Helper to add a check result to the checks list"""
    start_time = time.perf_counter()
    ok = True
    error = None
    
    try:
        check_fn()
    except Exception as e:
        ok = False
        error = str(e)
    
    latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
    
    checks.append({
        "name": name,
        "ok": ok,
        "latency_ms": latency_ms,
        "error": error
    })

@router.get("/selftest")
async def selftest(live: bool = Query(False, description="Include live provider checks")):
    """
    Comprehensive self-test endpoint that checks system health
    
    - live=false: Only in-process checks (no network calls)
    - live=true: Include live provider health checks
    """
    start_time = time.perf_counter()
    checks = []
    
    # In-process checks (no network)
    check_component("engine.load", lambda: sophisticated_engine.enhanced_research is not None, checks)
    check_component("performance.rust_available", lambda: performance_integration.rust_available, checks)
    check_component("performance.python_fallback", lambda: performance_integration.performance_service is not None, checks)
    
    # Check if sophisticated engine components are loaded
    check_component("sophisticated.enhanced_research", 
                   lambda: sophisticated_engine.enhanced_research is not None, checks)
    check_component("sophisticated.enhanced_synthesizer", 
                   lambda: sophisticated_engine.enhanced_synthesizer is not None, checks)
    check_component("sophisticated.search_engine", 
                   lambda: sophisticated_engine.search_engine is not None, checks)
    check_component("sophisticated.llm_manager", 
                   lambda: sophisticated_engine.llm_manager is not None, checks)
    
    # Optional live provider checks
    if live:
        # Check OpenAlex
        check_component("openalex.ping", 
                       lambda: __import__('httpx').AsyncClient().get("https://api.openalex.org/works?search=test&per-page=1", timeout=5.0), 
                       checks)
        
        # Check OpenAI (if key is set)
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "sk-dummy":
            check_component("openai.ping", 
                           lambda: __import__('openai').AsyncOpenAI().models.list(), 
                           checks)
        else:
            checks.append({
                "name": "openai.ping",
                "ok": False,
                "latency_ms": 0.0,
                "error": "OPENAI_API_KEY not set or is dummy"
            })
    
    total_ms = round((time.perf_counter() - start_time) * 1000, 1)
    all_ok = all(check["ok"] for check in checks)
    
    return {
        "ok": all_ok,
        "total_ms": total_ms,
        "checks": checks,
        "git_commit": get_current_commit(),
        "build_id": os.getenv("BUILD_ID", "dev"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
        "live_checks": live
    }

@router.get("/playground")
async def playground():
    """
    Debug playground endpoint for testing API calls
    Returns a simple HTML form for testing endpoints
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nocturnal Archive API Playground</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; margin-bottom: 10px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; }
            .error { background: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Nocturnal Archive API Playground</h1>
            
            <div class="form-group">
                <label>Endpoint:</label>
                <select id="endpoint">
                    <option value="/api/health">Health Check</option>
                    <option value="/api/search">Search Papers</option>
                    <option value="/api/synthesize">Synthesize Papers</option>
                    <option value="/api/format">Format Citations</option>
                    <option value="/diag/selftest">Self Test</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Request Body (JSON):</label>
                <textarea id="requestBody" rows="6" placeholder='{"query": "machine learning", "limit": 3}'></textarea>
            </div>
            
            <button onclick="makeRequest()">Send Request</button>
            
            <div id="result" class="result" style="display: none;">
                <h3>Response:</h3>
                <pre id="responseText"></pre>
            </div>
        </div>
        
        <script>
            async function makeRequest() {
                const endpoint = document.getElementById('endpoint').value;
                const requestBody = document.getElementById('requestBody').value;
                const resultDiv = document.getElementById('result');
                const responseText = document.getElementById('responseText');
                
                try {
                    const options = {
                        method: endpoint === '/api/health' ? 'GET' : 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    };
                    
                    if (requestBody && endpoint !== '/api/health') {
                        options.body = requestBody;
                    }
                    
                    const response = await fetch(endpoint, options);
                    const data = await response.json();
                    
                    responseText.textContent = JSON.stringify(data, null, 2);
                    resultDiv.className = 'result';
                    resultDiv.style.display = 'block';
                } catch (error) {
                    responseText.textContent = 'Error: ' + error.message;
                    resultDiv.className = 'result error';
                    resultDiv.style.display = 'block';
                }
            }
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
