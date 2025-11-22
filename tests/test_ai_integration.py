"""Tests for AI player integration"""

from fastapi.testclient import TestClient

from reversi_backend.app import app
from reversi_backend.models import CellState, GameStateResponse

client = TestClient(app)


def test_get_ai_players():
    """Test getting list of available AI players"""
    response = client.get("/api/ai/players")
    assert response.status_code == 200

    players = response.json()
    assert len(players) > 0

    # Check structure of first player
    player = players[0]
    assert "id" in player
    assert "name" in player
    assert "description" in player

    # Check that we have the expected AI players
    player_ids = [p["id"] for p in players]
    assert "random" in player_ids
    assert "piece_depth3" in player_ids


def test_create_game_with_ai():
    """Test creating a game with an AI player"""
    response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "random", "aiColor": CellState.WHITE}},
    )
    assert response.status_code == 200

    game_state = GameStateResponse.model_validate(response.json())
    assert game_state.gameId is not None
    assert game_state.currentPlayer == CellState.BLACK
    assert len(game_state.legalMoves) > 0


def test_create_game_without_ai():
    """Test creating a game without AI player"""
    response = client.post("/api/game/new", json={})
    assert response.status_code == 200

    game_state = GameStateResponse.model_validate(response.json())
    assert game_state.gameId is not None


def test_ai_move():
    """Test AI making a move"""
    # Create game with AI as WHITE
    create_response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "random", "aiColor": CellState.WHITE}},
    )
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # Human (BLACK) makes first move
    human_move = game_state.legalMoves[0]
    move_response = client.post(
        "/api/game/move",
        json={
            "gameId": game_id,
            "position": {"row": human_move.row, "col": human_move.col},
        },
    )
    assert move_response.status_code == 200
    after_human_move = GameStateResponse.model_validate(move_response.json())

    # Should now be WHITE's turn
    assert after_human_move.currentPlayer == CellState.WHITE

    # Let AI make a move
    ai_move_response = client.post("/api/game/ai-move", json={"gameId": game_id})
    assert ai_move_response.status_code == 200

    after_ai_move = GameStateResponse.model_validate(ai_move_response.json())
    # Should be back to BLACK's turn
    assert after_ai_move.currentPlayer == CellState.BLACK


def test_ai_move_wrong_turn():
    """Test AI move fails when it's not AI's turn"""
    # Create game with AI as WHITE
    create_response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "random", "aiColor": CellState.WHITE}},
    )
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # Try to make AI move when it's BLACK's turn
    ai_move_response = client.post("/api/game/ai-move", json={"gameId": game_id})
    assert ai_move_response.status_code == 400
    assert "Not AI's turn" in ai_move_response.json()["detail"]


def test_ai_move_no_ai_configured():
    """Test AI move fails when no AI is configured for the game"""
    # Create game without AI
    create_response = client.post("/api/game/new", json={})
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # Try to make AI move
    ai_move_response = client.post("/api/game/ai-move", json={"gameId": game_id})
    assert ai_move_response.status_code == 400
    assert "No AI player configured" in ai_move_response.json()["detail"]


def test_create_game_with_invalid_ai():
    """Test creating game with invalid AI player ID"""
    response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "invalid_ai", "aiColor": CellState.WHITE}},
    )
    assert response.status_code == 400
    assert "AI player not found" in response.json()["detail"]


def test_ai_as_black():
    """Test AI playing as BLACK"""
    # Create game with AI as BLACK
    create_response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "random", "aiColor": CellState.BLACK}},
    )
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # AI should be able to move immediately since BLACK goes first
    assert game_state.currentPlayer == CellState.BLACK

    ai_move_response = client.post("/api/game/ai-move", json={"gameId": game_id})
    assert ai_move_response.status_code == 200

    after_ai_move = GameStateResponse.model_validate(ai_move_response.json())
    # Should be WHITE's turn now
    assert after_ai_move.currentPlayer == CellState.WHITE


def test_delete_game():
    """Test deleting a game"""
    # Create game
    create_response = client.post("/api/game/new", json={})
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # Delete game
    delete_response = client.delete(f"/api/game/{game_id}")
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["message"]

    # Try to get deleted game - should fail
    get_response = client.get(f"/api/game/{game_id}")
    assert get_response.status_code == 404


def test_delete_game_with_ai():
    """Test deleting a game with AI player"""
    # Create game with AI
    create_response = client.post(
        "/api/game/new",
        json={"aiPlayer": {"aiPlayerId": "random", "aiColor": CellState.WHITE}},
    )
    assert create_response.status_code == 200
    game_state = GameStateResponse.model_validate(create_response.json())
    game_id = game_state.gameId

    # Delete game (should cleanup AI process)
    delete_response = client.delete(f"/api/game/{game_id}")
    assert delete_response.status_code == 200

    # Try to use AI for deleted game - should fail
    ai_move_response = client.post("/api/game/ai-move", json={"gameId": game_id})
    assert ai_move_response.status_code == 400


def test_delete_nonexistent_game():
    """Test deleting a non-existent game"""
    delete_response = client.delete("/api/game/nonexistent-id")
    assert delete_response.status_code == 404
    assert "not found" in delete_response.json()["detail"]
