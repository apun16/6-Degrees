import pytest
import json
from flask import Flask
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

class TestNewGameEndpoint:    
    def test_new_game_success(self, client):
        response = client.get('/api/game/new')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'startWord' in data
        assert 'targetWord' in data
        assert isinstance(data['startWord'], str)
        assert isinstance(data['targetWord'], str)
        assert data['startWord'] != data['targetWord']
    
    def test_new_game_returns_valid_words(self, client):
        response = client.get('/api/game/new')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # validate words exist
        validate_response = client.post('/api/word/validate', 
                                      json={'word': data['startWord']})
        assert json.loads(validate_response.data)['exists'] is True
        
        validate_response = client.post('/api/word/validate',
                                      json={'word': data['targetWord']})
        assert json.loads(validate_response.data)['exists'] is True

class TestPathEndpoint:
    def test_get_path_success(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)
        
        start_word = game_data['startWord']
        target_word = game_data['targetWord']
        
        response = client.post('/api/game/path',
                              json={
                                  'startWord': start_word,
                                  'targetWord': target_word,
                                  'maxSteps': 6
                              })
        
        assert response.status_code in [200, 404]  # May not find path
        
        data = json.loads(response.data)
        if data['success']:
            assert 'path' in data
            assert 'steps' in data
            if data['path']:
                assert len(data['path']) >= 2
                assert data['path'][0].lower() == start_word.lower()
                assert data['path'][-1].lower() == target_word.lower()
    
    def test_get_path_missing_params(self, client):
        response = client.post('/api/game/path', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'required' in data['error'].lower()
    
    def test_get_path_invalid_words(self, client):
        response = client.post('/api/game/path',
                              json={
                                  'startWord': 'nonexistentword123',
                                  'targetWord': 'anotherinvalid456'
                              })        
        assert response.status_code in [400, 404, 500]

class TestValidateWordEndpoint:
    def test_validate_word_exists(self, client):
        response = client.post('/api/game/validate',
                              json={
                                  'word': 'cat',
                                  'currentPath': [],
                                  'startWord': 'cat'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'valid' in data
    
    def test_validate_word_not_exists(self, client):
        response = client.post('/api/game/validate',
                              json={
                                  'word': 'nonexistentword123',
                                  'currentPath': [],
                                  'startWord': 'cat'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['valid'] is False
        assert 'not in the database' in data['error'].lower()
    
    def test_validate_word_duplicate(self, client):
        response = client.post('/api/game/validate',
                              json={
                                  'word': 'cat',
                                  'currentPath': ['cat'],
                                  'startWord': 'cat',
                                  'fullPath': ['cat', 'cat']
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['valid'] is False
        assert 'already used' in data['error'].lower()
    
    def test_validate_word_missing_params(self, client):
        response = client.post('/api/game/validate', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_validate_word_semantic_connection(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)        
        start_word = game_data['startWord']
        
        response = client.post('/api/game/validate',
                              json={
                                  'word': 'computer',
                                  'currentPath': [start_word],
                                  'startWord': start_word
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'valid' in data

class TestScoreEndpoint:
    def test_calculate_score_success(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)
        
        start_word = game_data['startWord']
        target_word = game_data['targetWord']
        
        path_response = client.post('/api/game/path',
                                   json={
                                       'startWord': start_word,
                                       'targetWord': target_word
                                   })
        path_data = json.loads(path_response.data)
        
        if path_data['success'] and path_data.get('path'):
            response = client.post('/api/game/score',
                                  json={
                                      'path': path_data['path'],
                                      'startWord': start_word,
                                      'targetWord': target_word
                                  })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'score' in data
            assert 'message' in data
            assert 'valid' in data
            assert 'algorithmPath' in data
            assert isinstance(data['score'], int)
            assert data['score'] >= 0
    
    def test_calculate_score_invalid_path(self, client):
        response = client.post('/api/game/score',
                              json={
                                  'path': ['cat', 'nonexistentword', 'dog'],
                                  'startWord': 'cat',
                                  'targetWord': 'dog'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['score'] == 0
        assert data['valid'] is False
    
    def test_calculate_score_missing_params(self, client):
        response = client.post('/api/game/score', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_calculate_score_returns_algorithm_path(self, client):
        response = client.post('/api/game/score',
                              json={
                                  'path': ['cat', 'invalid', 'dog'],
                                  'startWord': 'cat',
                                  'targetWord': 'dog'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'algorithmPath' in data

class TestSubmitEndpoint:
    def test_submit_chain(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)
        
        start_word = game_data['startWord']
        target_word = game_data['targetWord']
        
        response = client.post('/api/game/submit',
                              json={
                                  'path': [start_word, 'animal', target_word],
                                  'startWord': start_word,
                                  'targetWord': target_word
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'score' in data

class TestWordValidateEndpoint:
    def test_validate_word_exists(self, client):
        response = client.post('/api/word/validate',
                              json={'word': 'cat'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['exists'] is True
    
    def test_validate_word_not_exists(self, client):
        response = client.post('/api/word/validate',
                              json={'word': 'nonexistentword123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['exists'] is False
    
    def test_validate_word_missing_param(self, client):
        response = client.post('/api/word/validate', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

class TestSimilarityEndpoint:
    def test_get_similarity(self, client):
        response = client.post('/api/word/similarity',
                              json={
                                  'word1': 'cat',
                                  'word2': 'dog'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'similarity' in data
        assert 'connected' in data
        assert isinstance(data['similarity'], float)
        assert isinstance(data['connected'], bool)
        assert -1.0 <= data['similarity'] <= 1.0
    
    def test_get_similarity_missing_params(self, client):
        response = client.post('/api/word/similarity', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

class TestHintEndpoint:
    def test_get_hint_success(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)
        
        start_word = game_data['startWord']
        target_word = game_data['targetWord']
        
        response = client.get('/api/game/hint',
                            query_string={
                                'startWord': start_word,
                                'targetWord': target_word,
                                'hintLevel': 1
                            })
        
        assert response.status_code in [200, 404] 
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'hint' in data
            hint = data['hint']
            assert 'masked_word' in hint or hint.get('word') is None
            assert 'word_length' in hint or hint.get('word') is None
    
    def test_get_hint_missing_params(self, client):
        response = client.get('/api/game/hint')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_hint_with_current_path(self, client):
        game_response = client.get('/api/game/new')
        game_data = json.loads(game_response.data)
        
        start_word = game_data['startWord']
        target_word = game_data['targetWord']
        
        response = client.get('/api/game/hint',
                            query_string={
                                'startWord': start_word,
                                'targetWord': target_word,
                                'currentPath': 'cat',
                                'hintLevel': 1
                            })
        
        assert response.status_code in [200, 404]

class TestStatsEndpoint:
    def test_get_stats(self, client):
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'stats' in data
        stats = data['stats']
        assert 'totalWords' in stats
        assert 'wordsInGraph' in stats
        assert 'similarityThreshold' in stats
        assert 'embeddingModel' in stats
        assert 'embeddingDimension' in stats