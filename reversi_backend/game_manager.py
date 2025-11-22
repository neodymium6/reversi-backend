"""Game session management using rust-reversi"""

import logging
import uuid

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


class GameManager:
    """Manages game sessions with in-memory storage"""

    def __init__(self):
        self.games: dict[str, tuple[Board, Turn]] = {}
        self.ai_processes: dict[str, AIPlayerProcess] = {}

    def create_game(
        self, ai_player: AIPlayerSettings | None = None
    ) -> GameStateResponse:
        """Create a new game and return initial state

        Args:
            ai_player: Optional AI player settings
        """
        game_id = str(uuid.uuid4())
        board = Board()
        current_player = Turn.BLACK

        # Store game state
        self.games[game_id] = (board, current_player)

        # Initialize AI player if requested
        if ai_player:
            ai_config = get_ai_player(ai_player.aiPlayerId)
            if not ai_config:
                raise ValueError(f"AI player not found: {ai_player.aiPlayerId}")

            ai_process = AIPlayerProcess(ai_config, ai_player.aiColor)
            self.ai_processes[game_id] = ai_process
            logger.info(
                f"Created new game: {game_id} with AI player: {ai_config.name} "
                f"as {'BLACK' if ai_player.aiColor == CellState.BLACK else 'WHITE'}"
            )
        else:
            logger.info(f"Created new game: {game_id}")

        return self._build_response(game_id, board, current_player)

    def make_move(self, game_id: str, position: Position) -> GameStateResponse:
        """Execute a move and return updated state"""
        if game_id not in self.games:
            logger.warning(f"Attempted move on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        board, _current_player = self.games[game_id]

        # Convert position to rust-reversi format (0-63)
        pos = position.row * BOARD_SIZE + position.col

        # Validate and execute move
        if not board.is_legal_move(pos):
            logger.warning(f"Illegal move attempt: game={game_id}, pos={position}")
            raise ValueError(f"Illegal move at row={position.row}, col={position.col}")

        board.do_move(pos)

        # Check if next player needs to pass
        passed = False
        legal_moves = board.get_legal_moves_vec()

        if len(legal_moves) == 0 and not board.is_game_over():
            # Next player has no legal moves - must pass
            logger.info("Auto-pass: next player has no legal moves")
            board.do_pass()
            passed = True

            # After pass, check for double pass (game over)
            # If both players passed consecutively, game is over
            legal_moves_after_pass = board.get_legal_moves_vec()
            if len(legal_moves_after_pass) == 0:
                logger.info("Double pass detected - game over")
                # Game will be marked as over by is_game_over()

        # Update current player (rust-reversi handles turn switching internally)
        # Get the new current player from the board
        new_player = board.get_board()[2]  # (player_board, opponent_board, turn)

        # Update stored state
        self.games[game_id] = (board, new_player)

        logger.info(
            f"Move executed: game={game_id}, pos={position}, "
            f"next_player={new_player}, passed={passed}"
        )
        return self._build_response(game_id, board, new_player, passed)

    def get_game_state(self, game_id: str) -> GameStateResponse:
        """Get current game state"""
        if game_id not in self.games:
            logger.warning(f"Attempted get_state on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        board, current_player = self.games[game_id]
        return self._build_response(game_id, board, current_player)

    def make_ai_move(self, game_id: str) -> GameStateResponse:
        """Let AI make a move and return updated state"""
        if game_id not in self.games:
            logger.warning(f"Attempted AI move on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        if game_id not in self.ai_processes:
            raise ValueError(f"No AI player configured for game {game_id}")

        board, current_player = self.games[game_id]
        ai_process = self.ai_processes[game_id]

        # Check if it's AI's turn
        current_player_int = (
            CellState.BLACK if current_player == Turn.BLACK else CellState.WHITE
        )
        if current_player_int != ai_process.color:
            raise ValueError(
                f"Not AI's turn. Current player: {current_player_int}, "
                f"AI color: {ai_process.color}"
            )

        # Get AI move
        move = ai_process.get_move(board)
        logger.info(f"AI player selected move: {move}")

        # Convert to Position and execute move
        position = Position(row=move // BOARD_SIZE, col=move % BOARD_SIZE)
        return self.make_move(game_id, position)

    def delete_game(self, game_id: str) -> None:
        """Delete a game and cleanup associated resources"""
        if game_id not in self.games:
            logger.warning(f"Attempted delete on non-existent game: {game_id}")
            raise ValueError(f"Game {game_id} not found")

        # Remove AI process if exists (will trigger __del__ cleanup)
        if game_id in self.ai_processes:
            del self.ai_processes[game_id]

        # Remove game state
        del self.games[game_id]
        logger.info(f"Deleted game: {game_id}")

    def _build_response(
        self, game_id: str, board: Board, current_player: Turn, passed: bool = False
    ) -> GameStateResponse:
        """Build GameStateResponse from Board object"""
        # Get board state as vector (returns Color objects for each cell)
        board_vec = board.get_board_vec_turn()

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
        legal_moves_pos = board.get_legal_moves_vec()
        legal_moves = [
            Position(row=pos // BOARD_SIZE, col=pos % BOARD_SIZE)
            for pos in legal_moves_pos
        ]

        # Get scores
        black_score = board.black_piece_num()
        white_score = board.white_piece_num()

        # Check game over
        game_over = board.is_game_over()
        winner = None
        if game_over:
            if board.is_black_win():
                winner = CellState.BLACK
            elif board.is_white_win():
                winner = CellState.WHITE
            # else: draw (winner remains None)

        # Determine current player (1=Black, 2=White)
        current_player_int = (
            CellState.BLACK if current_player == Turn.BLACK else CellState.WHITE
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
