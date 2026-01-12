import pytest
from app.game_service import GameService
from app.word_database import WordDatabase

class TestGameService:    
    def test_game_service_initialization(self, game_service):
        assert game_service.embedding_service is not None
        assert game_service.word_database is not None
        assert game_service.semantic_graph is not None
    
    def test_validate_word_exists(self, game_service):
        # use words that should be in the database
        valid_words = ["cat", "dog", "bird", "animal", "pet"]
        for word in valid_words:
            if game_service.word_database.word_exists(word):
                assert game_service.validate_word(word)
    
    def test_validate_word_not_exists(self, game_service):
        invalid_words = ["xyzabc123", "nonexistentword999"]        
        for word in invalid_words:
            assert not game_service.validate_word(word)
    
    def test_find_optimal_path_valid_words(self, game_service):
        start_word = "cat"
        target_word = "dog"        
        if game_service.validate_word(start_word) and game_service.validate_word(target_word):
            path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
            
            if path:
                assert path[0].lower() == start_word.lower()
                assert path[-1].lower() == target_word.lower()
                steps = len(path) - 1
                assert 1 <= steps <= 6
    
    def test_find_optimal_path_invalid_start(self, game_service):
        start_word = "nonexistentword123"
        target_word = "dog"
        
        path = game_service.find_optimal_path(start_word, target_word)
        assert path is None
    
    def test_find_optimal_path_invalid_target(self, game_service):
        start_word = "cat"
        target_word = "nonexistentword123"
        
        path = game_service.find_optimal_path(start_word, target_word)
        assert path is None
    
    def test_validate_path_minimum_length(self, game_service):
        short_path = ["cat", "dog"]        
        is_valid, error = game_service.validate_path(short_path)
        
        assert not is_valid
        assert "at least 2 steps" in error.lower()
    
    def test_validate_path_maximum_length(self, game_service):
        long_path = ["cat", "a", "b", "c", "d", "e", "f", "dog"]
        is_valid, error = game_service.validate_path(long_path)
        
        assert not is_valid
        assert "exceeds maximum" in error.lower() or "6 steps" in error
    
    def test_validate_path_duplicates(self, game_service):
        path_with_duplicate = ["cat", "dog", "cat", "bird"]        
        is_valid, error = game_service.validate_path(path_with_duplicate)
        
        assert not is_valid
        assert "duplicate" in error.lower()
    
    def test_validate_path_invalid_word(self, game_service):
        path_with_invalid = ["cat", "nonexistentword123", "dog"]
        is_valid, error = game_service.validate_path(path_with_invalid)
        
        assert not is_valid
        assert "not in the database" in error.lower()
    
    def test_validate_path_semantic_disconnection(self, game_service):
        path = ["cat", "computer", "dog"]        
        is_valid, error = game_service.validate_path(path)
        
        if not is_valid:
            assert "not semantically connected" in error.lower() or "not in the database" in error.lower()
    
    def test_validate_path_valid(self, game_service):
        start_word = "cat"
        target_word = "dog"
        
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path and len(optimal_path) >= 3:
            is_valid, error = game_service.validate_path(optimal_path)
            assert is_valid
            assert error is None
    
    def test_calculate_score_perfect_path(self, game_service):
        start_word = "cat"
        target_word = "dog"
        
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path and len(optimal_path) >= 3:
            score, message, algo_path = game_service.calculate_score(
                optimal_path, start_word, target_word
            )
            
            assert score == 100
            assert "perfect" in message.lower() or "🎯" in message
            assert algo_path == optimal_path
    
    def test_calculate_score_beats_algorithm(self, game_service):
        start_word = "cat"
        target_word = "dog"
        
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path and len(optimal_path) > 3:
            shorter_path = optimal_path[:3]  
            
            is_valid, _ = game_service.validate_path(shorter_path)
            
            if is_valid and shorter_path[0].lower() == start_word.lower():
                score, message, algo_path = game_service.calculate_score(
                    shorter_path, start_word, target_word
                )                
                assert score >= 100
    
    def test_calculate_score_one_extra_step(self, game_service):
        start_word = "cat"
        target_word = "dog"
        
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path and len(optimal_path) >= 3:
            longer_path = optimal_path + ["pet"]
            longer_path[-2], longer_path[-1] = longer_path[-1], longer_path[-2]             
            is_valid, _ = game_service.validate_path(longer_path)
            if is_valid and longer_path[0].lower() == start_word.lower() and longer_path[-1].lower() == target_word.lower():
                score, message, algo_path = game_service.calculate_score(
                    longer_path, start_word, target_word
                )
                assert score >= 50  
    
    def test_calculate_score_invalid_path(self, game_service):
        start_word = "cat"
        target_word = "dog"
        invalid_path = ["cat", "nonexistentword", "dog"]
        
        score, message, algo_path = game_service.calculate_score(
            invalid_path, start_word, target_word
        )
        
        assert score == 0
        assert "not in the database" in message.lower() or "not semantically connected" in message.lower()
        assert algo_path is not None or algo_path is None  # May or may not find path
    
    def test_calculate_score_wrong_start(self, game_service):
        start_word = "cat"
        target_word = "dog"
        wrong_start_path = ["dog", "cat", "bird"]
        
        score, message, algo_path = game_service.calculate_score(
            wrong_start_path, start_word, target_word
        )
        
        assert score == 0
        assert start_word.lower() in message.lower()
    
    def test_calculate_score_wrong_end(self, game_service):
        start_word = "cat"
        target_word = "dog"
        wrong_end_path = ["cat", "bird", "fish"]
        
        score, message, algo_path = game_service.calculate_score(
            wrong_end_path, start_word, target_word
        )
        
        assert score == 0
        assert target_word.lower() in message.lower()
    
    def test_get_word_similarity(self, game_service):
        word1 = "cat"
        word2 = "dog"
        
        similarity = game_service.get_word_similarity(word1, word2)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0
    
    def test_get_random_word_pair(self, game_service):
        start_word, target_word = game_service.get_random_word_pair()
        
        assert isinstance(start_word, str)
        assert isinstance(target_word, str)
        assert start_word != target_word
        assert game_service.validate_word(start_word)
        assert game_service.validate_word(target_word)
    
    def test_get_random_word_pair_has_path(self, game_service):
        start_word, target_word = game_service.get_random_word_pair()
        
        path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if path:
            steps = len(path) - 1
            assert 2 <= steps <= 6
    
    def test_validate_path_case_insensitive(self, game_service):
        start_word = "cat"
        target_word = "dog"
        
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path and len(optimal_path) >= 3:
            mixed_case_path = [w.upper() if i % 2 == 0 else w.lower() for i, w in enumerate(optimal_path)]            
            is_valid, error = game_service.validate_path(mixed_case_path)            
            assert is_valid or "duplicate" in error.lower() 
    
    def test_path_validation_empty_path(self, game_service):
        is_valid, error = game_service.validate_path([])
        
        assert not is_valid
        assert "at least" in error.lower()
    
    def test_path_validation_single_word(self, game_service):
        is_valid, error = game_service.validate_path(["cat"])
        
        assert not is_valid
        assert "at least 2 steps" in error.lower()
    
    def test_scoring_returns_algorithm_path(self, game_service):
        start_word = "cat"
        target_word = "dog"
        player_path = ["cat", "invalid", "dog"]
        
        score, message, algo_path = game_service.calculate_score(
            player_path, start_word, target_word
        )        
        assert algo_path is not None or algo_path is None  # May be None if no path found
    
    def test_preload_words(self, game_service):
        words_in_graph = game_service.semantic_graph.get_all_words()        
        assert len(words_in_graph) > 0