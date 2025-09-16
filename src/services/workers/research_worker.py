import asyncio
import logging
import os
from typing import Dict, Any, List
from datetime import datetime
import json

from arq import ArqRedis
from arq.connections import RedisSettings
from arq.worker import Worker

# Import services needed by the worker
from src.storage.db.operations import DatabaseOperations
from src.services.llm_service.llm_manager import LLMManager
from src.services.paper_service.paper_manager import PaperManager
from src.services.search_service.search_engine import SearchEngine
from src.services.research_service.synthesizer import ResearchSynthesizer
from src.services.research_service.context_manager import ResearchContextManager
from src.services.graph.knowledge_graph import KnowledgeGraph
from src.services.rerank.reranker import Reranker

logger = logging.getLogger(__name__)

async def startup(ctx):
    """Worker startup hook to initialize services."""
    logger.info("Research worker starting up...")
    
    # Get environment variables
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/nocturnal_archive')
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    neo4j_url = os.getenv('NEO4J_URL', 'bolt://localhost:7687')
    neo4j_auth = os.getenv('NEO4J_AUTH', 'neo4j/test1234').split('/')
    
    # Initialize services
    ctx['db_ops'] = DatabaseOperations(mongo_url, redis_url)
    ctx['llm_manager'] = LLMManager(redis_url, ctx['db_ops'])
    ctx['paper_manager'] = PaperManager(ctx['db_ops'])
    ctx['search_engine'] = SearchEngine(ctx['db_ops'], redis_url)  # Fixed: only 2 args
    ctx['knowledge_graph'] = KnowledgeGraph()  # Fixed: no args needed
    ctx['reranker'] = Reranker()
    ctx['synthesizer'] = ResearchSynthesizer(ctx['db_ops'], ctx['llm_manager'], redis_url, ctx['knowledge_graph'])
    ctx['context_manager'] = ResearchContextManager(ctx['db_ops'], ctx['synthesizer'], redis_url)
    ctx['context_manager'].llm_manager = ctx['llm_manager']  # Ensure LLM manager is set
    
    # Connect to Neo4j
    try:
        # Note: KnowledgeGraph doesn't have async connect method, so we'll skip this
        logger.info("KnowledgeGraph initialized (sync connection)")
    except Exception as e:
        logger.warning(f"Failed to initialize KnowledgeGraph: {e}")
    
    logger.info("Research worker services initialized.")

async def shutdown(ctx):
    """Worker shutdown hook to close connections."""
    logger.info("Research worker shutting down...")
    
    try:
        if 'db_ops' in ctx:
            await ctx['db_ops'].cleanup()
        if 'knowledge_graph' in ctx:
            await ctx['knowledge_graph'].close()
        logger.info("Research worker services cleaned up.")
    except Exception as e:
        logger.error(f"Error during worker shutdown: {e}")

async def run_research_pipeline(ctx: Dict[str, Any], session_id: str, topic: str, research_questions: List[str], user_id: str):
    """
    Background job to run the full research pipeline with real-time updates.
    """
    logger.info(f"Starting background research pipeline for session {session_id} on topic: {topic}")
    
    context_manager: ResearchContextManager = ctx['context_manager']
    search_engine: SearchEngine = ctx['search_engine']
    paper_manager: PaperManager = ctx['paper_manager']
    synthesizer: ResearchSynthesizer = ctx['synthesizer']
    
    try:
        # Step 1: Generate search queries
        await context_manager.update_session_status(session_id, "planning", "Generating search queries...", 5.0)
        
        # Generate search queries from topic and research questions
        queries = [topic] + research_questions[:3]  # Limit to 3 additional queries
        
        await context_manager.update_session_status(session_id, "searching_papers", f"Searching for: {', '.join(queries)}", 10.0)
        
        # Step 2: Search for papers
        all_results = []
        for i, query in enumerate(queries):
            progress = 10 + (i / len(queries)) * 30  # 10-40% for search phase
            await context_manager.update_session_status(session_id, "searching_papers", f"Searching: {query}", progress)
            
            try:
                # Web search for papers
                web_results = await search_engine.web_search(query, num_results=10)
                all_results.extend(web_results)
                
                # Also try semantic search if available
                try:
                    semantic_results = await search_engine.semantic_search(query, limit=5)
                    # Convert semantic results to web result format
                    for result in semantic_results:
                        all_results.append({
                            'title': result.content[:100] + '...',
                            'url': f"semantic_result_{result.paper_id}",
                            'snippet': result.content[:200] + '...',
                            'score': result.score
                        })
                except Exception as e:
                    logger.warning(f"Semantic search failed for query '{query}': {e}")
                    
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                await context_manager.update_session_status(session_id, "searching_papers", f"Search failed: {query}", progress)
        
        # Step 3: Deduplicate and filter results
        await context_manager.update_session_status(session_id, "processing_documents", "Deduplicating and filtering results...", 40.0)
        
        unique_urls = set()
        papers_to_process = []
        for res in all_results:
            if res.get('url') and res['url'] not in unique_urls:
                unique_urls.add(res['url'])
                papers_to_process.append(res)
        
        # Limit to top 10 papers for processing
        papers_to_process = papers_to_process[:10]
        
        await context_manager.update_session_status(session_id, "processing_documents", f"Processing {len(papers_to_process)} papers...", 45.0)
        
        # Step 4: Process papers
        processed_paper_ids = []
        for i, paper_info in enumerate(papers_to_process):
            progress = 45 + (i / len(papers_to_process)) * 40  # 45-85% for processing phase
            paper_title = paper_info.get('title', paper_info['url'])
            
            await context_manager.update_session_status(session_id, "processing_documents", f"Processing {i+1}/{len(papers_to_process)}: {paper_title}", progress)
            
            try:
                # Fetch paper content
                if paper_info['url'].startswith('semantic_result_'):
                    # Handle semantic search results (already in database)
                    paper_id = paper_info['url'].replace('semantic_result_', '')
                    processed_paper_ids.append(paper_id)
                    await context_manager.add_paper_to_session(session_id, paper_id, paper_info)
                else:
                    # Fetch web content
                    content = await paper_manager.fetch_web_content(paper_info['url'])
                    if content and content.get('content'):
                        # Add paper to database
                        paper_id = await paper_manager.add_paper(
                            content=content['content'].encode('utf-8'),
                            filename=f"{paper_title}.txt",
                            content_type="text/plain"
                        )
                        processed_paper_ids.append(paper_id)
                        
                        # Add to session
                        await context_manager.add_paper_to_session(session_id, paper_id, {
                            'title': paper_title,
                            'url': paper_info['url'],
                            'snippet': paper_info.get('snippet', ''),
                            'score': paper_info.get('score', 0.0)
                        })
                        
                        logger.info(f"Successfully processed paper: {paper_title}")
                    else:
                        logger.warning(f"Could not fetch content for {paper_info['url']}")
                        
            except Exception as e:
                logger.error(f"Error processing paper {paper_info['url']}: {e}")
                await context_manager.update_session_status(session_id, "processing_documents", f"Failed: {paper_title}", progress)
        
        # Step 5: Synthesize findings
        await context_manager.update_session_status(session_id, "building_knowledge", "Synthesizing findings...", 85.0)
        
        if processed_paper_ids:
            try:
                # Get synthesis results
                synthesis_result = await synthesizer.synthesize_papers(processed_paper_ids)
                
                # Update session with synthesis
                await context_manager.update_session_synthesis(session_id, synthesis_result)
                
                await context_manager.update_session_status(session_id, "completed", "Research complete!", 100.0)
                logger.info(f"Research pipeline completed for session {session_id}")
                
                return {
                    "status": "completed",
                    "session_id": session_id,
                    "papers_processed": len(processed_paper_ids),
                    "synthesis_summary": {
                        "findings_count": len(synthesis_result.get("common_findings", [])),
                        "gaps_count": len(synthesis_result.get("research_gaps", [])),
                        "contradictions_count": len(synthesis_result.get("contradictions", []))
                    }
                }
                
            except Exception as e:
                logger.error(f"Synthesis failed for session {session_id}: {e}")
                await context_manager.update_session_status(session_id, "error", f"Synthesis failed: {e}", 90.0)
                return {"status": "error", "error": str(e)}
        else:
            await context_manager.update_session_status(session_id, "completed", "No papers processed for synthesis.", 100.0)
            logger.warning(f"No papers processed for synthesis for session {session_id}")
            return {"status": "completed", "papers_processed": 0}
    
    except Exception as e:
        logger.error(f"Research pipeline failed for session {session_id}: {e}")
        await context_manager.update_session_status(session_id, "error", f"Research failed: {e}", 0.0)
        return {"status": "error", "error": str(e)}

async def process_single_paper(ctx: Dict[str, Any], paper_id: str, session_id: str = None):
    """
    Background job to process a single paper with LLM analysis.
    """
    logger.info(f"Processing single paper: {paper_id}")
    
    paper_manager: PaperManager = ctx['paper_manager']
    llm_manager: LLMManager = ctx['llm_manager']
    context_manager: ResearchContextManager = ctx['context_manager']
    
    try:
        # Get paper content
        paper = await paper_manager.get_paper_content(paper_id)
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        # Process with LLM
        analysis_result = await llm_manager.process_document(paper_id, paper.content)
        
        # Update session if provided
        if session_id:
            await context_manager.update_session_status(session_id, "processing_documents", f"Analyzed: {paper.filename}", 50.0)
        
        return {
            "status": "completed",
            "paper_id": paper_id,
            "analysis": analysis_result
        }
        
    except Exception as e:
        logger.error(f"Error processing paper {paper_id}: {e}")
        return {"status": "error", "error": str(e)}

class WorkerSettings:
    functions = [run_research_pipeline, process_single_paper]
    redis_settings = RedisSettings(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10  # Limit concurrent jobs
    job_timeout = 3600  # 1 hour timeout


