"""Test configuration and fixtures."""

import os

# Set test database URL BEFORE any imports that might use it
# Use file-based SQLite for tests to avoid connection issues
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest

from reversi_backend.database import Base, engine
from reversi_backend.game_manager import game_manager


@pytest.fixture(scope="session", autouse=True)
def setup_test_db_session():
    """Setup test database once for the entire test session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Drop all tables after all tests
    Base.metadata.drop_all(bind=engine)

    # Remove the test database file
    import os as os_module
    if os_module.path.exists("./test.db"):
        os_module.remove("./test.db")


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """Cleanup test data after each test."""
    yield

    # Clear game sessions
    game_manager.sessions.clear()

    # Clear all data from tables (but keep schema)
    from sqlalchemy import delete
    from reversi_backend.database import Game, SessionLocal

    db = SessionLocal()
    try:
        db.execute(delete(Game))
        db.commit()
    finally:
        db.close()
