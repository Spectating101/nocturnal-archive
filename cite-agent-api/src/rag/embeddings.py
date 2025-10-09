"""
Embeddings service with graceful fallback when sentence transformers are unavailable.
"""
import hashlib
import math
import os
from typing import List, Optional, TYPE_CHECKING, Union
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer as SentenceTransformerType
else:  # pragma: no cover - typing fallback
    SentenceTransformerType = object

import structlog

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - exercised when dependency missing
    SentenceTransformer = None  # type: ignore[assignment]

logger = structlog.get_logger(__name__)


# Global model cache
_model = None
_FALLBACK_DIM = 128


def get_embedding_model() -> Optional[SentenceTransformerType]:
    """
    Get or create the embedding model
    
    Returns:
        SentenceTransformer: The embedding model
    """
    global _model

    if SentenceTransformer is None:
        if not os.getenv("RAG_EMBED_FORCE_MODEL"):
            logger.warning(
                "SentenceTransformer not available, falling back to deterministic hash embeddings",
            )
            return None
        raise ImportError("sentence_transformers is required but not installed")

    if _model is None:
        model_name = os.getenv("RAG_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Loading embedding model", model=model_name)
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")

    return _model


def _fallback_embed(text: str) -> List[float]:
    """Generate a deterministic, unit-normalized embedding vector without external models."""

    seed = text.encode("utf-8") or b"\x00"
    values: List[int] = []
    digest = hashlib.sha256(seed).digest()

    while len(values) < _FALLBACK_DIM:
        values.extend(digest)
        digest = hashlib.sha256(digest + seed).digest()

    # Convert byte values to floats in [-1, 1]
    floats = [((byte / 255.0) * 2.0) - 1.0 for byte in values[:_FALLBACK_DIM]]

    norm = math.sqrt(sum(v * v for v in floats))
    if norm == 0:
        return [0.0] * _FALLBACK_DIM
    return [v / norm for v in floats]


def embed(texts: Union[str, List[str]]) -> List[List[float]]:
    """
    Generate embeddings for text(s)
    
    Args:
        texts: Single text string or list of text strings
        
    Returns:
        List[List[float]]: List of embedding vectors (normalized)
    """
    model = get_embedding_model()

    # Handle single text
    if isinstance(texts, str):
        texts = [texts]

    if model is None:
        return [_fallback_embed(text) for text in texts]

    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def get_embedding_dimensions() -> int:
    """
    Get the dimension size of embeddings
    
    Returns:
        int: Number of dimensions in embedding vectors
    """
    model = get_embedding_model()
    if model is None:
        return _FALLBACK_DIM
    return model.get_sentence_embedding_dimension()


if __name__ == "__main__":
    # Test the embeddings
    test_texts = [
        "Apple reported strong quarterly earnings",
        "Revenue increased by 15% year-over-year",
        "Management discussed margin compression"
    ]
    
    print("Testing embeddings...")
    embeddings = embed(test_texts)
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Each embedding has {len(embeddings[0])} dimensions")
    print(f"Model dimensions: {get_embedding_dimensions()}")
