"""AlphaBetaBot: minimax with alpha-beta pruning and iterative deepening."""

from __future__ import annotations

import math
import time

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import (
    WIN_SCORE,
    center_distance,
    evaluate,
    path_slack,
    shortest_path_distance,
    with_stone,
)
from hexarena.game.state import EMPTY, Board, opponent

TIME_FRACTION = 0.8
"""Fraction of ``time_limit`` the bot allows itself."""

MAX_CANDIDATES = 20
"""Moves explored at each node (the most promising ones)."""


class OutOfTime(Exception):
    """Raised inside the search when the deadline has passed."""


class AlphaBetaSearch:
    """Negamax search with alpha-beta pruning.

    *Negamax* is minimax written once: the value of a position for the
    player to move is minus the value of the best reply for the opponent.

    Args:
        max_candidates: Moves explored per node (``None`` = all of them).
        deadline: ``time.perf_counter()`` value at which the search aborts
            by raising :class:`OutOfTime`.
    """

    def __init__(self, max_candidates: int | None = MAX_CANDIDATES, deadline: float = math.inf) -> None:
        self.max_candidates = max_candidates
        self.deadline = deadline
        self.nodes = 0

    def ordered_moves(self, board: Board, to_move: int) -> list[Move]:
        """Empty cells, most critical first, cut to ``max_candidates``.

        A cell is critical if it lies on (or near) a shortest path of
        either player: taking it advances our path or blocks theirs. This
        needs 4 BFS per node instead of one evaluation per move.
        """
        mine = path_slack(board, to_move)
        theirs = path_slack(board, opponent(to_move))
        size = len(board)
        empties = [(r, c) for r in range(size) for c in range(size) if board[r][c] == EMPTY]

        def key(move: Move) -> tuple[float, float, float]:
            a, b = mine.get(move, math.inf), theirs.get(move, math.inf)
            return (min(a, b), a + b, center_distance(move, size))

        empties.sort(key=key)
        return empties if self.max_candidates is None else empties[: self.max_candidates]

    def negamax(self, board: Board, to_move: int, depth: int, alpha: float, beta: float) -> float:
        """Value of ``board`` for ``to_move``, searching ``depth`` plies ahead.

        Wins are scored ``WIN_SCORE + depth`` so that, among winning lines,
        the fastest one is preferred (and the slowest loss is preferred).
        """
        self.nodes += 1
        if time.perf_counter() > self.deadline:
            raise OutOfTime
        own = shortest_path_distance(board, to_move)
        if own == 0:
            return WIN_SCORE + depth
        rival = shortest_path_distance(board, opponent(to_move))
        if rival == 0:
            return -(WIN_SCORE + depth)
        if depth == 0:
            return rival - own

        best = -math.inf
        for move in self.ordered_moves(board, to_move):
            value = -self.negamax(with_stone(board, move, to_move), opponent(to_move), depth - 1, -beta, -alpha)
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break  # Beta cut-off: the opponent will never allow this line.
        return best

    def search_root(self, board: Board, player: int, moves: list[Move], depth: int) -> tuple[Move, float]:
        """Best of ``moves`` for ``player`` at ``depth`` plies, and its value."""
        alpha, beta = -math.inf, math.inf
        best_move, best_value = moves[0], -math.inf
        for move in moves:
            value = -self.negamax(with_stone(board, move, player), opponent(player), depth - 1, -beta, -alpha)
            if value > best_value:
                best_move, best_value = move, value
            alpha = max(alpha, value)
        return best_move, best_value


@register_bot("alpha-beta")
class AlphaBetaBot(Bot):
    """Minimax with alpha-beta pruning and iterative deepening.

    1. Orders the root moves with the same one-ply evaluation as
       :class:`~hexarena.bots.shortest_path.ShortestPathBot` and keeps the
       best ``max_candidates``.
    2. Searches depth 1, 2, 3... until 80 % of the time limit is used. The
       best move of each completed depth is searched first in the next one,
       which makes pruning more effective.
    3. Returns the best move of the deepest completed search.

    Args:
        max_candidates: Moves explored per node.
        max_depth: Optional depth limit (``None`` = limited only by time).
    """

    name = "AlphaBetaBot"
    author = "hex-arena team"
    description = "Minimax con poda alfa-beta y profundización iterativa sobre la heurística de caminos."

    def __init__(self, max_candidates: int = MAX_CANDIDATES, max_depth: int | None = None) -> None:
        self.max_candidates = max_candidates
        self.max_depth = max_depth
        self.last_depth = 0
        """Depth of the last completed search (for analysis and tests)."""
        self.last_nodes = 0

    def choose_move(self, observation: Observation) -> Move:
        """Search as deep as time allows and return the best move found."""
        deadline = time.perf_counter() + TIME_FRACTION * observation.time_limit
        board, player, size = observation.board, observation.player, observation.size
        legal = list(observation.legal_moves)
        self.last_depth, self.last_nodes = 0, 0
        if len(legal) == 1:
            return legal[0]

        # Root ordering: full one-ply evaluation, as in ShortestPathBot.
        scored: list[tuple[float, float, Move]] = []
        for move in legal:
            score = evaluate(with_stone(board, move, player), player)
            if score >= WIN_SCORE:
                return move  # Immediate win.
            scored.append((-score, center_distance(move, size), move))
            if time.perf_counter() > deadline:
                break
        scored.sort()
        candidates = [move for _, _, move in scored[: self.max_candidates]]
        best = candidates[0]

        search = AlphaBetaSearch(self.max_candidates, deadline)
        max_depth = min(self.max_depth or len(legal), len(legal))
        for depth in range(1, max_depth + 1):
            try:
                move, value = search.search_root(board, player, candidates, depth)
            except OutOfTime:
                break
            best, self.last_depth = move, depth
            candidates.remove(move)
            candidates.insert(0, move)  # Principal variation first.
            if abs(value) >= WIN_SCORE:
                break  # Forced win or loss found: searching deeper changes nothing.
        self.last_nodes = search.nodes
        return best
