"""AI player configuration models and registry"""

import sys
from pathlib import Path

from pydantic import BaseModel

# Get absolute path to ai_players directory
AI_PLAYERS_DIR = Path(__file__).parent / "ai_players"


class AIPlayerConfig(BaseModel):
    """Configuration for an AI player"""

    id: str
    name: str
    command: list[str]
    description: str


# Registry of available AI players
AI_PLAYERS: list[AIPlayerConfig] = [
    AIPlayerConfig(
        id="random",
        name="Random Player",
        command=[sys.executable, str(AI_PLAYERS_DIR / "random_player.py")],
        description="Randomly selects legal moves",
    ),
    AIPlayerConfig(
        id="piece_depth3",
        name="Piece Counter (Depth 3)",
        command=[sys.executable, str(AI_PLAYERS_DIR / "piece_player.py"), "3"],
        description="Alpha-beta search with piece counting evaluation (depth 3)",
    ),
    AIPlayerConfig(
        id="piece_depth5",
        name="Piece Counter (Depth 5)",
        command=[sys.executable, str(AI_PLAYERS_DIR / "piece_player.py"), "5"],
        description="Alpha-beta search with piece counting evaluation (depth 5)",
    ),
]


def get_ai_player(player_id: str) -> AIPlayerConfig | None:
    """Get AI player configuration by ID"""
    for player in AI_PLAYERS:
        if player.id == player_id:
            return player
    return None


def get_all_ai_players() -> list[AIPlayerConfig]:
    """Get all available AI players"""
    return AI_PLAYERS
