"""BridgeBot: alpha-beta search with a heuristic that understands *bridges*.

A **bridge** is the most basic pattern in Hex: two cells that are not
adjacent but share two neighbours (the *carrier*, ``a`` and ``b``)::

     X a
      b X        X = the two ends of the bridge

The rival cannot cut a bridge: if they play ``a`` we answer ``b`` and vice
versa. So two stones joined by a bridge are, in practice, already
connected, while using one stone fewer than a solid chain. A chain of
bridges advances two rows per stone.
"""

from __future__ import annotations

import math
from collections import deque

from hexarena.bots import Move, register_bot
from hexarena.bots.alpha_beta import AlphaBetaBot, AlphaBetaSearch
from hexarena.game.hex_game import neighbors
from hexarena.game.state import RED, Board, opponent

BRIDGE_PATTERNS: tuple[tuple[Move, Move, Move], ...] = (
    ((1, 1), (0, 1), (1, 0)),
    ((2, -1), (1, -1), (1, 0)),
    ((1, -2), (0, -1), (1, -1)),
)
"""``(offset of the far end, carrier cell 1, carrier cell 2)``, all relative
to the *upper* end of the bridge.

There are six bridge directions, but they come in opposite pairs (the same
bridge seen from each end), so three patterns are enough:
:func:`bridge_jumps` uses each of them in both directions.
"""


def bridge_jumps(board: Board, cell: Move, rival: int) -> list[Move]:
    """Cells reachable from ``cell`` by jumping over a bridge.

    The jump is allowed when the far end is not a rival stone and the
    rival has no stone in either carrier cell (so the bridge cannot be cut).
    """
    size = len(board)
    r, c = cell
    jumps = []
    for (pr, pc), (ar, ac), (br, bc) in BRIDGE_PATTERNS:
        # ``cell`` can be the upper end (target below) or the lower end
        # (target above, and then the target is the upper end).
        for upper, target in (((r, c), (r + pr, c + pc)), ((r - pr, c - pc), (r - pr, c - pc))):
            tr, tc = target
            if not (0 <= tr < size and 0 <= tc < size) or board[tr][tc] == rival:
                continue
            a = (upper[0] + ar, upper[1] + ac)
            b = (upper[0] + br, upper[1] + bc)
            if board[a[0]][a[1]] != rival and board[b[0]][b[1]] != rival:
                jumps.append(target)
    return jumps


def bridge_distance(board: Board, player: int) -> float:
    """Stones ``player`` still needs to connect, if bridges count as links.

    The same 0-1 BFS as
    :func:`~hexarena.bots.heuristics.shortest_path_distance` (own stone =
    cost 0, empty cell = cost 1, rival stone = wall) with one extra kind of
    step: from any cell the path may also jump to the far end of a bridge,
    as if the two cells were neighbours (see :func:`bridge_jumps`).

    Returns:
        ``0`` if already connected through stones and/or bridges,
        ``math.inf`` if every path is blocked, otherwise a positive integer.
    """
    size = len(board)
    rival = opponent(player)
    axis = 0 if player == RED else 1  # Coordinate that must go from 0 to size-1.
    dist = [[math.inf] * size for _ in range(size)]
    queue: deque[tuple[float, int, int]] = deque()

    starts = [(0, c) for c in range(size)] if player == RED else [(r, 0) for r in range(size)]
    for r, c in starts:
        if board[r][c] != rival:
            cost = 0 if board[r][c] == player else 1
            dist[r][c] = cost
            (queue.appendleft if cost == 0 else queue.append)((cost, r, c))

    while queue:
        d, r, c = queue.popleft()
        if d > dist[r][c]:
            continue  # Stale entry.
        if (r, c)[axis] == size - 1:
            return d
        for nr, nc in neighbors((r, c), size) + bridge_jumps(board, (r, c), rival):
            value = board[nr][nc]
            if value == rival:
                continue
            step = 0 if value == player else 1
            if d + step < dist[nr][nc]:
                dist[nr][nc] = d + step
                (queue.appendleft if step == 0 else queue.append)((d + step, nr, nc))
    return math.inf


class BridgeSearch(AlphaBetaSearch):
    """The same alpha-beta search, with bridges added to the leaf evaluation."""

    def evaluate_leaf(self, board: Board, to_move: int, own: float, rival: float) -> float:
        """Plain path difference plus path difference counting bridges.

        ``(rival - own) + (rival_with_bridges - own_with_bridges)``

        The first term (the one :class:`AlphaBetaBot` uses) counts stones
        cell by cell. The second one rewards positions whose paths are
        made of bridges, which the rival cannot cut. Using both keeps the
        exact count while breaking its ties in favour of solid shapes.
        """
        with_bridges = bridge_distance(board, opponent(to_move)) - bridge_distance(board, to_move)
        return (rival - own) + with_bridges


@register_bot("bridges")
class BridgeBot(AlphaBetaBot):
    """AlphaBetaBot whose heuristic understands bridges.

    The search is exactly the one of
    :class:`~hexarena.bots.alpha_beta.AlphaBetaBot` (negamax, alpha-beta
    pruning, iterative deepening, 20 candidates per node). Only the
    evaluation of the leaves changes: see :meth:`BridgeSearch.evaluate_leaf`.
    """

    name = "BridgeBot"
    author = "hex-arena team"
    description = "Alfa-beta con heurística de caminos que cuenta los puentes como conexiones."
    search_class = BridgeSearch
