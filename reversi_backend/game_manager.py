"""Game session management using rust-reversi"""

import logging
import time
import uuid
from dataclasses import dataclass
from functools import wraps

from rust_reversi import Board, Color, Turn

from reversi_backend.ai_config import get_ai_player
from reversi_backend.ai_manager import AIPlayerProcess
from reversi_backend.models import (
    AIPlayerSettings,
    CellState,
    GameStateResponse,
    Position,
    Score,
)

BOARD_SIZE = 8

logger = logging.getLogger(__name__)


@dataclass
class GameSession:
    """Represents a single game session with all associated data"""

    board: Board
    last_access: float
    ai_process: AIPlayerProcess | None = None

    @property
    def current_player(self) -> Turn:
        """Get current player from board state"""
        return self.board.get_board()[2]


def update_access_time(func):
    """Decorator to update last access time for a game"""

    @wraps(func)
    def wrapper(self, game_id: str, *args, **kwargs):
        result = func(self, game_id, *args, **kwargs)
        # Update access time after successful execution
        if game_id in self.sessions:
            self.sessions[game_id].last_access = time.time()
        return result

    return wrapper


class GameManager:
    """Manages game sessions with in-memory storage"""

    def __init__(self):
        self.sessions: dict[str, GameSession] = {}

    def create_game(
        self, ai_player: AIPlayerSettings | None = None
    ) -> GameStateResponse:
        """Create a new game and return initial state

        Args:
            ai_player: Optional AI player settings
        """
        game_id = str(uuid.uuid4())
        board = Board()

        # Initialize AI player if requested
        ai_process = None
        if ai_player:
            ai_config = get_ai_player(ai_player.aiPlayerId)
            if not ai_config:
                raise ValueError(f"AI player not found: {ai_player.aiPlayerId}")

            ai_process = AIPlayerProcess(ai_config, ai_player.aiColor)
            logger.info(
                f"Created new game: {game_id} with AI player: {ai_config.name} "
                f"as {'BLACK' if ai_player.aiColor == CellState.BLACK else 'WHITE'}"
            )
        else:
            logger.info(f"Created new game: {game_id}")

        # Create and store game session
        session = GameSession(
            board=board, last_access=time.time(), ai_process=ai_process
        )
        self.sessions[game_id] = session

        return self._build_response(game_id, session)

    @update_access_time
    def make_move(self, game_id: str, position: Position) -> GameStateResponse:
        """Execute a move and return updated state"""
        if game_id not in self.sessions:
            logger.warning(f"Attempted move on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        session = self.sessions[game_id]

        # Convert position to rust-reversi format (0-63)
        pos = position.row * BOARD_SIZE + position.col

        # Validate and execute move
        if not session.board.is_legal_move(pos):
            logger.warning(f"Illegal move attempt: game={game_id}, pos={position}")
            raise ValueError(f"Illegal move at row={position.row}, col={position.col}")

        session.board.do_move(pos)

        # Check if next player needs to pass
        passed = False
        legal_moves = session.board.get_legal_moves_vec()

        if len(legal_moves) == 0 and not session.board.is_game_over():
            # Next player has no legal moves - must pass
            logger.info("Auto-pass: next player has no legal moves")
            session.board.do_pass()
            passed = True

            # After pass, check for double pass (game over)
            # If both players passed consecutively, game is over
            legal_moves_after_pass = session.board.get_legal_moves_vec()
            if len(legal_moves_after_pass) == 0:
                logger.info("Double pass detected - game over")
                # Game will be marked as over by is_game_over()

        logger.info(
            f"Move executed: game={game_id}, pos={position}, "
            f"next_player={session.current_player}, passed={passed}"
        )
        return self._build_response(game_id, session, passed)

    @update_access_time
    def get_game_state(self, game_id: str) -> GameStateResponse:
        """Get current game state"""
        if game_id not in self.sessions:
            logger.warning(f"Attempted get_state on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        session = self.sessions[game_id]
        return self._build_response(game_id, session)

    @update_access_time
    def make_ai_move(self, game_id: str) -> GameStateResponse:
        """Let AI make a move and return updated state"""
        if game_id not in self.sessions:
            logger.warning(f"Attempted AI move on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        session = self.sessions[game_id]

        if session.ai_process is None:
            raise ValueError(f"No AI player configured for game {game_id}")

        # Check if it's AI's turn
        current_player_int = (
            CellState.BLACK if session.current_player == Turn.BLACK else CellState.WHITE
        )
        if current_player_int != session.ai_process.color:
            raise ValueError(
                f"Not AI's turn. Current player: {current_player_int}, "
                f"AI color: {session.ai_process.color}"
            )

        # Get AI move
        move = session.ai_process.get_move(session.board)
        logger.info(f"AI player selected move: {move}")

        # Convert to Position and execute move
        position = Position(row=move // BOARD_SIZE, col=move % BOARD_SIZE)
        return self.make_move(game_id, position)

    def delete_game(self, game_id: str) -> None:
        """Delete a game and cleanup associated resources"""
        if game_id not in self.sessions:
            logger.warning(f"Attempted delete on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        # Remove session (AI process cleanup handled by __del__)
        del self.sessions[game_id]

        logger.info(f"Deleted game: {game_id}")

    def collect_garbage(self, timeout_seconds: int) -> int:
        """Remove inactive games that haven't been accessed for timeout_seconds

        Args:
            timeout_seconds: Time in seconds after which inactive games are deleted

        Returns:
            Number of games deleted
        """
        current_time = time.time()
        games_to_delete = []

        for game_id, session in self.sessions.items():
            if current_time - session.last_access > timeout_seconds:
                games_to_delete.append(game_id)

        # Delete expired games
        for game_id in games_to_delete:
            try:
                self.delete_game(game_id)
            except ValueError:
                # Game already deleted, skip
                logger.warning(f"Game {game_id} already deleted during GC")

        if games_to_delete:
            logger.info(f"Garbage collection: deleted {len(games_to_delete)} games")

        return len(games_to_delete)

    def _build_response(
        self, game_id: str, session: GameSession, passed: bool = False
    ) -> GameStateResponse:
        """Build GameStateResponse from GameSession object"""
        # Get board state as vector (returns Color objects for each cell)
        board_vec = session.board.get_board_vec_turn()

        # Convert to 8x8 matrix
        board_2d: list[list[CellState]] = []
        for row in range(BOARD_SIZE):
            board_row: list[CellState] = []
            for col in range(BOARD_SIZE):
                idx = row * BOARD_SIZE + col
                cell = board_vec[idx]
                # Convert Color enum to CellState
                if cell == Color.EMPTY:
                    board_row.append(CellState.EMPTY)
                elif cell == Color.BLACK:
                    board_row.append(CellState.BLACK)
                else:  # Color.WHITE
                    board_row.append(CellState.WHITE)
            board_2d.append(board_row)

        # Get legal moves
        legal_moves_pos = session.board.get_legal_moves_vec()
        legal_moves = [
            Position(row=pos // BOARD_SIZE, col=pos % BOARD_SIZE)
            for pos in legal_moves_pos
        ]

        # Get scores
        black_score = session.board.black_piece_num()
        white_score = session.board.white_piece_num()

        # Check game over
        game_over = session.board.is_game_over()
        winner = None
        if game_over:
            if session.board.is_black_win():
                winner = CellState.BLACK
            elif session.board.is_white_win():
                winner = CellState.WHITE
            # else: draw (winner remains None)

        # Determine current player (1=Black, 2=White)
        current_player_int = (
            CellState.BLACK if session.current_player == Turn.BLACK else CellState.WHITE
        )

        return GameStateResponse(
            gameId=game_id,
            board=board_2d,
            currentPlayer=current_player_int,
            score=Score(black=black_score, white=white_score),
            legalMoves=legal_moves,
            gameOver=game_over,
            winner=winner,
            passed=passed,
        )


# Global game manager instance
game_manager: GameManager = GameManager()
