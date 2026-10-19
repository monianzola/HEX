"""What a player (human or bot) sees when it is asked for a move."""

from __future__ import annotations

from dataclasses import dataclass

from hexarena.game.state import Board, Move


@dataclass(frozen=True, slots=True)
class Observation:
    """Read-only view of the game given to the player who must move.

    Every field is immutable, so a bot cannot alter the real game
    through its observation.

    Attributes:
        board: The board as a tuple of rows (``EMPTY``, ``RED`` or ``BLUE``).
        size: Side length N of the board.
        player: The player who must move (``RED`` = 1 or ``BLUE`` = 2).
        legal_moves: Every legal move, in row-major order.
        time_limit: Seconds available to choose the move.
    """

    board: Board
    size: int
    player: int
    legal_moves: tuple[Move, ...]
    time_limit: float
