"""Hex game logic: board state, rules and win detection."""

from hexarena.game.hex_game import (
    NEIGHBOR_OFFSETS,
    HexGame,
    IllegalMoveError,
    find_winner,
    neighbors,
)
from hexarena.game.match import GameResult, MoveChooser, play_game
from hexarena.game.observation import Observation
from hexarena.game.state import BLUE, EMPTY, RED, Board, HexState, Move, opponent

__all__ = [
    "BLUE",
    "EMPTY",
    "NEIGHBOR_OFFSETS",
    "RED",
    "Board",
    "GameResult",
    "HexGame",
    "HexState",
    "IllegalMoveError",
    "Move",
    "MoveChooser",
    "Observation",
    "find_winner",
    "neighbors",
    "opponent",
    "play_game",
]
