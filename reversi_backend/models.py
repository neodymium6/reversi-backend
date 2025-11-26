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
    passed: bool = False  # True if the previous player had to pass


class MakeMoveRequest(BaseModel):
    """Request to make a move"""

    gameId: str
    position: Position


class AIPlayerSettings(BaseModel):
    """AI player settings for a game"""

    aiPlayerId: str
    aiColor: CellState  # BLACK or WHITE


class CreateGameRequest(BaseModel):
    """Request to create a new game"""

    aiPlayer: AIPlayerSettings | None = None


class AIMoveRequest(BaseModel):
    """Request for AI to make a move"""

    gameId: str


class AIStatistics(BaseModel):
    """AI player statistics"""

    totalGames: int  # Total number of games played
    wins: int  # Number of wins
    losses: int  # Number of losses
    draws: int  # Number of draws
    winRate: float | None  # Win rate (wins / totalGames), None if no games
    asBlackWinRate: float | None  # Win rate as black player, None if no games
    asWhiteWinRate: float | None  # Win rate as white player, None if no games
    averageScore: float | None  # Average score across all games, None if no games


class AIPlayerMetadata(BaseModel):
    """AI player metadata with statistics"""

    id: str
    name: str
    description: str
    statistics: AIStatistics
