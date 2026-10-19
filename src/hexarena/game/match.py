"""Play a full game from code, without any user interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hexarena.game.hex_game import HexGame
from hexarena.game.observation import Observation
from hexarena.game.state import BLUE, RED, HexState, Move


class MoveChooser(Protocol):
    """Anything with a ``choose_move`` method can play (bots, test players...)."""

    def choose_move(self, observation: Observation) -> Move:
        """Return the move to play given ``observation``."""
        ...


@dataclass(frozen=True, slots=True)
class GameResult:
    """Result of a game played with :func:`play_game`.

    Attributes:
        winner: ``RED`` (1) or ``BLUE`` (2).
        moves: Moves in the order they were played.
        final_state: State at the end of the game.
    """

    winner: int
    moves: tuple[Move, ...]
    final_state: HexState


def play_game(
    game: HexGame,
    bot1: MoveChooser,
    bot2: MoveChooser,
    time_limit: float = 1.0,
) -> GameResult:
    """Play a full game between two players.

    ``bot1`` plays Red (moves first) and ``bot2`` plays Blue. This
    function does not enforce time limits or catch bot errors: an illegal
    move raises :class:`~hexarena.game.hex_game.IllegalMoveError`. That
    robustness belongs to the tournament module.

    Args:
        game: The game (defines the board size).
        bot1: Red player.
        bot2: Blue player.
        time_limit: Seconds per move reported in each observation.

    Returns:
        The winner and the move history.
    """
    players = {RED: bot1, BLUE: bot2}
    state = game.initial_state()
    moves: list[Move] = []
    while not game.is_terminal(state):
        player = game.current_player(state)
        move = players[player].choose_move(game.observation(state, player, time_limit))
        state = game.play(state, move)
        moves.append(move)
    winner = game.winner(state)
    assert winner is not None  # Hex has no draws: a finished game always has a winner.
    return GameResult(winner=winner, moves=tuple(moves), final_state=state)
