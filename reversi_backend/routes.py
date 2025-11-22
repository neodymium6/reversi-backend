"""API route handlers"""

from fastapi import APIRouter, HTTPException

from reversi_backend.game_manager import game_manager
from reversi_backend.models import GameStateResponse, MakeMoveRequest

router: APIRouter = APIRouter()


@router.post("/api/game/new", response_model=GameStateResponse)
async def create_new_game():
    """Start a new game"""
    return game_manager.create_game()


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
