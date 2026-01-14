"""
Embedding utilities for bioRxiv RAG system using SciBERT.
"""

import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SciBERTEmbedder:
    """
    SciBERT-based embedding generator for scientific text.
    Uses sentence-transformers with a SciBERT model optimized for scientific literature.
    """
    
    def __init__(self, model_name: str = "allenai/scibert_scivocab_uncased", device: Optional[str] = None):
        """
        Initialize the SciBERT embedder.
        
        Args:
            model_name: HuggingFace model name for SciBERT
            device: Device to run on ('cuda', 'cpu', or None for auto-detect)
        """
        self.model_name = model_name
        
        # Auto-detect device if not specified
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        logger.info(f"Initializing SciBERT embedder on device: {self.device}")
        
        # Load the sentence transformer model
        # Note: We'll use sentence-transformers wrapper for easier embedding generation
        try:
            # Try to use a sentence-transformers compatible SciBERT model
            self.model = SentenceTransformer('sentence-transformers/allenai-specter', device=self.device)
            logger.info("Loaded SPECTER model (SciBERT-based for scientific papers)")
        except Exception as e:
            logger.warning(f"Could not load SPECTER model: {e}")
            logger.info("Falling back to all-MiniLM-L6-v2 (general purpose)")
            # Fallback to a general model if SciBERT isn't available
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of embeddings
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            return np.array([])
        
        # Filter out empty texts but keep track of indices
        non_empty_texts = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                text_indices.append(i)
        
        if not non_empty_texts:
            # All texts are empty
            embedding_dim = self.model.get_sentence_embedding_dimension()
            return np.zeros((len(texts), embedding_dim))
        
        try:
            # Generate embeddings for non-empty texts
            embeddings = self.model.encode(non_empty_texts, convert_to_numpy=True, batch_size=32)
            
            # Create full result array with zeros for empty texts
            embedding_dim = embeddings.shape[1]
            result = np.zeros((len(texts), embedding_dim))
            
            # Fill in the actual embeddings
            for i, text_idx in enumerate(text_indices):
                result[text_idx] = embeddings[i]
                
            return result
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            embedding_dim = self.model.get_sentence_embedding_dimension()
            return np.zeros((len(texts), embedding_dim))
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.model.get_sentence_embedding_dimension()
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(embedding1, embedding2) / (norm1 * norm2)

def add_embeddings_to_chunks(chunks: List[Dict[str, Any]], embedder: SciBERTEmbedder) -> List[Dict[str, Any]]:
    """
    Add embeddings to a list of chunks.
    
    Args:
        chunks: List of chunk dictionaries from build_rag.py
        embedder: SciBERTEmbedder instance
        
    Returns:
        List of chunks with embeddings added
    """
    if not chunks:
        return chunks
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    
    # Extract content from all chunks
    texts = [chunk.get('content', '') for chunk in chunks]
    
    # Generate embeddings in batch
    embeddings = embedder.embed_texts(texts)
    
    # Add embeddings to chunks
    enhanced_chunks = []
    for i, chunk in enumerate(chunks):
        enhanced_chunk = chunk.copy()
        enhanced_chunk['embedding'] = embeddings[i].tolist()  # Convert to list for JSON serialization
        enhanced_chunk['embedding_model'] = embedder.model_name
        enhanced_chunk['embedding_dimension'] = len(embeddings[i])
        enhanced_chunks.append(enhanced_chunk)
    
    logger.info(f"Successfully added embeddings (dim={embeddings.shape[1]}) to all chunks")
    return enhanced_chunks

# Global embedder instance (lazy loading)
_global_embedder = None

def get_embedder() -> SciBERTEmbedder:
    """Get or create a global embedder instance."""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = SciBERTEmbedder()
    return _global_embedder
