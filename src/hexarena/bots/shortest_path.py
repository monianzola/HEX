"""ShortestPathBot: greedy one-ply bot based on shortest-path distances."""

from __future__ import annotations

import time

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import WIN_SCORE, center_distance, evaluate, with_stone

TIME_FRACTION = 0.8
"""Fraction of ``time_limit`` the bot allows itself before answering."""


@register_bot("shortest-path")
class ShortestPathBot(Bot):
    """Plays the move that maximises ``opponent_distance - own_distance``.

    For every legal move the bot places its stone on a copy of the board
    and measures, with a 0-1 BFS, how many stones each player still needs
    to connect their edges. A single move can therefore both advance its
    own path and lengthen the opponent's. Ties are broken by proximity to
    the centre of the board, the strongest area in Hex.

    It looks only one move ahead (greedy), so it does not anticipate the
    opponent's reply.
    """

    name = "ShortestPathBot"
    author = "hex-arena team"
    description = "Greedy: maximises the opponent's shortest path minus its own."

    def choose_move(self, observation: Observation) -> Move:
        """Evaluate every legal move and return the best one."""
        deadline = time.perf_counter() + TIME_FRACTION * observation.time_limit
        board, size, player = observation.board, observation.size, observation.player

        # Visit moves from the centre outwards: if time runs out, the moves
        # already evaluated are the most promising ones.
        moves = sorted(observation.legal_moves, key=lambda m: center_distance(m, size))
        best_move = moves[0]
        best_key = (-float("inf"), 0.0)
        for move in moves:
            score = evaluate(with_stone(board, move, player), player)
            key = (score, -center_distance(move, size))
            if key > best_key:
                best_key, best_move = key, move
                if score >= WIN_SCORE:
                    break  # Winning move: no need to look further.
            if time.perf_counter() > deadline:
                break
        return best_move
