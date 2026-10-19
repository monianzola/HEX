"""Reusable evaluation functions for Hex bots.

The key idea is the *shortest-path distance*: how many more stones a
player needs to connect their two edges, assuming the opponent does not
move. It is computed with a 0-1 BFS where

* the player's own stones cost 0 (already placed),
* empty cells cost 1 (one stone must be placed there),
* opponent stones cannot be crossed.
"""

from __future__ import annotations

import math
from collections import deque

from hexarena.game.hex_game import neighbors
from hexarena.game.state import RED, Board, Move, opponent

WIN_SCORE = 10_000.0
"""Score of a position the player has already won (larger than any distance)."""


def shortest_path_distance(board: Board, player: int) -> float:
    """Return the number of stones ``player`` still needs to win.

    Uses 0-1 BFS (a Dijkstra specialised for edge weights 0 and 1): cells
    reached at cost 0 go to the front of the deque and cells reached at
    cost 1 to the back, so cells are popped in non-decreasing distance
    order. Complexity: O(N²) for an N×N board.

    Args:
        board: The board.
        player: ``RED`` (top-bottom) or ``BLUE`` (left-right).

    Returns:
        ``0`` if the player has already connected, ``math.inf`` if the
        opponent has blocked every path, otherwise a positive integer.
    """
    size = len(board)
    rival = opponent(player)
    dist = [[math.inf] * size for _ in range(size)]
    queue: deque[tuple[int, int, int]] = deque()

    starts = [(0, c) for c in range(size)] if player == RED else [(r, 0) for r in range(size)]
    for r, c in starts:
        if board[r][c] == rival:
            continue
        cost = 0 if board[r][c] == player else 1
        dist[r][c] = cost
        if cost == 0:
            queue.appendleft((cost, r, c))
        else:
            queue.append((cost, r, c))

    while queue:
        d, r, c = queue.popleft()
        if d > dist[r][c]:
            continue  # Stale entry: a cheaper path was found later.
        if (r if player == RED else c) == size - 1:
            return d
        for nr, nc in neighbors((r, c), size):
            value = board[nr][nc]
            if value == rival:
                continue
            step = 0 if value == player else 1
            nd = d + step
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if step == 0:
                    queue.appendleft((nd, nr, nc))
                else:
                    queue.append((nd, nr, nc))
    return math.inf


def evaluate(board: Board, player: int) -> float:
    """Score a board from ``player``'s point of view (higher is better).

    The score is ``opponent_distance - own_distance``: a position is good
    when we are close to connecting and the opponent is far.

    Returns:
        ``WIN_SCORE`` if ``player`` has connected, ``-WIN_SCORE`` if the
        opponent has, otherwise the distance difference.
    """
    own = shortest_path_distance(board, player)
    if own == 0:
        return WIN_SCORE
    rival = shortest_path_distance(board, opponent(player))
    if rival == 0:
        return -WIN_SCORE
    return rival - own


def with_stone(board: Board, move: Move, player: int) -> Board:
    """Return a copy of ``board`` with ``player``'s stone on ``move``.

    Only the affected row is rebuilt; the other rows are shared.
    """
    r, c = move
    row = board[r]
    return board[:r] + (row[:c] + (player,) + row[c + 1 :],) + board[r + 1 :]


def center_distance(move: Move, size: int) -> float:
    """Hex distance from ``move`` to the centre of the board.

    In rhombus coordinates the hex distance between two cells is
    ``(|dr| + |dc| + |dr + dc|) / 2``.
    """
    center = (size - 1) / 2
    dr, dc = move[0] - center, move[1] - center
    return (abs(dr) + abs(dc) + abs(dr + dc)) / 2
