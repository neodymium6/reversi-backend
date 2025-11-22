"""Test garbage collection functionality"""

import time

from reversi_backend.game_manager import GameManager


def test_garbage_collection():
    """Test that inactive games are deleted by garbage collection"""
    manager = GameManager()

    # Create a game
    state1 = manager.create_game()
    game_id1 = state1.gameId

    # Wait a bit and create another game
    time.sleep(0.1)
    state2 = manager.create_game()
    game_id2 = state2.gameId

    # Verify both games exist
    assert game_id1 in manager.sessions
    assert game_id2 in manager.sessions

    # Manually set first game's last access time to be old (2 seconds ago)
    manager.sessions[game_id1].last_access = time.time() - 2

    # Run garbage collection with 1 second timeout
    deleted = manager.collect_garbage(timeout_seconds=1)

    # First game should be deleted, second should remain
    assert deleted == 1
    assert game_id1 not in manager.sessions
    assert game_id2 in manager.sessions


def test_garbage_collection_no_timeout():
    """Test that no games are deleted if none have timed out"""
    manager = GameManager()

    # Create a game
    state = manager.create_game()
    game_id = state.gameId

    # Run garbage collection immediately with 10 second timeout
    deleted = manager.collect_garbage(timeout_seconds=10)

    # No games should be deleted
    assert deleted == 0
    assert game_id in manager.sessions


def test_access_updates_last_access_time():
    """Test that accessing a game updates its last access time"""
    manager = GameManager()

    # Create a game
    state = manager.create_game()
    game_id = state.gameId

    # Get initial access time
    initial_time = manager.sessions[game_id].last_access

    # Wait a bit
    time.sleep(0.1)

    # Access the game
    manager.get_game_state(game_id)

    # Last access time should be updated
    assert manager.sessions[game_id].last_access > initial_time


def test_garbage_collection_with_ai():
    """Test that AI processes are cleaned up during garbage collection"""
    from reversi_backend.models import AIPlayerSettings, CellState

    manager = GameManager()

    # Create a game with AI
    ai_settings = AIPlayerSettings(aiPlayerId="random", aiColor=CellState.WHITE)
    state = manager.create_game(ai_settings)
    game_id = state.gameId

    # Verify AI process exists
    assert manager.sessions[game_id].ai_process is not None

    # Set last access time to old
    manager.sessions[game_id].last_access = time.time() - 2

    # Run garbage collection
    deleted = manager.collect_garbage(timeout_seconds=1)

    # Game and AI process should be deleted
    assert deleted == 1
    assert game_id not in manager.sessions
