"""Rules of Hex: legal moves, applying moves and win detection."""

from __future__ import annotations

from collections import deque

from hexarena.game.observation import Observation
from hexarena.game.state import BLUE, EMPTY, RED, Board, HexState, Move, opponent

NEIGHBOR_OFFSETS: tuple[Move, ...] = (
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
)
"""Offsets of the six neighbours of a cell in rhombus coordinates."""

_SYMBOLS = {EMPTY: ".", RED: "R", BLUE: "B"}


class IllegalMoveError(ValueError):
    """Raised when a move breaks the rules of the game."""


def neighbors(cell: Move, size: int) -> list[Move]:
    """Return the cells adjacent to ``cell`` that lie inside the board.

    Args:
        cell: The cell ``(row, col)``.
        size: Side length N of the board.

    Returns:
        Between 2 (acute corners) and 6 (interior) cells.
    """
    r, c = cell
    return [
        (r + dr, c + dc)
        for dr, dc in NEIGHBOR_OFFSETS
        if 0 <= r + dr < size and 0 <= c + dc < size
    ]


def _on_start_edge(cell: Move, player: int) -> bool:
    return cell[0] == 0 if player == RED else cell[1] == 0


def _on_end_edge(cell: Move, player: int, size: int) -> bool:
    return cell[0] == size - 1 if player == RED else cell[1] == size - 1


def _group_connects(board: Board, start: Move, player: int) -> bool:
    """BFS over the group containing ``start``: does it touch both of ``player``'s edges?"""
    size = len(board)
    touches_start = touches_end = False
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        touches_start = touches_start or _on_start_edge(cell, player)
        touches_end = touches_end or _on_end_edge(cell, player, size)
        if touches_start and touches_end:
            return True
        for nr, nc in neighbors(cell, size):
            if (nr, nc) not in seen and board[nr][nc] == player:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return False


def find_winner(board: Board) -> int | None:
    """Determine the winner of an arbitrary board from scratch.

    Unlike the incremental check used by :meth:`HexGame.play`, this
    function runs a BFS from each player's starting edge. It is useful
    for validating positions and in tests.

    Returns:
        ``RED``, ``BLUE`` or ``None`` if nobody has connected their edges.
    """
    size = len(board)
    for player in (RED, BLUE):
        starts = [(0, c) for c in range(size)] if player == RED else [(r, 0) for r in range(size)]
        seen: set[Move] = set()
        for cell in starts:
            if board[cell[0]][cell[1]] == player and cell not in seen:
                seen.add(cell)
                queue = deque([cell])
                while queue:
                    current = queue.popleft()
                    if _on_end_edge(current, player, size):
                        return player
                    for nr, nc in neighbors(current, size):
                        if (nr, nc) not in seen and board[nr][nc] == player:
                            seen.add((nr, nc))
                            queue.append((nr, nc))
    return None


class HexGame:
    """Rules of Hex on an N×N board.

    The class holds no game state: every method receives a
    :class:`HexState` and returns new values, so a single instance can be
    shared safely by the web app, the tournament and the bots.

    Example:
        >>> game = HexGame(size=3)
        >>> state = game.play(game.initial_state(), (1, 1))
        >>> game.current_player(state)
        2
    """

    def __init__(self, size: int = 11) -> None:
        """Create a game with an N×N board.

        Args:
            size: Side length of the board (11 by default).

        Raises:
            ValueError: If ``size`` is not a positive integer.
        """
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise ValueError(f"Board size must be a positive integer, got {size!r}")
        self.size = size

    def initial_state(self) -> HexState:
        """Return an empty board with Red to move."""
        row = (EMPTY,) * self.size
        return HexState(board=(row,) * self.size, to_move=RED, winner=None)

    def legal_moves(self, state: HexState) -> list[Move]:
        """Return the empty cells in row-major order, or ``[]`` if the game is over."""
        if state.winner is not None:
            return []
        return [
            (r, c)
            for r, row in enumerate(state.board)
            for c, value in enumerate(row)
            if value == EMPTY
        ]

    def current_player(self, state: HexState) -> int:
        """Return the player whose turn it is."""
        return state.to_move

    def is_terminal(self, state: HexState) -> bool:
        """Return ``True`` if the game has finished."""
        return state.winner is not None

    def winner(self, state: HexState) -> int | None:
        """Return the winner, or ``None`` if the game is still in progress."""
        return state.winner

    def play(self, state: HexState, move: Move) -> HexState:
        """Apply ``move`` for the current player and return the new state.

        The original state is not modified. Only the affected row is
        rebuilt; the other rows are shared with the previous state.

        Raises:
            IllegalMoveError: If the game is over, the move is malformed,
                the cell is off the board or the cell is occupied.
        """
        self._check_move(state, move)
        r, c = move
        player = state.to_move
        row = state.board[r]
        new_row = row[:c] + (player,) + row[c + 1 :]
        board = state.board[:r] + (new_row,) + state.board[r + 1 :]
        winner = player if _group_connects(board, (r, c), player) else None
        return HexState(board=board, to_move=opponent(player), winner=winner)

    def observation(
        self, state: HexState, player: int, time_limit: float = 1.0
    ) -> Observation:
        """Build the observation given to ``player``.

        Hex has perfect information, so the observation contains the full
        board.

        Args:
            state: Current state.
            player: The player who will receive the observation.
            time_limit: Seconds available to choose the move.
        """
        if player not in (RED, BLUE):
            raise ValueError(f"Invalid player: {player!r}")
        return Observation(
            board=state.board,
            size=state.size,
            player=player,
            legal_moves=tuple(self.legal_moves(state)),
            time_limit=time_limit,
        )

    def render_ascii(self, state: HexState) -> str:
        """Draw the board as text (useful for debugging).

        Columns are labelled with letters (a = 0) and rows with numbers
        starting at 0. Each row is shifted half a cell to the right,
        which forms the Hex rhombus.
        """
        letters = "abcdefghijklmnopqrstuvwxyz"
        col_labels = [letters[c] if c < len(letters) else "?" for c in range(state.size)]
        lines = ["    " + " ".join(col_labels)]
        for r, row in enumerate(state.board):
            cells = " ".join(_SYMBOLS[v] for v in row)
            lines.append(f"{r:>2}  " + " " * r + cells)
        if state.winner is not None:
            lines.append(f"Winner: {'Red' if state.winner == RED else 'Blue'}")
        else:
            lines.append(f"To move: {'Red' if state.to_move == RED else 'Blue'}")
        return "\n".join(lines)

    def _check_move(self, state: HexState, move: Move) -> None:
        if state.size != self.size:
            raise IllegalMoveError(
                f"The state is {state.size}x{state.size} but the game is "
                f"{self.size}x{self.size}"
            )
        if state.winner is not None:
            raise IllegalMoveError("The game is already over")
        if (
            not isinstance(move, tuple)
            or len(move) != 2
            or not all(isinstance(x, int) and not isinstance(x, bool) for x in move)
        ):
            raise IllegalMoveError(f"A move must be a tuple (row, col) of integers, got {move!r}")
        r, c = move
        if not (0 <= r < self.size and 0 <= c < self.size):
            raise IllegalMoveError(
                f"Cell {move} is off the board (valid range 0..{self.size - 1})"
            )
        if state.board[r][c] != EMPTY:
            raise IllegalMoveError(f"Cell {move} is already occupied")
