# setting up flask

from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    
    # Enable CORS for frontend communication
    CORS(app)
    
    # Register blueprints to make the app modular
    from app.routes import game_bp
    app.register_blueprint(game_bp)
    
    return app