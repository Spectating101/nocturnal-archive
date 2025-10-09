"""
Text chunking utilities for RAG
"""
from typing import List


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better RAG performance
    
    Args:
        text: Input text to chunk
        max_chars: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Clean up whitespace
    text = " ".join(text.split())
    
    # If text is short enough, return as single chunk
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    n = len(text)
    
    while start < n:
        end = min(start + max_chars, n)
        
        # Try to break at sentence boundary for better context
        if end < n:  # Don't break at sentence boundary for the last chunk
            cut = text.rfind(". ", start, end)
            if cut > start + 200:  # Only use sentence boundary if it's not too early
                end = cut + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = max(0, end - overlap)
        
        # Prevent infinite loop
        if start >= n:
            break
    
    return [c for c in chunks if c]  # Remove empty chunks
