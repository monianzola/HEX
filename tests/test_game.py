"""Tests for the Hex rules: geometry, wins, illegal moves and immutability."""

from __future__ import annotations

import dataclasses
import random
from collections import deque

import pytest

from hexarena.game import (
    BLUE,
    EMPTY,
    RED,
    Board,
    HexGame,
    HexState,
    IllegalMoveError,
    Move,
    find_winner,
    neighbors,
    opponent,
)

# --------------------------------------------------------------------------- helpers


def board_from(rows: list[str]) -> Board:
    """Build a board from strings: '.' empty, 'R' red, 'B' blue."""
    symbol = {".": EMPTY, "R": RED, "B": BLUE}
    return tuple(tuple(symbol[ch] for ch in row.replace(" ", "")) for row in rows)


def play_all(game: HexGame, moves: list[Move]) -> HexState:
    state = game.initial_state()
    for move in moves:
        state = game.play(state, move)
    return state


def connects(board: Board, player: int) -> bool:
    """Independent reference check, written without the library's helpers."""
    n = len(board)
    offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    if player == RED:
        start = [(0, c) for c in range(n) if board[0][c] == RED]
        is_goal = lambda r, c: r == n - 1  # noqa: E731
    else:
        start = [(r, 0) for r in range(n) if board[r][0] == BLUE]
        is_goal = lambda r, c: c == n - 1  # noqa: E731
    seen = set(start)
    queue = deque(start)
    while queue:
        r, c = queue.popleft()
        if is_goal(r, c):
            return True
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen and board[nr][nc] == player:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return False


# --------------------------------------------------------------------------- construction


@pytest.mark.parametrize("size", [1, 3, 7, 11])
def test_initial_state_is_empty_and_red_moves_first(size: int) -> None:
    game = HexGame(size)
    state = game.initial_state()
    assert state.size == size
    assert all(cell == EMPTY for row in state.board for cell in row)
    assert game.current_player(state) == RED
    assert not game.is_terminal(state)
    assert game.winner(state) is None
    assert len(game.legal_moves(state)) == size * size


def test_default_size_is_11() -> None:
    assert HexGame().size == 11


@pytest.mark.parametrize("size", [0, -1, 2.5, "7", True, None])
def test_invalid_board_size_raises(size: object) -> None:
    with pytest.raises(ValueError):
        HexGame(size)  # type: ignore[arg-type]


def test_opponent() -> None:
    assert opponent(RED) == BLUE
    assert opponent(BLUE) == RED
    with pytest.raises(ValueError):
        opponent(EMPTY)


# --------------------------------------------------------------------------- neighbour geometry


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        # Acute corners (2 neighbours).
        ((0, 0), {(0, 1), (1, 0)}),
        ((4, 4), {(3, 4), (4, 3)}),
        # Obtuse corners (3 neighbours).
        ((0, 4), {(0, 3), (1, 3), (1, 4)}),
        ((4, 0), {(3, 0), (3, 1), (4, 1)}),
        # Edges (4 neighbours).
        ((0, 2), {(0, 1), (0, 3), (1, 1), (1, 2)}),
        ((4, 2), {(3, 2), (3, 3), (4, 1), (4, 3)}),
        ((2, 0), {(1, 0), (1, 1), (2, 1), (3, 0)}),
        ((2, 4), {(1, 4), (2, 3), (3, 3), (3, 4)}),
        # Interior (6 neighbours).
        ((2, 2), {(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)}),
    ],
)
def test_neighbors_on_5x5(cell: Move, expected: set[Move]) -> None:
    assert set(neighbors(cell, 5)) == expected


def test_diagonal_main_axis_is_not_adjacent() -> None:
    # (r-1, c-1) and (r+1, c+1) are NOT neighbours on a hex board.
    assert (1, 1) not in neighbors((2, 2), 5)
    assert (3, 3) not in neighbors((2, 2), 5)


def test_single_cell_board_has_no_neighbors() -> None:
    assert neighbors((0, 0), 1) == []


@pytest.mark.parametrize("size", [1, 2, 3, 11])
def test_neighbor_relation_is_symmetric(size: int) -> None:
    for r in range(size):
        for c in range(size):
            for other in neighbors((r, c), size):
                assert (r, c) in neighbors(other, size)


# --------------------------------------------------------------------------- winning


def test_red_wins_with_vertical_line() -> None:
    game = HexGame(3)
    state = play_all(game, [(0, 1), (0, 0), (1, 1), (1, 0), (2, 1)])
    assert game.is_terminal(state)
    assert game.winner(state) == RED


def test_red_wins_with_hex_diagonal() -> None:
    # (0,2) -> (1,1) -> (2,0) are adjacent on a hex board.
    game = HexGame(3)
    state = play_all(game, [(0, 2), (0, 0), (1, 1), (2, 2), (2, 0)])
    assert game.winner(state) == RED


def test_blue_wins_with_horizontal_line() -> None:
    game = HexGame(3)
    state = play_all(game, [(0, 0), (1, 0), (0, 1), (1, 1), (2, 2), (1, 2)])
    assert game.is_terminal(state)
    assert game.winner(state) == BLUE


def test_red_horizontal_line_is_not_a_win() -> None:
    game = HexGame(3)
    state = play_all(game, [(1, 0), (0, 0), (1, 1), (2, 0), (1, 2)])
    assert not game.is_terminal(state)
    assert game.winner(state) is None


def test_blue_vertical_line_is_not_a_win() -> None:
    game = HexGame(3)
    state = play_all(game, [(0, 0), (0, 1), (2, 2), (1, 1), (0, 2), (2, 1)])
    assert game.winner(state) is None


def test_win_on_1x1_board() -> None:
    game = HexGame(1)
    state = game.play(game.initial_state(), (0, 0))
    assert game.winner(state) == RED
    assert game.legal_moves(state) == []


def test_red_wins_on_11x11() -> None:
    game = HexGame(11)
    moves: list[Move] = []
    for r in range(11):
        moves.append((r, 5))  # Red builds column 5.
        if r < 10:
            moves.append((r, 0))  # Blue plays along column 0 (not a win for Blue).
    state = play_all(game, moves)
    assert game.winner(state) == RED
    assert len(moves) == 21


def test_win_detected_when_last_stone_joins_two_groups() -> None:
    game = HexGame(5)
    red = [(0, 2), (1, 2), (3, 2), (4, 2)]
    blue = [(0, 0), (1, 0), (3, 0), (4, 0)]
    moves = [m for pair in zip(red, blue) for m in pair]
    state = play_all(game, moves)
    assert game.winner(state) is None
    state = game.play(state, (2, 2))  # Bridges the top and bottom groups.
    assert game.winner(state) == RED


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (["R..", ".R.", "..R"], None),  # Main diagonal is not connected.
        (["..R", ".R.", "R.."], RED),
        ([".R.", ".R.", ".R."], RED),
        (["...", "BBB", "..."], BLUE),
        (["B..", ".B.", "..B"], None),
        (["...", "...", "..."], None),
    ],
)
def test_find_winner(rows: list[str], expected: int | None) -> None:
    assert find_winner(board_from(rows)) == expected


@pytest.mark.parametrize("size", [1, 2, 3, 5, 7, 11])
def test_a_full_board_always_has_exactly_one_winner(size: int) -> None:
    """Hex theorem: no draws. Checked on many random full boards (fixed seed)."""
    rng = random.Random(1234 + size)
    for _ in range(200):
        board = tuple(tuple(rng.choice((RED, BLUE)) for _ in range(size)) for _ in range(size))
        red, blue = connects(board, RED), connects(board, BLUE)
        assert red != blue, f"Expected exactly one winner on {board}"
        assert find_winner(board) == (RED if red else BLUE)


@pytest.mark.parametrize("size", [1, 2, 3, 5, 11])
def test_random_games_always_end_with_a_winner(size: int) -> None:
    rng = random.Random(42 + size)
    game = HexGame(size)
    for _ in range(100):
        state = game.initial_state()
        while not game.is_terminal(state):
            state = game.play(state, rng.choice(game.legal_moves(state)))
        assert game.winner(state) in (RED, BLUE)
        # The incremental check agrees with a full recomputation.
        assert find_winner(state.board) == game.winner(state)
        assert connects(state.board, game.winner(state))


# --------------------------------------------------------------------------- illegal moves


def test_occupied_cell_is_illegal() -> None:
    game = HexGame(3)
    state = game.play(game.initial_state(), (1, 1))
    with pytest.raises(IllegalMoveError, match="occupied"):
        game.play(state, (1, 1))


@pytest.mark.parametrize("move", [(-1, 0), (0, -1), (3, 0), (0, 3), (10, 10)])
def test_out_of_range_is_illegal(move: Move) -> None:
    game = HexGame(3)
    with pytest.raises(IllegalMoveError, match="off the board"):
        game.play(game.initial_state(), move)


@pytest.mark.parametrize("move", [[0, 0], (0,), (0, 0, 0), (0.0, 0), ("0", "0"), (True, 0), None])
def test_malformed_move_is_illegal(move: object) -> None:
    game = HexGame(3)
    with pytest.raises(IllegalMoveError, match="tuple"):
        game.play(game.initial_state(), move)  # type: ignore[arg-type]


def test_move_after_game_over_is_illegal() -> None:
    game = HexGame(1)
    state = game.play(game.initial_state(), (0, 0))
    with pytest.raises(IllegalMoveError, match="over"):
        game.play(state, (0, 0))


def test_state_from_other_board_size_is_illegal() -> None:
    with pytest.raises(IllegalMoveError):
        HexGame(5).play(HexGame(3).initial_state(), (0, 0))


def test_illegal_move_error_is_a_value_error() -> None:
    assert issubclass(IllegalMoveError, ValueError)


# --------------------------------------------------------------------------- immutability


def test_play_does_not_modify_the_original_state() -> None:
    game = HexGame(3)
    before = game.initial_state()
    snapshot = before.board
    after = game.play(before, (1, 1))
    assert before.board == snapshot
    assert before.board[1][1] == EMPTY
    assert after.board[1][1] == RED
    assert before.to_move == RED and after.to_move == BLUE


def test_state_is_frozen() -> None:
    state = HexGame(3).initial_state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.to_move = BLUE  # type: ignore[misc]
    assert isinstance(state.board, tuple)
    assert all(isinstance(row, tuple) for row in state.board)


def test_unchanged_rows_are_shared_between_states() -> None:
    game = HexGame(5)
    before = game.initial_state()
    after = game.play(before, (2, 3))
    for r in (0, 1, 3, 4):
        assert after.board[r] is before.board[r]
    assert after.board[2] is not before.board[2]


def test_states_are_hashable_and_comparable() -> None:
    game = HexGame(3)
    a = game.play(game.initial_state(), (0, 0))
    b = game.play(game.initial_state(), (0, 0))
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


# --------------------------------------------------------------------------- legal moves, observation, rendering


def test_legal_moves_are_empty_cells_in_row_major_order() -> None:
    game = HexGame(2)
    state = game.play(game.initial_state(), (0, 1))
    assert game.legal_moves(state) == [(0, 0), (1, 0), (1, 1)]


def test_observation_contents() -> None:
    game = HexGame(3)
    state = game.play(game.initial_state(), (1, 1))
    obs = game.observation(state, BLUE, time_limit=0.5)
    assert obs.board is state.board
    assert obs.size == 3
    assert obs.player == BLUE
    assert obs.time_limit == 0.5
    assert isinstance(obs.legal_moves, tuple)
    assert obs.legal_moves == tuple(game.legal_moves(state))
    with pytest.raises(dataclasses.FrozenInstanceError):
        obs.player = RED  # type: ignore[misc]


def test_observation_rejects_invalid_player() -> None:
    game = HexGame(3)
    with pytest.raises(ValueError):
        game.observation(game.initial_state(), 3)


def test_render_ascii() -> None:
    game = HexGame(3)
    state = play_all(game, [(0, 1), (1, 0)])
    text = game.render_ascii(state)
    lines = text.splitlines()
    assert lines[0] == "    a b c"
    assert lines[1] == " 0  . R ."
    assert lines[2] == " 1   B . ."
    assert lines[3] == " 2    . . ."
    assert lines[4] == "To move: Red"


def test_render_ascii_shows_winner() -> None:
    game = HexGame(1)
    state = game.play(game.initial_state(), (0, 0))
    assert game.render_ascii(state).endswith("Winner: Red")
