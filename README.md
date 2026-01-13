# 6° Degrees

![6 Degrees Demo](./docs/6-Degrees_DEMO%20(1).gif)

A semantic word connection game where players find paths between any two words in six steps or less. 

Check it out here: [https://play6degrees.com/](https://play6degrees.com/)

## 💡 Inspiration

The game is inspired by the idea that any two people in the world are connected by at most six social connections. I discovered I was only a few connections away from people I never imagined, and this sparked the idea: *what if we applied this concept to words?*

Every word links to another through meaning. "Heart" connects to "love," which connects to "family," which connects to "home." The challenge is finding these semantic bridges in six steps or less. 

## 📋 Game Rules

1. **Objective**: Connect the start word to the goal word using related words (ex: similar theme, synonyms, etc)
2. **Path Length**: Your path must take a maximum of 6 steps from start to end
3. **No Duplicates**: You cannot use the same word twice in a path
4. **Real-time Validation**: Words are validated as you add them—invalid connections are rejected immediately
5. **Scoring**: 
   - 🤖 Beat the algorithm: 120 points
   - 🎯 Perfect match: 100 points
   - +1 extra step: 90 points
   - +2 extra steps: 80 points
   - +3 extra steps: 60 points
   - Completed (longer): 50 points

## ⚙️ Features

- **Semantic Word Connections**: Uses Hugging Face's all-MiniLM-L6-v2 sentence transformer model to generate 384-dimensional embeddings and determine word relationships through cosine similarity
- **Progressive Hints**: Letter-by-letter reveals to help players when stuck
- **Optimal Path Finding**: Breadth First Search algorithm finds the shortest semantic path between words
- **Score Comparison**: Compare your path length against the optimal algorithm path
- **Share Results**: Share your game results via native share API or copy to clipboard

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16.1.1
- **Language**: TypeScript + JavaScript
- **Styling**: CSS
- **Testing**: Jest + React Testing Library
- **Analytics**: Vercel Analytics & Speed Insights
- **Deployment**: Vercel

### Backend
- **Framework**: Flask 3.0.0
- **Language**: Python 3.9+
- **ML Models**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Deep Learning**: PyTorch 2.5.0 (CPU-only)
- **Server**: Gunicorn
- **Testing**: pytest + pytest-cov
- **Deployment**: Railway.app (Docker)

### Infrastructure & Tools
- **Database**: Supabase (PostgreSQL)
- **CI/CD**: GitHub Actions
- **Containerization**: Docker
- **Version Control**: Git

## 🏗️ Architecture

### Core Components

1. **Embedding Service**: Generates 384-dimensional word embeddings using Sentence Transformers
2. **Semantic Graph**: Builds an implicit graph where edges represent semantic similarity above threshold
3. **Game Service**: Orchestrates game logic, path validation, and scoring
4. **Word Database**: Manages valid words for the game
5. **API Routes**: RESTful endpoints for game operations

### Design Philosophy

**Why Semantic Embeddings Instead of Manual Database?**

Traditional word games rely on manually curated word lists and predefined connections. I found that this approach has several limitations:

1. Manual curation doesn't scale—adding new words requires manual connection mapping
2. Human-curated connections may not reflect how words are actually used
3. Impossible to pre-compute all possible word relationships
4. Requires constant updates as language evolves

**New Approach:**
- Words are connected based on semantic similarity, computed on the go. Uses state-of-the-art sentence transformers trained on millions of text pairs
- Adding new words automatically computes their relationships with existing words
- Similarity scores provide consistent, data-driven connections
- Threshold-based system allows fine-tuning of connection strength

The semantic graph is built dynamically: when a word is added, its embedding is generated and compared against all existing words. Words with cosine similarity ≥ 0.45 are considered connected, creating an implicit graph structure that grows organically.

**Threshold Determination (0.45):**

The similarity threshold of 0.45 was determined through iterative experimentation and testing with various word pairs:

- **Too Low (< 0.40)**: Created overly connected graphs where unrelated words were linked (e.g., "coyote" connected to "willow"), making the game too easy and paths trivial
- **Too High (> 0.50)**: Created sparse graphs where semantically related words weren't connected (e.g., "joy" disconnected from "harmony"), making many puzzles unsolvable
- **Optimal (0.45)**: Was balanced so that it:
  - Maintains strong semantic relationships (e.g., "coyote" → "wolf", "joy" → "harmony")
  - Filters weak associations (e.g., "coyote" ✗ "willow")
  - Ensures most word pairs have solvable paths within 6 steps
  - Provides appropriate challenge level for players

This threshold was validated through testing with hundreds of word pairs, so that the game remains playable while maintaining semantic integrity. The value allows for creative word connections while preventing unrelated paths. 


## 📡 API Routes

### Game Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/warmup` | Pre-initialize game service |
| `GET` | `/api/game/new` | Get a new game puzzle (random word pair) |
| `POST` | `/api/game/path` | Get optimal path between two words |
| `POST` | `/api/game/validate` | Validate if a word can be added to current path |
| `POST` | `/api/game/score` | Calculate score for a completed path |
| `POST` | `/api/game/submit` | Submit a completed path |
| `GET` | `/api/game/hint` | Get progressive hint (letter reveals) |

### Word Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/word/validate` | Check if word exists in database |
| `POST` | `/api/word/similarity` | Get similarity score between two words |

### Stats Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Get game statistics |

## 📁 File Structure
```
Six-Degrees-1/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app initialization
│   │   ├── embedding_service.py # Word embedding generation
│   │   ├── game_service.py      # Game logic orchestration
│   │   ├── routes.py             # API route handlers
│   │   ├── semantic_graph.py     # Graph structure & BFS pathfinding
│   │   └── word_database.py      # Word list management
│   ├── tests/
│   │   ├── conftest.py           # Pytest fixtures
│   │   ├── test_embedding_service.py
│   │   ├── test_game_service.py
│   │   ├── test_routes.py
│   │   └── test_semantic_graph.py
│   ├── Dockerfile                # Docker configuration
│   ├── Procfile                  # Railway deployment config
│   ├── requirements.txt          # Python dependencies
│   └── run.py                    # Application entry point
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Root layout (Analytics)
│   │   │   ├── page.tsx          # Main game page
│   │   │   └── index.css         # Global styles
│   │   ├── components/
│   │   │   ├── Game.jsx          # Main game component
│   │   │   ├── WordChain.jsx     # Word chain visualization
│   │   │   ├── WordInput.jsx     # Word input field
│   │   │   ├── Results.jsx       # Results display
│   │   │   ├── Landing.jsx       # Landing page
│   │   │   ├── HowToPlay.jsx     # Instructions modal
│   │   │   └── GitHubIcon.jsx    # GitHub link component
│   │   ├── styles/               # CSS Modules
│   │   ├── utils/
│   │   │   ├── api.js            # API client
│   │   │   └── supabase.js       # Supabase integration
│   │   └── tests/                # Jest test files
│   ├── jest.config.js            # Jest configuration
│   ├── package.json              # Node dependencies
│   └── next.config.ts            # Next.js configuration
│
├── .github/
│   └── workflows/
│       ├── test-frontend.yml      # Frontend CI/CD
│       └── test-backend.yml       # Backend CI/CD
│
└── README.md                     # This file
```

## 🧪 Testing

### Frontend Tests (Jest)

- **Game State Management**: Tests for word addition, removal, submission
- **API Integration**: Mock API responses and error handling
- **Path Validation**: Input validation and path building logic
- **Score Rendering**: Results component display logic

Run tests:
```bash
cd frontend
npm test
npm run test:coverage
```

### Backend Tests (Pytest)

- **Embedding Service**: Embedding generation, normalization, batch encoding
- **Semantic Graph**: Graph construction, neighbor finding, BFS pathfinding
- **Game Service**: Path validation, scoring, optimal path finding
- **API Routes**: Endpoint responses, error handling, request validation

Run tests:
```bash
cd backend
source venv/bin/activate
pytest
pytest --cov=app
```

### CI/CD

GitHub Actions automatically runs tests on:
- Push to `main` branch
- Pull requests

Both frontend and backend test suites must pass for deployments.

## 🚀 Deployment

### Frontend (Vercel)

- **URL**: https://play6degrees.com/
- **Build Command**: `cd frontend && npm run build`
- **Root Directory**: `frontend`
- **Environment Variables**: 
  - `NEXT_PUBLIC_API_URL`: Backend API URL

### Backend (Railway)

- **Platform**: Railway.app
- **Root Directory**: `backend`
- **Build**: Docker-based
- **Optimizations**:
  - Pre-downloads ML model during Docker build
  - CPU-only PyTorch to reduce image size (5.9GB → ~2GB)
  - Gunicorn with `--preload` flag for faster cold starts
  - Pre-loads 400 common words into graph on startup

## 📊 Performance Optimizations

1. **Model Pre-loading**: ML model downloaded during Docker build, not at runtime
2. **Word Pre-loading**: 400 common words pre-loaded into semantic graph
3. **Batch Operations**: Words added in batches for efficient graph construction
4. **Similarity Caching**: Cosine similarity scores cached to avoid recomputation
5. **Lazy Initialization**: Game service initialized once with `--preload` flag
6. **CDN**: Static assets served via Vercel CDN

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feedback and contributions are welcome! If you have suggestions, bug reports, or feature requests, please open an issue or submit a pull request.

**Try it out here:** [https://play6degrees.com/](https://play6degrees.com/)

**Have feedback?** I want to periodically update this app based on user input so please reach out with any suggestions!

---
