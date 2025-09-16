import os
from typing import List, Dict

class Reranker:
    def __init__(self):
        self.provider = os.environ.get("RERANK_PROVIDER", "cohere")
        self.enabled = True
        self.client = None
        if self.provider == "cohere":
            try:
                import cohere
                self.client = cohere.Client(api_key=os.environ.get("COHERE_API_KEY"))
            except Exception:
                self.enabled = False

    async def rerank(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        if not self.enabled or not self.client:
            return documents[:top_k]
        try:
            inputs = [d.get("content", "")[:4000] for d in documents]
            res = self.client.rerank(model=os.environ.get("COHERE_RERANK_MODEL", "rerank-english-v3.0"), query=query, documents=inputs, top_n=min(top_k, len(inputs)))
            ranked = []
            for item in res.results:
                d = documents[item.index]
                d["rerank_score"] = item.relevance_score
                ranked.append(d)
            ranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return ranked
        except Exception:
            return documents[:top_k]


