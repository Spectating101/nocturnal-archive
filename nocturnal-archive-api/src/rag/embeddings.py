"""
Embeddings service using sentence transformers
"""
import os
from typing import List, Union
from sentence_transformers import SentenceTransformer


# Global model cache
_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get or create the embedding model
    
    Returns:
        SentenceTransformer: The embedding model
    """
    global _model
    
    if _model is None:
        model_name = os.getenv("RAG_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        print(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        print(f"Model loaded successfully")
    
    return _model


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
    
    # Generate embeddings with normalization
    embeddings = model.encode(texts, normalize_embeddings=True)
    
    # Convert to list format
    return embeddings.tolist()


def get_embedding_dimensions() -> int:
    """
    Get the dimension size of embeddings
    
    Returns:
        int: Number of dimensions in embedding vectors
    """
    model = get_embedding_model()
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
