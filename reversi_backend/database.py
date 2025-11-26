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
