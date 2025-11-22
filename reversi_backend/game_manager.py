"""Game session management using rust-reversi"""

import logging
import uuid

from rust_reversi import Board, Color, Turn

from reversi_backend.models import CellState, GameStateResponse, Position, Score

BOARD_SIZE = 8

logger = logging.getLogger(__name__)


class GameManager:
    """Manages game sessions with in-memory storage"""

    def __init__(self):
        self.games: dict[str, tuple[Board, Turn]] = {}

    def create_game(self) -> GameStateResponse:
        """Create a new game and return initial state"""
        game_id = str(uuid.uuid4())
        board = Board()
        current_player = Turn.BLACK

        # Store game state
        self.games[game_id] = (board, current_player)

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
