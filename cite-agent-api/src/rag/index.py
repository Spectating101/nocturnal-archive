"""
PGVector index operations for RAG with graceful degradation when dependencies are missing.
"""
import os
from datetime import date
from typing import Dict, List, Optional

import sqlalchemy as sa
import structlog

from src.rag.chunk import chunk_text
from src.rag.embeddings import embed


# Database configuration
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/finsight")
logger = structlog.get_logger(__name__)

engine: Optional[sa.engine.Engine] = None
_engine_error: Optional[Exception] = None

try:
    engine = sa.create_engine(DB_URL)
except ModuleNotFoundError as exc:  # pragma: no cover - environment specific
    _engine_error = exc
    logger.warning("Vector database driver not available", error=str(exc))
except Exception as exc:  # pragma: no cover - connection issue
    _engine_error = exc
    logger.warning("Vector database connection failed", error=str(exc), db_url=DB_URL)


def _require_engine() -> sa.engine.Engine:
    """Return the SQLAlchemy engine or raise a descriptive error."""

    if engine is None:
        raise RuntimeError(f"Vector database engine unavailable: {_engine_error}")
    return engine


def upsert_docs(docs: List[Dict]) -> int:
    """
    Upsert documents into the vector database with chunking
    
    Args:
        docs: List of document dictionaries with keys:
              {id, title, url, date, ticker, cik, section, text}
    
    Returns:
        int: Number of chunks inserted/updated
    """
    if not docs:
        return 0
    
    rows = []
    
    for doc in docs:
        # Chunk the text
        chunks = chunk_text(doc["text"])
        
        for i, chunk_text_content in enumerate(chunks):
            chunk_id = f"{doc['id']}#c{i}"
            
            # Boost chunk with section/title context for better recall
            boosted_text = _boost_chunk_text(chunk_text_content, doc)
            
            rows.append({
                "id": chunk_id,
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "date": doc.get("date") or date.today(),
                "ticker": doc.get("ticker", ""),
                "cik": doc.get("cik", ""),
                "section": doc.get("section", ""),
                "text": boosted_text  # Use boosted text for embedding
            })
    
    if not rows:
        return 0
    
    # Generate embeddings for all chunks
    print(f"Generating embeddings for {len(rows)} chunks...")
    texts = [row["text"] for row in rows]
    embeddings = embed(texts)
    
    db_engine = _require_engine()

    # Insert/update chunks with embeddings
    with db_engine.begin() as conn:
        for row, embedding in zip(rows, embeddings):
            conn.execute(sa.text("""
                INSERT INTO docs (id, title, url, date, ticker, cik, section, text, embedding)
                VALUES (:id, :title, :url, :date, :ticker, :cik, :section, :text, :embedding)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    url = EXCLUDED.url,
                    date = EXCLUDED.date,
                    ticker = EXCLUDED.ticker,
                    cik = EXCLUDED.cik,
                    section = EXCLUDED.section,
                    text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding
            """), {
                **row,
                "embedding": embedding
            })
    
    print(f"Upserted {len(rows)} document chunks")
    return len(rows)


def search(
    query: str, 
    k: int = 5, 
    cutoff: Optional[str] = None, 
    tickers: Optional[List[str]] = None
) -> List[Dict]:
    """
    Search for similar documents using vector similarity with MMR reranking
    
    Args:
        query: Search query text
        k: Number of results to return
        cutoff: Date cutoff for point-in-time queries (YYYY-MM-DD)
        tickers: List of tickers to filter by
        
    Returns:
        List[Dict]: Search results with metadata
    """
    # Generate query embedding
    query_embedding = embed([query])[0]
    
    # Build filter conditions
    filters = ["WHERE 1=1"]
    params = {"query_embedding": query_embedding, "k": min(k * 10, 50)}  # Get more for MMR
    
    if cutoff:
        filters.append("AND date <= :cutoff")
        params["cutoff"] = cutoff
    
    if tickers:
        filters.append("AND ticker = ANY(:tickers)")
        params["tickers"] = tickers
    
    filter_clause = " ".join(filters)
    
    # Search query with vector similarity
    sql = f"""
        SELECT 
            id, title, url, date, ticker, cik, section, text,
            1 - (embedding <=> :query_embedding) AS score
        FROM docs 
        {filter_clause}
        ORDER BY embedding <=> :query_embedding
        LIMIT :k
    """
    
    db_engine = _require_engine()

    with db_engine.begin() as conn:
        results = conn.execute(sa.text(sql), params)
        rows = [dict(row) for row in results]
    
    # Add snippets for display
    for row in rows:
        full_text = row.pop("text", "")
        row["snippet"] = full_text[:400] + ("..." if len(full_text) > 400 else "")
    
    # Apply MMR reranking for better diversity
    if len(rows) > k:
        rows = _mmr_rerank(rows, query_embedding, k)
    
    return rows


def _mmr_rerank(results: List[Dict], query_embedding: List[float], k: int, lambda_param: float = 0.7) -> List[Dict]:
    """
    Apply Maximal Marginal Relevance (MMR) reranking for better citation diversity
    
    Args:
        results: Initial search results
        query_embedding: Query vector
        k: Number of final results
        lambda_param: Balance between relevance (1.0) and diversity (0.0)
        
    Returns:
        List[Dict]: Reranked results
    """
    if len(results) <= k:
        return results
    
    # Extract embeddings for MMR calculation
    result_embeddings = []
    for result in results:
        # Re-embed the text for MMR (could be cached for performance)
        text_embedding = embed([result["snippet"]])[0]
        result_embeddings.append(text_embedding)
    
    selected = []
    remaining = list(range(len(results)))
    
    # Select first result (highest relevance)
    if remaining:
        selected.append(remaining.pop(0))
    
    # Select remaining results using MMR
    while len(selected) < k and remaining:
        best_idx = None
        best_score = -float('inf')
        
        for candidate in remaining:
            # Relevance score (cosine similarity to query)
            relevance = _cosine_similarity(query_embedding, result_embeddings[candidate])
            
            # Diversity score (max similarity to already selected)
            if selected:
                diversity = max(_cosine_similarity(result_embeddings[candidate], result_embeddings[sel]) 
                              for sel in selected)
            else:
                diversity = 0
            
            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = candidate
        
        if best_idx is not None:
            selected.append(remaining.remove(best_idx))
    
    return [results[i] for i in selected]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import math
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    
    if norm_a == 0 or norm_b == 0:
        return 0
    
    return dot_product / (norm_a * norm_b)


def _boost_chunk_text(chunk_text: str, doc: Dict) -> str:
    """
    Boost chunk text with section/title context for better recall
    
    Args:
        chunk_text: Original chunk text
        doc: Document metadata
        
    Returns:
        str: Boosted text with context
    """
    # Extract key context information
    section = doc.get("section", "")
    title = doc.get("title", "")
    ticker = doc.get("ticker", "")
    date = doc.get("date")
    
    # Format date if available
    date_str = ""
    if date:
        if hasattr(date, 'strftime'):
            date_str = date.strftime("%Y-%m-%d")
        else:
            date_str = str(date)
    
    # Build context prefix
    context_parts = []
    
    if section:
        context_parts.append(f"[{section}]")
    
    if ticker:
        context_parts.append(f"{ticker}")
    
    if date_str:
        context_parts.append(f"{date_str}")
    
    if title:
        context_parts.append(title)
    
    # Create boosted text
    if context_parts:
        context_prefix = " ".join(context_parts) + " — "
        boosted_text = context_prefix + chunk_text
    else:
        boosted_text = chunk_text
    
    # Ensure we don't exceed reasonable length for embeddings
    max_length = 2000  # Leave some room for the original text
    if len(boosted_text) > max_length:
        # Truncate context prefix if needed
        available_length = max_length - len(chunk_text) - 10  # 10 for " — "
        if available_length > 0:
            context_prefix = context_prefix[:available_length] + " — "
            boosted_text = context_prefix + chunk_text
        else:
            boosted_text = chunk_text
    
    return boosted_text


def get_doc_stats() -> Dict:
    """
    Get statistics about indexed documents
    
    Returns:
        Dict: Statistics about the document collection
    """
    db_engine = _require_engine()

    with db_engine.begin() as conn:
        # Total documents
        total_result = conn.execute(sa.text("SELECT COUNT(*) as count FROM docs"))
        total_docs = total_result.scalar()
        
        # Documents by ticker
        ticker_result = conn.execute(sa.text("""
            SELECT ticker, COUNT(*) as count 
            FROM docs 
            WHERE ticker != '' 
            GROUP BY ticker 
            ORDER BY count DESC 
            LIMIT 10
        """))
        ticker_counts = [{"ticker": row.ticker, "count": row.count} for row in ticker_result]
        
        # Date range
        date_result = conn.execute(sa.text("""
            SELECT MIN(date) as earliest, MAX(date) as latest 
            FROM docs 
            WHERE date IS NOT NULL
        """))
        date_row = date_result.fetchone()
        date_range = {
            "earliest": str(date_row.earliest) if date_row and date_row.earliest else None,
            "latest": str(date_row.latest) if date_row and date_row.latest else None
        }
        
        # Sections
        section_result = conn.execute(sa.text("""
            SELECT section, COUNT(*) as count 
            FROM docs 
            WHERE section != '' 
            GROUP BY section 
            ORDER BY count DESC 
            LIMIT 10
        """))
        section_counts = [{"section": row.section, "count": row.count} for row in section_result]
    
    return {
        "total_documents": total_docs,
        "ticker_counts": ticker_counts,
        "date_range": date_range,
        "section_counts": section_counts
    }


def clear_docs(ticker: Optional[str] = None) -> int:
    """
    Clear documents from the index
    
    Args:
        ticker: If provided, only clear documents for this ticker
        
    Returns:
        int: Number of documents deleted
    """
    db_engine = _require_engine()

    with db_engine.begin() as conn:
        if ticker:
            result = conn.execute(sa.text("DELETE FROM docs WHERE ticker = :ticker"), {"ticker": ticker})
        else:
            result = conn.execute(sa.text("DELETE FROM docs"))
        
        deleted_count = result.rowcount
    
    print(f"Deleted {deleted_count} documents")
    return deleted_count


if __name__ == "__main__":
    # Test the index functionality
    print("Testing RAG index...")
    
    # Test document insertion
    test_docs = [{
        "id": "TEST:Item7",
        "title": "Item 7 - Management's Discussion",
        "url": "https://example.com",
        "date": "2025-01-01",
        "ticker": "TEST",
        "cik": "0000000000",
        "section": "MD&A",
        "text": "We expect margin compression due to pricing pressure and FX headwinds. Revenue growth remains strong despite market challenges."
    }]
    
    print("Inserting test documents...")
    inserted = upsert_docs(test_docs)
    print(f"Inserted {inserted} chunks")
    
    # Test search
    print("Testing search...")
    results = search("margin compression", k=3)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['title']} (score: {result['score']:.3f})")
    
    # Test stats
    print("Getting stats...")
    stats = get_doc_stats()
    print(f"Total documents: {stats['total_documents']}")
    
    # Cleanup
    print("Cleaning up test data...")
    clear_docs("TEST")
