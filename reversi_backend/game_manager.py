"""Game session management using rust-reversi"""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from rust_reversi import Board, Color, Turn

from reversi_backend.ai_config import get_ai_player
from reversi_backend.ai_manager import AIPlayerProcess
from reversi_backend.database import Game, PlayerType, SessionLocal, Winner
from reversi_backend.models import (
    AIPlayerSettings,
    CellState,
    GameStateResponse,
    Position,
    Score,
)

BOARD_SIZE = 8

logger = logging.getLogger(__name__)


# Helper functions for type conversions
def color_to_cell_state(color: Color) -> CellState:
    """Convert rust-reversi Color to CellState"""
    match color:
        case Color.EMPTY:
            return CellState.EMPTY
        case Color.BLACK:
            return CellState.BLACK
        case Color.WHITE:
            return CellState.WHITE
    raise ValueError(f"Unknown color: {color}")


def turn_to_cell_state(turn: Turn) -> CellState:
    """Convert rust-reversi Turn to CellState"""
    match turn:
        case Turn.BLACK:
            return CellState.BLACK
        case Turn.WHITE:
            return CellState.WHITE
    raise ValueError(f"Unknown turn: {turn}")


# Helper functions for position conversions
def position_to_index(position: Position) -> int:
    """Convert Position (row, col) to board index (0-63)"""
    return position.row * BOARD_SIZE + position.col


def index_to_position(index: int) -> Position:
    """Convert board index (0-63) to Position (row, col)"""
    return Position(row=index // BOARD_SIZE, col=index % BOARD_SIZE)


@dataclass
class GameSession:
    """Represents a single game session with all associated data"""

    board: Board
    last_access: float
    created_at: datetime
    black_player_type: PlayerType
    black_ai_id: str | None
    white_player_type: PlayerType
    white_ai_id: str | None
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

    def __init__(self, db_session_factory=SessionLocal):
        self.sessions: dict[str, GameSession] = {}
        self.db_session_factory = db_session_factory

    def _save_game_to_db(self, game_id: str, session: GameSession) -> None:
        """Save completed game to database

        Args:
            game_id: Game UUID
            session: Game session data
        """
        # Determine winner
        if session.board.is_black_win():
            winner = Winner.BLACK
        elif session.board.is_white_win():
            winner = Winner.WHITE
        else:
            winner = Winner.DRAW

        # Count total moves by counting non-empty cells minus initial 4 pieces
        total_moves = (
            session.board.black_piece_num() + session.board.white_piece_num() - 4
        )

        # Create Game record
        game_record = Game(
            id=game_id,
            created_at=session.created_at,
            finished_at=datetime.now(),
            black_player_type=session.black_player_type,
            black_ai_id=session.black_ai_id,
            white_player_type=session.white_player_type,
            white_ai_id=session.white_ai_id,
            winner=winner,
            black_score=session.board.black_piece_num(),
            white_score=session.board.white_piece_num(),
            total_moves=total_moves,
        )

        # Save to database only when game is over
        db = self.db_session_factory()
        try:
            db.add(game_record)
            db.commit()
            logger.info(
                f"Saved game to database: {game_id}, winner={winner.value}, "
                f"score={game_record.black_score}-{game_record.white_score}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save game {game_id} to database: {e}")
            raise
        finally:
            db.close()

    def create_game(
        self, ai_player: AIPlayerSettings | None = None
    ) -> GameStateResponse:
        """Create a new game and return initial state

        Args:
            ai_player: Optional AI player settings
        """
        game_id = str(uuid.uuid4())
        board = Board()
        current_time = time.time()

        # Determine player types
        ai_process = None
        if ai_player:
            ai_config = get_ai_player(ai_player.aiPlayerId)
            if not ai_config:
                raise ValueError(f"AI player not found: {ai_player.aiPlayerId}")

            ai_process = AIPlayerProcess(ai_config, ai_player.aiColor)

            # Set player types based on AI color
            if ai_player.aiColor == CellState.BLACK:
                black_player_type = PlayerType.AI
                black_ai_id = ai_player.aiPlayerId
                white_player_type = PlayerType.HUMAN
                white_ai_id = None
            else:  # WHITE
                black_player_type = PlayerType.HUMAN
                black_ai_id = None
                white_player_type = PlayerType.AI
                white_ai_id = ai_player.aiPlayerId

            logger.info(
                f"Created new game: {game_id} with AI player: {ai_config.name} "
                f"as {'BLACK' if ai_player.aiColor == CellState.BLACK else 'WHITE'}"
            )
        else:
            # Both players are human
            black_player_type = PlayerType.HUMAN
            black_ai_id = None
            white_player_type = PlayerType.HUMAN
            white_ai_id = None
            logger.info(f"Created new game: {game_id}")

        # Create and store game session
        session = GameSession(
            board=board,
            last_access=current_time,
            created_at=datetime.fromtimestamp(current_time),
            black_player_type=black_player_type,
            black_ai_id=black_ai_id,
            white_player_type=white_player_type,
            white_ai_id=white_ai_id,
            ai_process=ai_process,
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
        pos = position_to_index(position)

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

        response = self._build_response(game_id, session, passed)

        # Save to database if game is over
        if response.gameOver:
            self._save_game_to_db(game_id, session)

        return response

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
        current_player_int = turn_to_cell_state(session.current_player)
        if current_player_int != session.ai_process.color:
            raise ValueError(
                f"Not AI's turn. Current player: {current_player_int}, "
                f"AI color: {session.ai_process.color}"
            )

        # Get AI move
        move = session.ai_process.get_move(session.board)
        logger.info(f"AI player selected move: {move}")

        # Convert to Position and execute move
        position = index_to_position(move)
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
                board_row.append(color_to_cell_state(cell))
            board_2d.append(board_row)

        # Get legal moves
        legal_moves_pos = session.board.get_legal_moves_vec()
        legal_moves = [index_to_position(pos) for pos in legal_moves_pos]

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
        current_player_int = turn_to_cell_state(session.current_player)

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
