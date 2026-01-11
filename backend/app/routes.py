# API routes for the game
from flask import Blueprint, jsonify, request

game_bp = Blueprint('game', __name__)


@game_bp.route('/health', methods=['GET'])
def health_check():
    # game health check
    return jsonify({'status': 'ok'}), 200
