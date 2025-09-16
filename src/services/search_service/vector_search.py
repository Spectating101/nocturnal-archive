#vector_search.py
from typing import List, Dict, Optional, Tuple
import numpy as np
import aiohttp
import os
import faiss
import pickle
import asyncio
import redis.asyncio as redis
from datetime import datetime
import json

from ...utils.logger import logger, log_operation
from ...storage.db.models import SearchResult
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
import os
import uuid
from typing import List, Dict, Tuple
from ..llm_service.embeddings import EmbeddingManager

class VectorSearchEngine:
    def __init__(self, redis_url: str = None):
        self.collection = os.environ.get("QDRANT_COLLECTION", "papers")
        self.enabled = True
        try:
            self.client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://qdrant:6333"))
            self._ensure_collection()
        except Exception:
            self.enabled = False
            self.client = None
        self.embedder = EmbeddingManager()

    def _ensure_collection(self):
        try:
            exists = self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE)
            )

    def upsert(self, points):
        if not self.enabled:
            return
        self.client.upsert(collection_name=self.collection, points=points)

    async def index_text(self, paper_id: str, text: str, metadata: Dict) -> bool:
        if not self.enabled:
            return False
        try:
            # truncate text for embedding efficiency
            text_chunk = text[:8000]
            vector = await self.embedder.get_query_embedding(text_chunk)
            point_id = str(uuid.uuid4())
            payload = {"paper_id": paper_id, "text": text_chunk, **(metadata or {})}
            self.upsert([
                qmodels.PointStruct(id=point_id, vector=vector, payload=payload)
            ])
            return True
        except Exception:
            return False

    async def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        if not self.enabled:
            return []
        try:
            vector = await self.embedder.get_query_embedding(query)
            res = self.client.search(collection_name=self.collection, query_vector=vector, limit=k, with_payload=True)
            results = []
            for r in res:
                payload = r.payload or {}
                score = float(r.score or 0)
                doc = {
                    "page_content": payload.get("text", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "text"}
                }
                results.append((doc, score))
            return results
        except Exception:
            return []
