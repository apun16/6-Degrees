import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from app.embedding_service import EmbeddingService
from app.semantic_graph import SemanticGraph
from app.game_service import GameService
from app.word_database import WordDatabase

# import warnings
# warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for faster tests"""
    mock_service = Mock(spec=EmbeddingService)
    mock_service.embedding_dim = 384
    
    # create deterministic mock embeddings
    def create_mock_embedding(word):
        # create a deterministic embedding based on word hash
        np.random.seed(hash(word) % 1000)
        embedding = np.random.rand(384).astype(np.float32)
        # normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def encode_word(word):
        return create_mock_embedding(word)
    
    def encode(words):
        if isinstance(words, str):
            words = [words]
        return np.array([create_mock_embedding(w) for w in words])
    
    mock_service.encode_word.side_effect = encode_word
    mock_service.encode.side_effect = encode
    mock_service.get_embedding_dim.return_value = 384
    
    return mock_service

@pytest.fixture
def real_embedding_service():
    return EmbeddingService()

@pytest.fixture
def semantic_graph(mock_embedding_service):
    return SemanticGraph(mock_embedding_service, similarity_threshold=0.49)

@pytest.fixture
def real_semantic_graph(real_embedding_service):
    return SemanticGraph(real_embedding_service, similarity_threshold=0.49)

@pytest.fixture
def game_service(mock_embedding_service):
    return GameService(similarity_threshold=0.49)

@pytest.fixture
def real_game_service(real_embedding_service):
    return GameService(similarity_threshold=0.49)

@pytest.fixture
def sample_words():
    return ['cat', 'dog', 'animal', 'pet', 'bird', 'fish', 'tree', 'flower']

@pytest.fixture
def connected_word_pairs():
    return [
        ('cat', 'animal'),
        ('dog', 'animal'),
        ('bird', 'animal'),
        ('pet', 'animal'),
        ('tree', 'plant'),
        ('flower', 'plant'),
    ]

@pytest.fixture
def disconnected_word_pairs():
    return [
        ('cat', 'tree'),
        ('dog', 'flower'),
        ('bird', 'computer'),
    ]