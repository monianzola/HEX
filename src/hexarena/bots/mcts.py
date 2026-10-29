"""MCTSBot: Monte Carlo Tree Search with UCT (UCB1 applied to trees)."""

from __future__ import annotations

import math
import random
import time
from functools import lru_cache

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.game.hex_game import neighbors
from hexarena.game.state import BLUE, EMPTY, RED, Board, opponent

TIME_FRACTION = 0.8
"""Fraction of ``time_limit`` used for iterations."""

EXPLORATION = math.sqrt(2)
"""UCB1 exploration constant ``c``."""


def ucb1(wins: float, visits: int, parent_visits: int, c: float = EXPLORATION) -> float:
    """UCB1 score of a child: exploitation + exploration.

    ``wins / visits + c * sqrt(ln(parent_visits) / visits)``

    The first term is the observed win rate; the second grows for children
    visited rarely compared with their parent, so every move keeps being
    tried now and then. Unvisited children score ``inf`` (always tried first).
    """
    if visits == 0:
        return math.inf
    return wins / visits + c * math.sqrt(math.log(parent_visits) / visits)


@lru_cache(maxsize=None)
def _flat_neighbors(size: int) -> tuple[tuple[int, ...], ...]:
    """Neighbours of every cell, as indices ``r * size + c`` of a flat board."""
    return tuple(
        tuple(nr * size + nc for nr, nc in neighbors((r, c), size))
        for r in range(size)
        for c in range(size)
    )


def full_board_winner(cells: list[int], size: int) -> int:
    """Winner of a COMPLETELY filled flat board.

    On a full Hex board exactly one player is connected, so it is enough
    to check whether Red connects top and bottom.
    """
    adjacency = _flat_neighbors(size)
    stack = [c for c in range(size) if cells[c] == RED]
    seen = set(stack)
    last_row = size * (size - 1)
    while stack:
        cell = stack.pop()
        if cell >= last_row:
            return RED
        for nxt in adjacency[cell]:
            if nxt not in seen and cells[nxt] == RED:
                seen.add(nxt)
                stack.append(nxt)
    return BLUE


def _wins_now(board: Board, move: Move, player: int) -> bool:
    """Does ``player`` connect its edges by playing ``move``?"""
    size = len(board)
    r, c = move
    axis = 0 if player == RED else 1
    seen = {move}
    stack = [move]
    touches_start = touches_end = False
    while stack:
        cell = stack.pop()
        touches_start |= cell[axis] == 0
        touches_end |= cell[axis] == size - 1
        if touches_start and touches_end:
            return True
        for nr, nc in neighbors(cell, size):
            if (nr, nc) not in seen and board[nr][nc] == player:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return False


class Node:
    """A node of the search tree: the position after ``move``.

    ``wins`` counts simulations won by ``player_just_moved``, the player
    who made ``move``. Its parent picks children with that win rate, which
    is exactly the point of view of the player choosing.
    """

    __slots__ = ("move", "parent", "children", "untried", "visits", "wins", "player_just_moved")

    def __init__(self, move: int | None, parent: Node | None, player_just_moved: int, untried: list[int]) -> None:
        self.move = move
        self.parent = parent
        self.player_just_moved = player_just_moved
        self.untried = untried
        self.children: list[Node] = []
        self.visits = 0
        self.wins = 0.0

    def select_child(self, c: float) -> Node:
        """Child with the highest UCB1 score."""
        return max(self.children, key=lambda ch: ucb1(ch.wins, ch.visits, self.visits, c))


@register_bot("mcts")
class MCTSBot(Bot):
    """Monte Carlo Tree Search (UCT) with random full-board rollouts.

    Each iteration has four phases:

    1. **Selection**: walk down the tree choosing children by UCB1.
    2. **Expansion**: add one untried move as a new node.
    3. **Simulation**: fill the rest of the board at random, alternating
       colours, and see who connected.
    4. **Backpropagation**: update ``visits`` and ``wins`` up to the root.

    Iterations run until 80 % of the time limit (or ``max_iterations``) and
    the most visited root move is played.

    Args:
        seed: Seed of the bot's random generator.
        exploration: UCB1 constant ``c`` (``sqrt(2)`` by default).
        max_iterations: Optional cap on iterations (makes the bot
            deterministic for a given seed, useful in tests).
    """

    name = "MCTSBot"
    author = "hex-arena team"
    description = "Monte Carlo Tree Search (UCT, c=√2) con simulaciones aleatorias rellenando el tablero."

    def __init__(
        self,
        seed: int | None = None,
        exploration: float = EXPLORATION,
        max_iterations: int | None = None,
    ) -> None:
        self._rng = random.Random(seed)
        self.exploration = exploration
        self.max_iterations = max_iterations
        self.last_iterations = 0
        """Iterations run in the last call (for analysis and tests)."""

    def choose_move(self, observation: Observation) -> Move:
        """Run MCTS from the current position and return the most visited move."""
        deadline = time.perf_counter() + TIME_FRACTION * observation.time_limit
        board, size, player = observation.board, observation.size, observation.player
        legal = list(observation.legal_moves)
        self.last_iterations = 0
        if len(legal) == 1:
            return legal[0]

        # Safety checks that pure random simulations can miss.
        for move in legal:
            if _wins_now(board, move, player):
                return move
        rival = opponent(player)
        threats = [move for move in legal if _wins_now(board, move, rival)]
        if len(threats) == 1:
            return threats[0]

        root_cells = [cell for row in board for cell in row]
        empties = [r * size + c for r, c in legal]
        root = Node(None, None, rival, self._shuffled(empties))
        rng, c = self._rng, self.exploration

        iterations = 0
        while self._keep_going(iterations, deadline):
            node = root
            cells = root_cells.copy()
            to_move = player

            # 1. Selection.
            while not node.untried and node.children:
                node = node.select_child(c)
                cells[node.move] = to_move  # type: ignore[index]
                to_move = opponent(to_move)

            # 2. Expansion.
            if node.untried:
                move = node.untried.pop()
                cells[move] = to_move
                free = [i for i, v in enumerate(cells) if v == EMPTY]
                child = Node(move, node, to_move, self._shuffled(free))
                node.children.append(child)
                node = child
                to_move = opponent(to_move)

            # 3. Simulation: fill every empty cell, alternating colours.
            free = [i for i, v in enumerate(cells) if v == EMPTY]
            rng.shuffle(free)
            for i, cell in enumerate(free):
                cells[cell] = to_move if i % 2 == 0 else opponent(to_move)
            winner = full_board_winner(cells, size)

            # 4. Backpropagation.
            while node is not None:
                node.visits += 1
                if winner == node.player_just_moved:
                    node.wins += 1
                node = node.parent  # type: ignore[assignment]
            iterations += 1

        self.last_iterations = iterations
        if not root.children:
            return legal[0]
        best = max(root.children, key=lambda ch: (ch.visits, ch.wins))
        return divmod(best.move, size)  # type: ignore[arg-type,return-value]

    def _keep_going(self, iterations: int, deadline: float) -> bool:
        if self.max_iterations is not None:
            return iterations < self.max_iterations
        return time.perf_counter() < deadline

    def _shuffled(self, moves: list[int]) -> list[int]:
        moves = list(moves)
        self._rng.shuffle(moves)
        return moves
