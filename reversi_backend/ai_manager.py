"""AI player process management"""

import logging
import subprocess

from rust_reversi import Board

from reversi_backend.ai_config import AIPlayerConfig
from reversi_backend.models import CellState

logger = logging.getLogger(__name__)


class AIPlayerProcess:
    """Manages a subprocess running an AI player"""

    def __init__(self, config: AIPlayerConfig, color: CellState):
        """Initialize and start AI player process

        Args:
            config: AI player configuration
            color: Color this player will play as (BLACK or WHITE)
        """
        self.config = config
        self.color = color
        self.process: subprocess.Popen | None = None
        self._start()

    def __del__(self):
        """Cleanup when object is destroyed"""
        self._stop()

    def get_move(self, board: Board) -> int:
        """Get move from AI player for current board state

        Args:
            board: Current board state

        Returns:
            Move position (0-63)
        """
        # Send board state
        board_str = board.get_board_line()
        self._send_line(board_str)

        # Read move response
        response = self._read_line()

        try:
            move = int(response)
            logger.debug(f"AI player {self.config.name} selected move: {move}")
            return move
        except ValueError as e:
            raise RuntimeError(
                f"AI player {self.config.name} returned invalid move: {response}"
            ) from e

    def _start(self):
        """Start the AI player process"""
        # Add color argument to command
        color_str = "BLACK" if self.color == CellState.BLACK else "WHITE"
        command = self.config.command + [color_str]

        logger.info(f"Starting AI player: {self.config.name} as {color_str}")
        logger.debug(f"Command: {' '.join(command)}")

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Verify connection with ping/pong
        self._send_line("ping")
        response = self._read_line()
        if response != "pong":
            self._stop()
            raise RuntimeError(
                f"AI player {self.config.name} failed ping check: got '{response}'"
            )

        logger.info(f"AI player {self.config.name} started successfully")

    def _stop(self):
        """Stop the AI player process"""
        if self.process:
            logger.info(f"Stopping AI player: {self.config.name}")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing AI player: {self.config.name}")
                self.process.kill()
            self.process = None

    def _send_line(self, line: str):
        """Send a line to the AI player process"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("AI player process not started")

        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def _read_line(self) -> str:
        """Read a line from the AI player process"""
        if not self.process or not self.process.stdout:
            raise RuntimeError("AI player process not started")

        try:
            line = self.process.stdout.readline().strip()
            if not line and self.process.poll() is not None:
                # Process has terminated
                stderr_output = (
                    self.process.stderr.read() if self.process.stderr else ""
                )
                raise RuntimeError(
                    f"AI player {self.config.name} terminated unexpectedly. "
                    f"stderr: {stderr_output}"
                )
            return line
        except Exception as e:
            logger.error(f"Error reading from AI player {self.config.name}: {e}")
            raise
