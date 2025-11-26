"""Database models and configuration for reversi backend."""

import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from reversi_backend.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class PlayerType(enum.Enum):
    """Player type enumeration."""

    AI = "AI"
    HUMAN = "HUMAN"


class Winner(enum.Enum):
    """Winner enumeration."""

    BLACK = "BLACK"
    WHITE = "WHITE"
    DRAW = "DRAW"


class Game(Base):
    """Game table storing completed game results."""

    __tablename__ = "games"

    # Primary key
    id = Column(String, primary_key=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)

    # Black player info
    black_player_type = Column(Enum(PlayerType), nullable=False)
    black_ai_id = Column(String, nullable=True)  # NULL for HUMAN players

    # White player info
    white_player_type = Column(Enum(PlayerType), nullable=False)
    white_ai_id = Column(String, nullable=True)  # NULL for HUMAN players

    # Game result (all NOT NULL for completed games)
    winner = Column(Enum(Winner), nullable=False)
    black_score = Column(Integer, nullable=False)
    white_score = Column(Integer, nullable=False)
    total_moves = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Game(id={self.id}, winner={self.winner}, created_at={self.created_at})>"
        )


# Database engine and session factory
engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_ai_statistics(ai_id: str, db_session_factory=SessionLocal) -> dict:
    """Calculate statistics for a specific AI player.

    Args:
        ai_id: AI player ID
        db_session_factory: Database session factory (for testing)

    Returns:
        Dictionary with statistics:
        - totalGames: Total games played
        - wins: Number of wins
        - losses: Number of losses
        - draws: Number of draws
        - winRate: Overall win rate (None if no games)
        - asBlackWinRate: Win rate as black (None if no games as black)
        - asWhiteWinRate: Win rate as white (None if no games as white)
        - averageScore: Average score (None if no games)
    """
    db = db_session_factory()
    try:
        # Query games where this AI played (only DB operations in try block)
        games_as_black = (
            db.query(Game)
            .filter(Game.black_player_type == PlayerType.AI, Game.black_ai_id == ai_id)
            .all()
        )
        games_as_white = (
            db.query(Game)
            .filter(Game.white_player_type == PlayerType.AI, Game.white_ai_id == ai_id)
            .all()
        )
    finally:
        db.close()

    # Calculate statistics (pure Python, outside try block)
    total_games = len(games_as_black) + len(games_as_white)

    # Return empty statistics if no games
    if total_games == 0:
        return {
            "totalGames": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "winRate": None,
            "asBlackWinRate": None,
            "asWhiteWinRate": None,
            "averageScore": None,
        }

    # Count wins, losses, draws
    wins = 0
    losses = 0
    draws = 0
    total_score = 0

    # Process games as black
    black_wins = 0
    for game in games_as_black:
        if game.winner == Winner.BLACK:
            wins += 1
            black_wins += 1
        elif game.winner == Winner.WHITE:
            losses += 1
        else:  # DRAW
            draws += 1
        total_score += game.black_score

    # Process games as white
    white_wins = 0
    for game in games_as_white:
        if game.winner == Winner.WHITE:
            wins += 1
            white_wins += 1
        elif game.winner == Winner.BLACK:
            losses += 1
        else:  # DRAW
            draws += 1
        total_score += game.white_score

    # Calculate rates
    win_rate = wins / total_games

    black_games = len(games_as_black)
    as_black_win_rate = black_wins / black_games if black_games > 0 else None

    white_games = len(games_as_white)
    as_white_win_rate = white_wins / white_games if white_games > 0 else None

    average_score = total_score / total_games

    return {
        "totalGames": total_games,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "winRate": win_rate,
        "asBlackWinRate": as_black_win_rate,
        "asWhiteWinRate": as_white_win_rate,
        "averageScore": average_score,
    }
