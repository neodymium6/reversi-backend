"""API route handlers"""

from fastapi import APIRouter, HTTPException

from reversi_backend.ai_config import get_all_ai_players
from reversi_backend.game_manager import game_manager
from reversi_backend.models import (
    AIMoveRequest,
    CreateGameRequest,
    GameStateResponse,
    MakeMoveRequest,
)

router: APIRouter = APIRouter()


@router.post("/api/game/new", response_model=GameStateResponse)
async def create_new_game(request: CreateGameRequest | None = None):
    """Start a new game"""
    try:
        ai_player = request.aiPlayer if request else None
        return game_manager.create_game(ai_player)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/game/move", response_model=GameStateResponse)
async def make_move(request: MakeMoveRequest):
    """Make a move in an existing game"""
    try:
        return game_manager.make_move(request.gameId, request.position)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/game/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get current game state"""
    try:
        return game_manager.get_game_state(game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/api/ai/players")
async def get_ai_players():
    """Get list of available AI players"""
    return [
        {
            "id": player.id,
            "name": player.name,
            "description": player.description,
        }
        for player in get_all_ai_players()
    ]


@router.post("/api/game/ai-move", response_model=GameStateResponse)
async def make_ai_move(request: AIMoveRequest):
    """Let AI make a move"""
    try:
        return game_manager.make_ai_move(request.gameId)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    """Delete a game and cleanup resources"""
    try:
        game_manager.delete_game(game_id)
        return {"message": f"Game {game_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
