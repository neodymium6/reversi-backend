"""Pydantic models for API request/response"""

from enum import IntEnum

from pydantic import BaseModel


class CellState(IntEnum):
    """Cell state values"""

    EMPTY = 0
    BLACK = 1
    WHITE = 2


class Position(BaseModel):
    """Position on the board (row, col)"""

    row: int
    col: int


class Score(BaseModel):
    """Game score"""

    black: int
    white: int


class GameStateResponse(BaseModel):
    """Response containing full game state"""

    gameId: str
    board: list[list[CellState]]  # 8x8 grid
    currentPlayer: CellState  # BLACK or WHITE
    score: Score
    legalMoves: list[Position]
    gameOver: bool
    winner: CellState | None = None  # BLACK, WHITE, or None


class MakeMoveRequest(BaseModel):
    """Request to make a move"""

    gameId: str
    position: Position
