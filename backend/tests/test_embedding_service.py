import pytest
import numpy as np
from app.embedding_service import EmbeddingService

class TestEmbeddingService:    
    def test_embedding_service_initialization(self, real_embedding_service):
        assert real_embedding_service.model is not None
        assert real_embedding_service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert real_embedding_service.embedding_dim == 384
    
    def test_get_embedding_dim(self, real_embedding_service):
        dim = real_embedding_service.get_embedding_dim()
        assert dim == 384
        assert isinstance(dim, int)
    
    def test_encode_single_word(self, real_embedding_service):
        word = "cat"
        embedding = real_embedding_service.encode_word(word)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
    
    def test_encode_multiple_words(self, real_embedding_service):
        words = ["cat", "dog", "bird"]
        embeddings = real_embedding_service.encode(words)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32
    
    def test_encode_string_single_word(self, real_embedding_service):
        word = "cat"
        embedding = real_embedding_service.encode(word)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1, 384)
    
    def test_embeddings_are_normalized(self, real_embedding_service):
        words = ["cat", "dog", "bird"]
        embeddings = real_embedding_service.encode(words)
        
        for embedding in embeddings:
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.01, f"Embedding not normalized: norm={norm}"
    
    def test_embeddings_are_deterministic(self, real_embedding_service):
        word = "cat"
        embedding1 = real_embedding_service.encode_word(word)
        embedding2 = real_embedding_service.encode_word(word)
        
        np.testing.assert_array_almost_equal(embedding1, embedding2)
    
    def test_different_words_produce_different_embeddings(self, real_embedding_service):
        word1 = "cat"
        word2 = "dog"
        
        embedding1 = real_embedding_service.encode_word(word1)
        embedding2 = real_embedding_service.encode_word(word2)        
        assert not np.array_equal(embedding1, embedding2)
    
    def test_similar_words_have_high_similarity(self, real_embedding_service):
        similar_pairs = [
            ("cat", "kitten"),
            ("dog", "puppy"),
            ("car", "vehicle"),
            ("happy", "joyful"),
        ]
        
        for word1, word2 in similar_pairs:
            emb1 = real_embedding_service.encode_word(word1)
            emb2 = real_embedding_service.encode_word(word2)
            
            similarity = np.dot(emb1, emb2)
            assert similarity > 0.5, f"{word1} and {word2} should have similarity > 0.5, got {similarity:.3f}"
    
    def test_dissimilar_words_have_low_similarity(self, real_embedding_service):
        dissimilar_pairs = [
            ("cat", "computer"),
            ("dog", "mountain"),
            ("car", "philosophy"),
        ]
        
        for word1, word2 in dissimilar_pairs:
            emb1 = real_embedding_service.encode_word(word1)
            emb2 = real_embedding_service.encode_word(word2)
            
            similarity = np.dot(emb1, emb2)
            assert similarity < 0.5, f"{word1} and {word2} should have similarity < 0.5, got {similarity:.3f}"
    
    def test_encode_handles_empty_list(self, real_embedding_service):
        embeddings = real_embedding_service.encode([])
        assert isinstance(embeddings, np.ndarray)
        # Empty list may return shape (0,) or (0, 384) depending on implementation
        assert len(embeddings.shape) >= 1
        assert embeddings.shape[0] == 0
    
    def test_encode_handles_case_variations(self, real_embedding_service):
        word_upper = "CAT"
        word_lower = "cat"
        word_mixed = "Cat"
        
        emb_upper = real_embedding_service.encode_word(word_upper)
        emb_lower = real_embedding_service.encode_word(word_lower)
        emb_mixed = real_embedding_service.encode_word(word_mixed)
        
        assert emb_upper.shape == (384,)
        assert emb_lower.shape == (384,)
        assert emb_mixed.shape == (384,)
    
    def test_embedding_dimension_consistency(self, real_embedding_service):
        words = ["cat", "dog", "bird", "fish", "tree"]
        embeddings = real_embedding_service.encode(words)
        
        for i, embedding in enumerate(embeddings):
            assert embedding.shape == (384,), f"Word {words[i]} has wrong dimension"
    
    def test_batch_encoding_performance(self, real_embedding_service):
        words = ["cat", "dog", "bird", "fish", "tree", "flower", "car", "house"]
        embeddings = real_embedding_service.encode(words)
        
        assert embeddings.shape[0] == len(words)
        assert embeddings.shape[1] == 384
        
        for i, embedding in enumerate(embeddings):
            assert not np.isnan(embedding).any(), f"Embedding {i} contains NaN"
            assert not np.isinf(embedding).any(), f"Embedding {i} contains Inf"