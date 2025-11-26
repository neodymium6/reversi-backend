# Reversi Backend

A high-performance REST API backend for Reversi (Othello) game built with FastAPI and Rust.

## Features

- High-performance game logic powered by **[rust-reversi](https://github.com/neodymium6/rust_reversi)** library
- RESTful API with FastAPI
- In-memory game session management
- **Automatic garbage collection** - inactive games are automatically cleaned up
- AI player support with multiple difficulty levels
  - Random move player
  - Alpha-beta search with configurable depth
  - Extensible architecture for custom AI players
- **AI Statistics** - Track AI performance with detailed statistics
  - Win/loss/draw counts and win rates
  - Performance by color (black/white)
  - Average score tracking
  - PostgreSQL database for persistent storage
- Automatic pass handling (when a player has no legal moves)
- Game over detection with winner calculation
- CORS support for frontend integration
- Comprehensive test coverage with pytest

## Tech Stack

- **FastAPI** - Modern Python web framework
- **[rust-reversi](https://github.com/neodymium6/rust_reversi)** - Rust-based Reversi game engine for optimal performance
- **PostgreSQL** - Database for persistent game statistics
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migration tool
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server
- **pytest** - Testing framework

## Prerequisites

- Python 3.10 or higher (not required if using Docker)
- PostgreSQL 12 or higher (or use Docker Compose)
- Docker (optional, for containerized deployment)

## Docker

Pre-built Docker images are available at [ghcr.io/neodymium6/reversi-backend](https://github.com/neodymium6/reversi-backend/pkgs/container/reversi-backend).

For Docker Compose examples and usage instructions, see the [examples/](examples/) directory.

## Setup

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Set up PostgreSQL database

Using Docker Compose (recommended for development):
```bash
docker compose up -d db
```

Or install PostgreSQL manually and create a database:
```bash
createdb reversi
```

### 3. Configure environment variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and configure the database URL and other settings:
```env
DATABASE_URL=postgresql://reversi:reversi@localhost:5432/reversi
FRONTEND_ORIGINS=["http://localhost:5173"]
```

### 4. Run database migrations

```bash
alembic upgrade head
```

This creates the necessary database tables for storing game statistics.

### 5. Run the development server

```bash
python main.py
```

The API will be available at `http://localhost:8000/`

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Root
- **GET** `/` - API information

### Game Management

#### Create New Game
- **POST** `/api/game/new`
- **Request Body** (optional): `CreateGameRequest`
  ```json
  {
    "aiPlayer": {
      "aiPlayerId": "piece_depth3",
      "aiColor": 2  // 1=Black, 2=White
    }
  }
  ```
- **Response**: `GameStateResponse`
- Creates a new game session and returns initial game state
- Optionally specify an AI player to play against

#### Make Move
- **POST** `/api/game/move`
- **Request Body**: `MakeMoveRequest`
  ```json
  {
    "gameId": "uuid-string",
    "position": {
      "row": 2,
      "col": 3
    }
  }
  ```
- **Response**: `GameStateResponse`
- Executes a move and returns updated game state
- Automatically handles pass when next player has no legal moves

#### Get Game State
- **GET** `/api/game/{game_id}`
- **Response**: `GameStateResponse`
- Retrieves current state of an existing game

#### Delete Game
- **DELETE** `/api/game/{game_id}`
- **Response**: Success message
- Deletes a game and cleans up associated resources (including AI processes)
- Returns 404 if game not found

### AI Player Management

#### Get Available AI Players
- **GET** `/api/ai/players`
- **Response**: List of available AI players with statistics
  ```json
  [
    {
      "id": "random",
      "name": "Random Player",
      "description": "Randomly selects legal moves",
      "statistics": {
        "totalGames": 150,
        "wins": 45,
        "losses": 92,
        "draws": 13,
        "winRate": 0.30,
        "asBlackWinRate": 0.28,
        "asWhiteWinRate": 0.32,
        "averageScore": 25.4
      }
    },
    {
      "id": "piece_depth3",
      "name": "Piece Counter (Depth 3)",
      "description": "Alpha-beta search with piece counting evaluation (depth 3)",
      "statistics": {
        "totalGames": 200,
        "wins": 140,
        "losses": 45,
        "draws": 15,
        "winRate": 0.70,
        "asBlackWinRate": 0.68,
        "asWhiteWinRate": 0.72,
        "averageScore": 38.2
      }
    }
  ]
  ```
- Each AI player includes comprehensive statistics:
  - `totalGames`: Total number of completed games
  - `wins`, `losses`, `draws`: Game outcome counts
  - `winRate`: Overall win rate (0.0 to 1.0, null if no games)
  - `asBlackWinRate`: Win rate when playing as black
  - `asWhiteWinRate`: Win rate when playing as white
  - `averageScore`: Average final score across all games

#### Make AI Move
- **POST** `/api/game/ai-move`
- **Request Body**: `AIMoveRequest`
  ```json
  {
    "gameId": "uuid-string"
  }
  ```
- **Response**: `GameStateResponse`
- Instructs the AI player to make a move for the current game
- Returns the updated game state after AI's move
- Fails if no AI is configured for the game or if it's not AI's turn

### Response Models

#### GameStateResponse
```json
{
  "gameId": "string",
  "board": [[0, 0, ...], ...],  // 8x8 grid (0=Empty, 1=Black, 2=White)
  "currentPlayer": 1,  // 1=Black, 2=White
  "score": {
    "black": 2,
    "white": 2
  },
  "legalMoves": [
    {"row": 2, "col": 3},
    ...
  ],
  "gameOver": false,
  "winner": null,  // null, 1, or 2
  "passed": false  // true if previous player had to pass
}
```

## Project Structure

```
reversi-backend/
├── reversi_backend/
│   ├── __init__.py
│   ├── app.py           # FastAPI application setup
│   ├── config.py        # Configuration and settings
│   ├── models.py        # Pydantic models for request/response
│   ├── routes.py        # API route handlers
│   ├── game_manager.py  # Game session management logic
│   ├── database.py      # Database models and statistics
│   ├── ai_config.py     # AI player configuration
│   ├── ai_manager.py    # AI process management
│   └── ai_players/      # AI player implementations
│       ├── __init__.py
│       ├── random_player.py
│       └── piece_player.py
├── alembic/             # Database migrations
│   ├── versions/        # Migration scripts
│   └── env.py          # Alembic configuration
├── tests/
│   ├── conftest.py                   # Test configuration
│   ├── test_integration.py           # Integration tests
│   ├── test_ai_integration.py        # AI integration tests
│   ├── test_database_integration.py  # Database tests
│   └── test_garbage_collection.py    # GC tests
├── main.py              # Application entry point
├── alembic.ini          # Alembic configuration file
├── pyproject.toml       # Project metadata and dependencies
├── .env.example         # Example environment variables
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

Run with coverage:
```bash
pytest --cov=reversi_backend
```

### Code Quality

Format code with ruff:
```bash
ruff format .
```

Lint code:
```bash
ruff check .
```

Auto-fix linting issues:
```bash
ruff check --fix .
```

### Pre-commit Hooks

Install git hooks:
```bash
pre-commit install
```

Run all hooks manually:
```bash
pre-commit run --all-files
```

## Game Logic

The backend uses the [`rust-reversi`](https://github.com/neodymium6/rust_reversi) library, which provides:
- Efficient bitboard-based game state representation
- Fast legal move generation
- Automatic game state validation
- Win/draw detection

### Pass Handling

When a player has no legal moves:
1. The backend automatically executes a pass
2. The `passed` flag is set to `true` in the response
3. If both players pass consecutively, the game ends

## AI Players

The backend supports AI players that run as separate processes. AI players communicate via stdin/stdout using the protocol defined by [rust-reversi](https://github.com/neodymium6/rust_reversi).

### Available AI Players

By default, the following AI players are available:

- **random** - Randomly selects from legal moves
- **piece_depth3** - Alpha-beta search with piece counting (depth 3)
- **piece_depth5** - Alpha-beta search with piece counting (depth 5)

### Adding Custom AI Players

To add a custom AI player, register it in `reversi_backend/ai_config.py`:

```python
AIPlayerConfig(
    id="my_custom_ai",
    name="My Custom AI",
    command=[sys.executable, str(AI_PLAYERS_DIR / "my_ai.py"), "arg1"],
    description="Description of your AI player"
)
```

Note: `sys.executable` ensures the same Python interpreter is used, and `AI_PLAYERS_DIR` provides the absolute path to the ai_players directory.

For implementation details and player protocol, see the [rust-reversi documentation](https://github.com/neodymium6/rust_reversi#creating-ai-players).

## Garbage Collection

The backend automatically cleans up inactive game sessions to prevent memory leaks:

- **Automatic cleanup**: Games that haven't been accessed for a specified timeout are automatically deleted
- **Periodic checks**: A background task runs at regular intervals to check for inactive games
- **Resource cleanup**: When a game is deleted, all associated resources (including AI processes) are properly cleaned up

### Configuration

You can configure the garbage collection behavior via environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GAME_TIMEOUT_SECONDS` | Time in seconds before inactive games are deleted | 3600 (1 hour) | 7200 |
| `GC_INTERVAL_SECONDS` | Interval in seconds between GC runs | 600 (10 minutes) | 300 |

**What counts as "access"?**
- Creating a new game
- Making a move
- Getting game state
- Making an AI move

Games are **not** deleted if they've been accessed within the timeout period, even if they're completed.

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `HOST` | Server host address | Yes | N/A |
| `PORT` | Server port | Yes | N/A |
| `RELOAD` | Enable auto-reload on code changes | No | `false` |
| `FRONTEND_ORIGINS` | List of allowed CORS origins | No | `[]` |
| `DATABASE_URL` | PostgreSQL connection URL | Yes | N/A |
| `DATABASE_ECHO` | Enable SQLAlchemy SQL logging | No | `false` |
| `GAME_TIMEOUT_SECONDS` | Time before inactive games are deleted (seconds) | No | `3600` |
| `GC_INTERVAL_SECONDS` | Interval between garbage collection runs (seconds) | No | `600` |

## Production Deployment

For production deployment:

1. Set up PostgreSQL database and configure `DATABASE_URL`
2. Run database migrations: `alembic upgrade head`
3. Set `reload=False` in `main.py` or use a production ASGI server
4. Configure proper CORS origins in `.env`
5. Consider using a process manager like systemd or supervisord
6. Set up reverse proxy (nginx/caddy) for SSL termination

Example deployment commands:
```bash
# Run migrations
alembic upgrade head

# Start server with multiple workers
uvicorn reversi_backend.app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Important**: Always run `alembic upgrade head` before starting the application to ensure the database schema is up to date.

## Integration with Frontend

This backend is designed to work with the [reversi-frontend](https://github.com/neodymium6/reversi-frontend) application. Make sure to:
1. Start the backend before the frontend
2. Configure `FRONTEND_ORIGINS` to include the frontend URL
3. Set `VITE_BACKEND_URL` in the frontend to point to this backend

## License

See LICENSE file for details.
