from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.game_service import GameService
from app.word_database import WordDatabase
from app.embedding_service import EmbeddingService
from app.semantic_graph import SemanticGraph
import logging

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize game service (singleton pattern for Vercel)
_game_service = None

def get_game_service():
    global _game_service
    if _game_service is None:
        _game_service = GameService(similarity_threshold=0.49)
    return _game_service

@app.route('/api/game/new', methods=['GET'])
def get_new_game():
    try:
        game_service = get_game_service()
        start_word, target_word = game_service.get_random_word_pair()
        optimal_path = game_service.find_optimal_path(start_word, target_word, max_steps=6)
        
        if optimal_path is None:
            return jsonify({
                'success': False,
                'error': 'Could not generate valid puzzle'
            }), 500
        
        return jsonify({
            'success': True,
            'puzzle': {
                'start_word': start_word,
                'end_word': target_word,
                'optimal_length': len(optimal_path) - 1
            }
        }), 200
    except Exception as e:
        logger.error(f"Error generating new game: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/game/validate', methods=['POST'])
def validate_word():
    try:
        data = request.get_json()
        word = data.get('word')
        current_word = data.get('currentWord')
        full_path = data.get('fullPath', [])
        
        if not word or not current_word:
            return jsonify({
                'success': False,
                'error': 'word and currentWord are required'
            }), 400
        
        game_service = get_game_service()
        
        # Check if word exists in database
        if not game_service.word_database.word_exists(word):
            return jsonify({
                'success': False,
                'error': f"Word '{word.upper()}' is not in the database"
            }), 400
        
        # Check for duplicates in full path
        word_lower = word.lower().strip()
        if word_lower in [w.lower() for w in full_path]:
            return jsonify({
                'success': False,
                'error': 'This word has already been used'
            }), 400
        
        # Check connection
        if not game_service.are_words_connected(current_word, word):
            similarity = game_service.get_word_similarity(current_word, word)
            return jsonify({
                'success': False,
                'error': f'Not connected to {current_word.upper()} (similarity: {similarity:.2f})',
                'similarity': similarity
            }), 400
        
        return jsonify({
            'success': True,
            'word': word,
            'connected': True
        }), 200
    except Exception as e:
        logger.error(f"Error validating word: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/game/hint', methods=['GET'])
def get_hint():
    try:
        start_word = request.args.get('startWord')
        target_word = request.args.get('targetWord')
        current_path = request.args.get('currentPath', '')
        
        if not start_word or not target_word:
            return jsonify({
                'success': False,
                'error': 'startWord and targetWord are required'
            }), 400
        
        game_service = get_game_service()
        
        current_words = []
        if current_path:
            current_words = [w.strip() for w in current_path.split(',') if w.strip()]
        
        hint_level = int(request.args.get('hintLevel', 1))
        
        full_path = [start_word.lower()] + [w.lower() for w in current_words]
        used_words = set(full_path)
        
        if not current_words or len(current_words) == 0:
            current_position = start_word
        elif current_words[-1].lower() == target_word.lower():
            return jsonify({
                'success': True,
                'hint': {
                    'word': None,
                    'message': "You've reached the target word!",
                    'masked_word': None,
                    'word_length': None,
                    'fully_revealed': False,
                    'optimalPathLength': 0,
                    'hint_level': hint_level
                }
            }), 200
        else:
            current_position = current_words[-1]
        
        optimal_from_here = game_service.find_optimal_path(current_position, target_word, max_steps=6)
        
        if optimal_from_here is None or len(optimal_from_here) < 2:
            return jsonify({
                'success': False,
                'error': f'No path found from {current_position} to {target_word}'
            }), 404
        
        hint_word = None
        for word in optimal_from_here[1:]:
            if word.lower() not in used_words:
                hint_word = word
                break
        
        if not hint_word:
            neighbors = list(game_service.semantic_graph.get_neighbors(current_position.lower()))
            if neighbors:
                best_neighbor = None
                best_similarity = -1
                for neighbor in neighbors:
                    if neighbor.lower() in used_words:
                        continue
                    sim = game_service.get_word_similarity(neighbor, target_word)
                    if sim > best_similarity:
                        best_similarity = sim
                        best_neighbor = neighbor
                hint_word = best_neighbor
        
        masked_word = None
        word_length = None
        fully_revealed = False
        message = ""
        steps_remaining = len(optimal_from_here) - 1 if optimal_from_here else None
        
        if hint_word:
            word_length = len(hint_word)
            letters_to_reveal = min(hint_level, len(hint_word))
            
            if letters_to_reveal >= len(hint_word):
                masked_word = hint_word.upper()
                fully_revealed = True
                message = f"The word is '{hint_word.upper()}'"
            else:
                revealed = hint_word[:letters_to_reveal].upper()
                hidden = '_' * (len(hint_word) - letters_to_reveal)
                masked_word = revealed + hidden
                message = f"Revealing {letters_to_reveal} letter{'s' if letters_to_reveal > 1 else ''}"
        else:
            message = "Continue towards the target word"
        
        return jsonify({
            'success': True,
            'hint': {
                'word': hint_word,
                'message': message,
                'masked_word': masked_word,
                'word_length': word_length,
                'fully_revealed': fully_revealed,
                'steps_remaining': steps_remaining,
                'hint_level': hint_level
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting hint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/game/score', methods=['POST'])
def calculate_score():
    try:
        data = request.get_json()
        path = data.get('path', [])
        start_word = data.get('startWord')
        target_word = data.get('targetWord')
        
        if not start_word or not target_word:
            return jsonify({
                'success': False,
                'error': 'startWord and targetWord are required'
            }), 400
        
        game_service = get_game_service()
        score, message, algorithm_path = game_service.calculate_score(path, start_word, target_word)
        
        algorithm_steps = len(algorithm_path) - 1 if algorithm_path else None
        player_steps = len(path) - 1
        
        is_valid = score > 0
        
        return jsonify({
            'success': True,
            'score': score,
            'message': message,
            'valid': is_valid,
            'algorithmPath': algorithm_path,
            'playerSteps': player_steps,
            'algorithmSteps': algorithm_steps
        }), 200
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel handler
def handler(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()
