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
from hexarena.game.state import EMPTY, RED, Board, Move, opponent

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


def distance_map(board: Board, player: int, from_start: bool = True) -> list[list[float]]:
    """Cheapest cost to reach every cell from one of ``player``'s edges.

    Same 0-1 BFS as :func:`shortest_path_distance`, but it does not stop at
    the goal and returns the whole grid. The cost of a cell includes the
    cell itself (0 if it is the player's stone, 1 if empty); opponent
    cells stay at ``math.inf``.

    Args:
        board: The board.
        player: ``RED`` or ``BLUE``.
        from_start: Start from the first edge (top/left) if ``True``,
            otherwise from the second edge (bottom/right).
    """
    size = len(board)
    rival = opponent(player)
    edge = 0 if from_start else size - 1
    starts = [(edge, c) for c in range(size)] if player == RED else [(r, edge) for r in range(size)]
    dist = [[math.inf] * size for _ in range(size)]
    queue: deque[tuple[float, int, int]] = deque()
    for r, c in starts:
        if board[r][c] == rival:
            continue
        cost = 0 if board[r][c] == player else 1
        dist[r][c] = cost
        (queue.appendleft if cost == 0 else queue.append)((cost, r, c))
    while queue:
        d, r, c = queue.popleft()
        if d > dist[r][c]:
            continue
        for nr, nc in neighbors((r, c), size):
            value = board[nr][nc]
            if value == rival:
                continue
            step = 0 if value == player else 1
            if d + step < dist[nr][nc]:
                dist[nr][nc] = d + step
                (queue.appendleft if step == 0 else queue.append)((d + step, nr, nc))
    return dist


def path_slack(board: Board, player: int) -> dict[Move, float]:
    """For every empty cell, how far it is from lying on a shortest path.

    ``slack = (cheapest path forced through the cell) - (cheapest path overall)``.
    A slack of 0 means the cell is on one of ``player``'s shortest paths, so
    it is critical: playing there helps that player, and the opponent
    playing there blocks them. Cells that cannot be part of any path are
    left out.
    """
    size = len(board)
    top = distance_map(board, player, from_start=True)
    bottom = distance_map(board, player, from_start=False)
    best = min(
        (top[r][c] for r in range(size) for c in range(size)
         if (r if player == RED else c) == size - 1),
        default=math.inf,
    )
    slack: dict[Move, float] = {}
    for r in range(size):
        for c in range(size):
            if board[r][c] == EMPTY:
                through = top[r][c] + bottom[r][c] - 1  # The cell is counted twice.
                if through < math.inf:
                    slack[(r, c)] = through - best
    return slack
