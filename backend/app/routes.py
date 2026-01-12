# API routes for the game
from flask import Blueprint, jsonify, request
from app.game_service import GameService
import logging

logger = logging.getLogger(__name__)

game_bp = Blueprint('game', __name__)

# Initialize game service (singleton pattern)
_game_service = None

def get_game_service():
    # lazy initialization of game service
    global _game_service
    if _game_service is None:
        _game_service = GameService()
    return _game_service


@game_bp.route('/health', methods=['GET'])
def health_check():
    # game health check
    return jsonify({'status': 'ok'}), 200

@game_bp.route('/game/new', methods=['GET'])
def new_game():
    # get a new game with random word pair
    try:
        game_service = get_game_service()
        start_word, target_word = game_service.get_random_word_pair()
        
        return jsonify({
            'success': True,
            'startWord': start_word,
            'targetWord': target_word
        }), 200
    except Exception as e:
        logger.error(f"Error creating new game: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@game_bp.route('/game/path', methods=['POST'])
def get_optimal_path():
    # get the algorithm's optimal path between two words
    try:
        data = request.get_json()
        start_word = data.get('startWord')
        target_word = data.get('targetWord')
        max_steps = data.get('maxSteps', 6)
        
        if not start_word or not target_word:
            return jsonify({
                'success': False,
                'error': 'startWord and targetWord are required'
            }), 400
        
        game_service = get_game_service()
        path = game_service.find_optimal_path(start_word, target_word, max_steps)
        
        if path is None:
            return jsonify({
                'success': False,
                'error': 'No path found within max steps',
                'path': None,
                'steps': None
            }), 404
        
        steps = len(path) - 1
        # Ensure path is within 2-6 steps range
        if steps < 2 or steps > 6:
            return jsonify({
                'success': False,
                'error': f'Path has {steps} steps, must be between 2-6 steps',
                'path': None,
                'steps': None
            }), 400
        
        return jsonify({
            'success': True,
            'path': path,
            'steps': steps
        }), 200
    except Exception as e:
        logger.error(f"Error finding path: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@game_bp.route('/game/validate', methods=['POST'])
def validate_word_in_chain():
    # validate a word in the chain (check if it can be added to current path)
    try:
        data = request.get_json()
        word = data.get('word')
        current_path = data.get('currentPath', [])
        start_word = data.get('startWord')
        full_path = data.get('fullPath', [])  # Frontend may send full path
        
        if not word:
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'Word is required'
            }), 400
        
        game_service = get_game_service()
        
        # validate word exists
        if not game_service.validate_word(word):
            return jsonify({
                'success': True,
                'valid': False,
                'error': f"Word '{word}' is not in the database"
            }), 200
        
        # Build full path for duplicate checking (including start word)
        if not full_path:
            full_path = [start_word] + current_path if start_word else current_path
        else:
            # Ensure we have start word in full path
            if start_word and start_word.lower() not in [w.lower() for w in full_path]:
                full_path = [start_word] + full_path
        
        # check if word is duplicate (including start word)
        if word.lower().strip() in [w.lower().strip() for w in full_path]:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Word already used in path'
            }), 200
        
        # if no current path, word is valid (it's the first word)
        if not current_path or len(current_path) == 0:
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Word is valid'
            }), 200
        
        # check semantic connection with last word in path
        last_word = current_path[-1].lower().strip()
        word_lower = word.lower().strip()
        
        # ensure words are in graph
        if not game_service.semantic_graph.word_exists(last_word):
            game_service.semantic_graph.add_word(last_word)
        if not game_service.semantic_graph.word_exists(word_lower):
            game_service.semantic_graph.add_word(word_lower)
        
        # check if semantically connected
        is_connected = game_service.semantic_graph.are_connected(last_word, word_lower)
        
        if is_connected:
            similarity = game_service.semantic_graph.get_similarity(last_word, word_lower)
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Word is valid and connected',
                'similarity': similarity
            }), 200
        else:
            similarity = game_service.semantic_graph.get_similarity(last_word, word_lower)
            return jsonify({
                'success': True,
                'valid': False,
                'error': f"Word '{word}' is not semantically connected to '{current_path[-1]}'",
                'similarity': similarity
            }), 200
    except Exception as e:
        logger.error(f"Error validating word: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'error': str(e)
        }), 500


@game_bp.route('/game/score', methods=['POST'])
def calculate_score():
    # calculate score for a player's path
    try:
        data = request.get_json()
        path = data.get('path', [])
        start_word = data.get('startWord')
        target_word = data.get('targetWord')
        
        if not path or not isinstance(path, list):
            return jsonify({
                'success': False,
                'error': 'Path must be a non-empty array'
            }), 400
        
        if not start_word or not target_word:
            return jsonify({
                'success': False,
                'error': 'startWord and targetWord are required'
            }), 400
        
        game_service = get_game_service()
        score, message, algorithm_path = game_service.calculate_score(path, start_word, target_word)
        
        # Always return optimal path, even if player path is invalid
        algorithm_steps = len(algorithm_path) - 1 if algorithm_path else None
        player_steps = len(path) - 1
        
        # Determine if path is valid: score > 0 means valid path
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


@game_bp.route('/game/submit', methods=['POST'])
def submit_chain():
    # submit completed chain (alias for /game/score)
    # same functionality as calculate_score
    return calculate_score()


@game_bp.route('/word/validate', methods=['POST'])
def validate_word():
    # validate if a word exists in the database
    try:
        data = request.get_json()
        word = data.get('word')
        
        if not word:
            return jsonify({
                'success': False,
                'error': 'Word is required'
            }), 400
        
        game_service = get_game_service()
        exists = game_service.validate_word(word)
        
        return jsonify({
            'success': True,
            'word': word,
            'exists': exists
        }), 200
    except Exception as e:
        logger.error(f"Error validating word: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@game_bp.route('/word/similarity', methods=['POST'])
def get_similarity():
    # get similarity between two words
    try:
        data = request.get_json()
        word1 = data.get('word1')
        word2 = data.get('word2')
        
        if not word1 or not word2:
            return jsonify({
                'success': False,
                'error': 'word1 and word2 are required'
            }), 400
        
        game_service = get_game_service()
        similarity = game_service.get_word_similarity(word1, word2)
        
        return jsonify({
            'success': True,
            'word1': word1,
            'word2': word2,
            'similarity': similarity,
            'connected': similarity >= game_service.semantic_graph.similarity_threshold
        }), 200
    except Exception as e:
        logger.error(f"Error getting similarity: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@game_bp.route('/game/hint', methods=['GET'])
def get_hint():
    # get hint for current puzzle
    try:
        start_word = request.args.get('startWord')
        target_word = request.args.get('targetWord')
        current_path = request.args.get('currentPath', '')
        
        if not start_word or not target_word:
            return jsonify({
                'success': False,
                'error': 'startWord and targetWord are required as query parameters'
            }), 400
        
        game_service = get_game_service()
      
        # parse current path if provided
        current_words = []
        if current_path:
            current_words = [w.strip() for w in current_path.split(',') if w.strip()]
        
        # get hint level (how many times user has asked for hint)
        hint_level = int(request.args.get('hintLevel', 1))

        # build full path including start word to check for duplicates
        full_path = [start_word.lower()] + [w.lower() for w in current_words]
        used_words = set(full_path)
        
        # determine current position
        if not current_words or len(current_words) == 0:
            # user hasn't started yet -> use start word
            current_position = start_word
        elif current_words[-1].lower() == target_word.lower():
            # already at target
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
            # use last word in current path
            current_position = current_words[-1]
        
        # Find optimal path FROM CURRENT POSITION to target
        optimal_from_here = game_service.find_optimal_path(current_position, target_word, max_steps=6)
        
        if optimal_from_here is None or len(optimal_from_here) < 2:
            return jsonify({
                'success': False,
                'error': f'No path found from {current_position} to {target_word}',
                'hint': None
            }), 404
        
        # hint word is the next word in the optimal path from current position
        # optimal_from_here[0] is current position, optimal_from_here[1] is the next word
        hint_word = None
        
        # find first word in optimal_from_here that hasn't been used yet
        for word in optimal_from_here[1:]:  # Skip the first word (current position)
            if word.lower() not in used_words:
                hint_word = word
                break
        
        # if all words in optimal path have been used, find a semantic neighbor
        if not hint_word:
            neighbors = list(game_service.semantic_graph.get_neighbors(current_position.lower()))
            if neighbors:
                # find neighbor closest to target that hasn't been used
                best_neighbor = None
                best_similarity = -1
                for neighbor in neighbors:
                    # skip if already used
                    if neighbor.lower() in used_words:
                        continue
                    sim = game_service.get_word_similarity(neighbor, target_word)
                    if sim > best_similarity:
                        best_similarity = sim
                        best_neighbor = neighbor
                hint_word = best_neighbor
        
        # generate letter reveal hints only
        masked_word = None
        word_length = None
        fully_revealed = False
        message = ""
        steps_remaining = len(optimal_from_here) - 1 if optimal_from_here else None
        
        if hint_word:
            word_length = len(hint_word)
            # progressive letter reveal based on hint level
            letters_to_reveal = min(hint_level, len(hint_word))
            
            if letters_to_reveal >= len(hint_word):
                # full reveal
                masked_word = hint_word.upper()
                fully_revealed = True
                message = f"The word is '{hint_word.upper()}'"
            else:
                # partial reveal
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


@game_bp.route('/stats', methods=['GET'])
def get_stats():
    # get game statistics
    try:
        game_service = get_game_service()
        
        # get basic stats
        total_words = game_service.word_database.get_word_count()
        words_in_graph = len(game_service.semantic_graph.get_all_words())
        
        return jsonify({
            'success': True,
            'stats': {
                'totalWords': total_words,
                'wordsInGraph': words_in_graph,
                'similarityThreshold': game_service.semantic_graph.similarity_threshold,
                'embeddingModel': game_service.embedding_service.model_name,
                'embeddingDimension': game_service.embedding_service.get_embedding_dim()
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500