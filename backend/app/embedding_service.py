import os
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

# Set cache directory for model (matches Dockerfile)
os.environ.setdefault('TRANSFORMERS_CACHE', '/app/models')
os.environ.setdefault('HF_HOME', '/app/models')
os.environ.setdefault('HF_DATASETS_CACHE', '/app/models')

logger = logging.getLogger(__name__)

class EmbeddingService:
    # service for generating and managing word embeddings using sentence-transformers
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # init embedding service
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        self.embedding_dim = 384  
        self._load_model()
    
    def _load_model(self):
        # load the sentence-transformer model
        try:
            logger.info(f"Loading sentence-transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def encode(self, texts: List[str]) -> np.ndarray:
        # generate embeddings for a list of texts/words
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        if isinstance(texts, str):
            texts = [texts]
        
        # generate embeddings
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            # normalize for cosine similarity
            normalize_embeddings=True  
        )
        
        return embeddings
    
    def encode_word(self, word: str) -> np.ndarray:
        # embed a single word
        embedding = self.encode([word])
        return embedding[0]
    
    def get_embedding_dim(self) -> int:
        # get the dimension of embeddings produced by this model
        return self.embedding_dim