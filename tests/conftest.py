"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from reversi_backend.database import Base
from reversi_backend.game_manager import game_manager


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Setup in-memory SQLite database for testing."""
    # Create in-memory SQLite database for tests
    engine = create_engine("sqlite:///:memory:")
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Replace game_manager's db_session_factory with test one
    original_factory = game_manager.db_session_factory
    game_manager.db_session_factory = TestSessionLocal

    yield TestSessionLocal

    # Cleanup: restore original factory
    game_manager.db_session_factory = original_factory
    game_manager.sessions.clear()

    # Drop all tables
    Base.metadata.drop_all(bind=engine)
