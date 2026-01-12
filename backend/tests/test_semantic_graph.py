import pytest
import numpy as np
from app.semantic_graph import SemanticGraph

class TestSemanticGraph:
    def test_graph_initialization(self, semantic_graph):
        assert semantic_graph.similarity_threshold == 0.49
        assert semantic_graph.word_embeddings == {}
        assert len(semantic_graph.graph) == 0
    
    def test_add_single_word(self, semantic_graph):
        word = "cat"
        embedding = semantic_graph.add_word(word)
        
        assert word in semantic_graph.word_embeddings
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
    
    def test_add_duplicate_word(self, semantic_graph):
        word = "cat"
        embedding1 = semantic_graph.add_word(word)
        embedding2 = semantic_graph.add_word(word)
        
        np.testing.assert_array_equal(embedding1, embedding2)
        assert len(semantic_graph.word_embeddings) == 1
    
    def test_add_multiple_words(self, semantic_graph):
        words = ["cat", "dog", "bird"]
        embeddings = semantic_graph.add_words(words)
        
        assert len(embeddings) == 3
        for word in words:
            assert word in semantic_graph.word_embeddings
    
    def test_word_exists(self, semantic_graph):
        word = "cat"
        assert not semantic_graph.word_exists(word)
        
        semantic_graph.add_word(word)
        assert semantic_graph.word_exists(word)
    
    def test_get_all_words(self, semantic_graph):
        words = ["cat", "dog", "bird"]
        semantic_graph.add_words(words)
        
        all_words = semantic_graph.get_all_words()
        assert len(all_words) == 3
        for word in words:
            assert word in all_words
    
    def test_cosine_similarity_calculation(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        
        vec1 = semantic_graph.word_embeddings[word1]
        vec2 = semantic_graph.word_embeddings[word2]
        
        similarity = semantic_graph.cosine_similarity(vec1, vec2)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0
    
    def test_get_similarity(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        similarity = semantic_graph.get_similarity(word1, word2)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0
        assert word1 in semantic_graph.word_embeddings
        assert word2 in semantic_graph.word_embeddings
    
    def test_similarity_caching(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        similarity1 = semantic_graph.get_similarity(word1, word2)
        similarity2 = semantic_graph.get_similarity(word1, word2)
        
        assert similarity1 == similarity2
        cache_key = tuple(sorted([word1, word2]))
        assert cache_key in semantic_graph.similarity_cache
    
    def test_are_connected_high_similarity(self, semantic_graph):
        word1 = "cat"
        word2 = "kitten"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)        
        similarity = semantic_graph.get_similarity(word1, word2)
        if similarity >= semantic_graph.similarity_threshold:
            assert semantic_graph.are_connected(word1, word2)
    
    def test_are_connected_low_similarity(self, semantic_graph):
        word1 = "cat"
        word2 = "computer"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        
        similarity = semantic_graph.get_similarity(word1, word2)
        connected = semantic_graph.are_connected(word1, word2)
        
        assert connected == (similarity >= semantic_graph.similarity_threshold)
    
    def test_get_neighbors(self, semantic_graph):
        words = ["cat", "dog", "bird"]
        semantic_graph.add_words(words)
        
        neighbors = semantic_graph.get_neighbors("cat")        
        assert isinstance(neighbors, set)
        for neighbor in neighbors:
            assert neighbor in semantic_graph.word_embeddings
    
    def test_neighbors_are_bidirectional(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        
        if semantic_graph.are_connected(word1, word2):
            neighbors1 = semantic_graph.get_neighbors(word1)
            neighbors2 = semantic_graph.get_neighbors(word2)
            assert word2 in neighbors1
            assert word1 in neighbors2
    
    def test_bfs_path_same_word(self, semantic_graph):
        word = "cat"
        semantic_graph.add_word(word)
        
        path = semantic_graph.bfs_path(word, word)
        assert path == [word]
    
    def test_bfs_path_direct_connection(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        if semantic_graph.are_connected(word1, word2):
            path = semantic_graph.bfs_path(word1, word2)
            assert path == [word1, word2]
    
    def test_bfs_path_multi_step(self, semantic_graph):
        words = ["cat", "animal", "dog"]
        semantic_graph.add_words(words)

        path = semantic_graph.bfs_path("cat", "dog", max_steps=6)        
        if path:
            assert path[0] == "cat"
            assert path[-1] == "dog"
            assert len(path) <= 7 
    
    def test_bfs_path_respects_max_steps(self, semantic_graph):
        words = ["cat", "dog", "bird", "fish", "tree", "flower", "car", "house"]
        semantic_graph.add_words(words)
        
        path = semantic_graph.bfs_path("cat", "house", max_steps=3)
        
        if path:
            steps = len(path) - 1
            assert steps <= 3
    
    def test_bfs_path_no_path_found(self, semantic_graph):
        word1 = "cat"
        word2 = "computer"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        
        path = semantic_graph.bfs_path(word1, word2, max_steps=6)        
        if path is None:
            assert not semantic_graph.are_connected(word1, word2)
    
    def test_batch_update_connections(self, semantic_graph):
        existing_words = ["cat", "dog"]
        new_words = ["bird", "fish"]
        
        semantic_graph.add_words(existing_words)
        semantic_graph.add_words(new_words)        
        assert len(semantic_graph.word_embeddings) == 4
        
        for word in new_words:
            neighbors = semantic_graph.get_neighbors(word)
            assert isinstance(neighbors, set)
    
    def test_case_insensitive_operations(self, semantic_graph):
        word_upper = "CAT"
        word_lower = "cat"
        
        semantic_graph.add_word(word_upper)
        assert semantic_graph.word_exists(word_lower)
        assert word_lower in semantic_graph.word_embeddings
    
    def test_similarity_threshold_affects_connections(self, semantic_graph):
        word1 = "cat"
        word2 = "dog"
        
        semantic_graph.add_word(word1)
        semantic_graph.add_word(word2)
        
        similarity = semantic_graph.get_similarity(word1, word2)
        connected = semantic_graph.are_connected(word1, word2)
        assert connected == (similarity >= semantic_graph.similarity_threshold)
    
    def test_graph_scales_with_many_words(self, semantic_graph):
        words = [f"word{i}" for i in range(50)]
        semantic_graph.add_words(words)
        
        assert len(semantic_graph.word_embeddings) == 50        
        neighbors = semantic_graph.get_neighbors("word0")
        assert isinstance(neighbors, set)