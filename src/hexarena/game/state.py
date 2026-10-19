"""Basic types and the immutable game state."""

from __future__ import annotations

from dataclasses import dataclass

EMPTY = 0
"""Value of an empty cell."""

RED = 1
"""Player 1 (Red): moves first and connects the top row with the bottom row."""

BLUE = 2
"""Player 2 (Blue): connects the left column with the right column."""

Board = tuple[tuple[int, ...], ...]
"""An N×N board: ``board[row][col]`` is ``EMPTY``, ``RED`` or ``BLUE``."""

Move = tuple[int, int]
"""A move is the cell ``(row, col)`` where the current player places a stone."""


def opponent(player: int) -> int:
    """Return the other player.

    Args:
        player: ``RED`` or ``BLUE``.

    Raises:
        ValueError: If ``player`` is not a valid player.
    """
    if player not in (RED, BLUE):
        raise ValueError(f"Invalid player: {player!r} (expected {RED} or {BLUE})")
    return BLUE if player == RED else RED


@dataclass(frozen=True, slots=True)
class HexState:
    """Immutable snapshot of a Hex game.

    Attributes:
        board: The board as a tuple of rows.
        to_move: Player whose turn it is.
        winner: The winner, or ``None`` while the game is in progress.
    """

    board: Board
    to_move: int = RED
    winner: int | None = None

    @property
    def size(self) -> int:
        """Side length N of the board."""
        return len(self.board)
