from fastapi.testclient import TestClient
from httpx import Response

from reversi_backend.app import app
from reversi_backend.models import CellState, GameStateResponse

client: TestClient = TestClient(app)


def test_create_game():
    response: Response = client.post("/api/game/new")
    assert response.status_code == 200
    # Use model_validate for type-safe parsing
    data = GameStateResponse.model_validate(response.json())
    assert data.gameId is not None
    assert len(data.board) == 8
    assert data.currentPlayer == CellState.BLACK
    assert len(data.legalMoves) > 0


def test_make_move_flow():
    # 1. Create game
    create_resp: Response = client.post("/api/game/new")
    assert create_resp.status_code == 200
    game_data = GameStateResponse.model_validate(create_resp.json())
    game_id: str = game_data.gameId

    # 2. Make a valid move (Black at 2,3)
    move: dict[str, int] = {"row": 2, "col": 3}
    move_resp: Response = client.post(
        "/api/game/move", json={"gameId": game_id, "position": move}
    )
    assert move_resp.status_code == 200

    new_state = GameStateResponse.model_validate(move_resp.json())
    assert new_state.currentPlayer == CellState.WHITE  # Should switch to White
    assert new_state.score.black == 4
    assert new_state.score.white == 1


def test_invalid_move():
    # 1. Create game
    create_resp: Response = client.post("/api/game/new")
    # Use model_validate to extract gameId safely
    game_data = GameStateResponse.model_validate(create_resp.json())
    game_id: str = game_data.gameId

    # 2. Try invalid move (Occupied center square)
    move: dict[str, int] = {"row": 3, "col": 3}
    resp: Response = client.post(
        "/api/game/move", json={"gameId": game_id, "position": move}
    )
    assert resp.status_code == 400


def test_get_game_state():
    # 1. Create game
    create_resp: Response = client.post("/api/game/new")
    # Use model_validate
    game_data = GameStateResponse.model_validate(create_resp.json())
    game_id: str = game_data.gameId

    # 2. Get state
    resp: Response = client.get(f"/api/game/{game_id}")
    assert resp.status_code == 200
    state = GameStateResponse.model_validate(resp.json())
    assert state.gameId == game_id
