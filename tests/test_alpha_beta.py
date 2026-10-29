"""Tests for AlphaBetaBot, its search and the path-based move ordering."""

from __future__ import annotations

import math
import random
import time

import pytest

from hexarena.bots import BLUE, EMPTY, RED, Observation
from hexarena.bots.alpha_beta import AlphaBetaBot, AlphaBetaSearch, OutOfTime
from hexarena.bots.heuristics import (
    WIN_SCORE,
    distance_map,
    path_slack,
    shortest_path_distance,
    with_stone,
)
from hexarena.bots.random_bot import RandomBot
from hexarena.game import Board, HexGame, HexState, opponent, play_game


def board_from(rows: list[str]) -> Board:
    symbol = {".": EMPTY, "R": RED, "B": BLUE}
    return tuple(tuple(symbol[ch] for ch in row.replace(" ", "")) for row in rows)


def observe(rows: list[str], player: int, time_limit: float = 1.0) -> Observation:
    board = board_from(rows)
    game = HexGame(len(board))
    return game.observation(HexState(board=board, to_move=player), player, time_limit)


def random_open_position(size: int, stones: int, seed: int) -> HexState:
    game = HexGame(size)
    rng = random.Random(seed)
    while True:
        state = game.initial_state()
        for _ in range(stones):
            state = game.play(state, rng.choice(game.legal_moves(state)))
            if game.is_terminal(state):
                break
        if not game.is_terminal(state):
            return state


def plain_minimax(board: Board, to_move: int, depth: int) -> float:
    """Reference negamax WITHOUT pruning, same scoring as AlphaBetaSearch."""
    own = shortest_path_distance(board, to_move)
    if own == 0:
        return WIN_SCORE + depth
    rival = shortest_path_distance(board, opponent(to_move))
    if rival == 0:
        return -(WIN_SCORE + depth)
    if depth == 0:
        return rival - own
    size = len(board)
    return max(
        -plain_minimax(with_stone(board, (r, c), to_move), opponent(to_move), depth - 1)
        for r in range(size)
        for c in range(size)
        if board[r][c] == EMPTY
    )


# --------------------------------------------------------------------------- heuristics


def test_distance_map_on_empty_board() -> None:
    board = HexGame(3).initial_state().board
    top = distance_map(board, RED, from_start=True)
    bottom = distance_map(board, RED, from_start=False)
    assert top == [[1, 1, 1], [2, 2, 2], [3, 3, 3]]
    assert bottom == [[3, 3, 3], [2, 2, 2], [1, 1, 1]]
    left = distance_map(board, BLUE, from_start=True)
    assert [row[0] for row in left] == [1, 1, 1]


def test_distance_map_blocks_opponent_cells() -> None:
    board = board_from(["...", "BBB", "..."])
    top = distance_map(board, RED)
    assert top[2] == [math.inf] * 3


def test_every_cell_is_on_a_shortest_path_of_an_empty_board() -> None:
    board = HexGame(5).initial_state().board
    assert set(path_slack(board, RED).values()) == {0}
    assert set(path_slack(board, BLUE).values()) == {0}


def test_path_slack_marks_critical_cells() -> None:
    board = board_from(["...", ".R.", "..."])
    slack = path_slack(board, RED)
    assert slack[(0, 1)] == 0  # Above the red stone: on a shortest path.
    assert slack[(0, 0)] == 1  # One detour away.
    assert (1, 1) not in slack  # Occupied cells are not candidates.


# --------------------------------------------------------------------------- search correctness


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("depth", [1, 2, 3])
def test_alpha_beta_equals_plain_minimax(seed: int, depth: int) -> None:
    state = random_open_position(4, stones=4, seed=seed)
    search = AlphaBetaSearch(max_candidates=None)
    value = search.negamax(state.board, state.to_move, depth, -math.inf, math.inf)
    assert value == plain_minimax(state.board, state.to_move, depth)


def test_pruning_visits_fewer_nodes_than_full_tree() -> None:
    state = random_open_position(4, stones=2, seed=0)
    search = AlphaBetaSearch(max_candidates=None)
    search.negamax(state.board, state.to_move, 3, -math.inf, math.inf)
    empties = sum(row.count(EMPTY) for row in state.board)
    full_tree = 1 + empties + empties * (empties - 1) + empties * (empties - 1) * (empties - 2)
    assert search.nodes < full_tree / 3


def test_search_aborts_at_deadline() -> None:
    search = AlphaBetaSearch(deadline=time.perf_counter() - 1)
    with pytest.raises(OutOfTime):
        search.negamax(HexGame(5).initial_state().board, RED, 3, -math.inf, math.inf)


def test_ordered_moves_respects_candidate_limit() -> None:
    board = HexGame(7).initial_state().board
    assert len(AlphaBetaSearch(max_candidates=20).ordered_moves(board, RED)) == 20
    assert len(AlphaBetaSearch(max_candidates=None).ordered_moves(board, RED)) == 49


# --------------------------------------------------------------------------- bot behaviour


def test_takes_the_winning_move() -> None:
    obs = observe(["B.R..", "B.R..", "..R..", "B.R..", "....B"], RED)
    move = AlphaBetaBot().choose_move(obs)
    assert HexGame(5).play(HexState(board=obs.board, to_move=RED), move).winner == RED


def test_blocks_the_only_winning_cell() -> None:
    obs = observe(["B.R..", "B.R..", "..R..", "..R..", ".B..."], BLUE)
    assert AlphaBetaBot().choose_move(obs) == (4, 2)


def test_single_legal_move() -> None:
    board = ((RED, BLUE, RED), (BLUE, EMPTY, BLUE), (RED, BLUE, RED))
    obs = HexGame(3).observation(HexState(board=board, to_move=RED), RED)
    assert AlphaBetaBot().choose_move(obs) == (1, 1)


def test_iterative_deepening_goes_deeper_than_one_ply() -> None:
    bot = AlphaBetaBot()
    obs = HexGame(5).observation(random_open_position(5, 4, seed=1), RED, time_limit=1.0)
    bot.choose_move(obs)
    assert bot.last_depth >= 2
    assert bot.last_nodes > 0


def test_max_depth_is_respected() -> None:
    bot = AlphaBetaBot(max_depth=1)
    bot.choose_move(HexGame(5).observation(HexGame(5).initial_state(), RED, time_limit=1.0))
    assert bot.last_depth == 1


@pytest.mark.parametrize("size", [7, 11])
def test_respects_the_time_limit(size: int) -> None:
    obs = HexGame(size).observation(HexGame(size).initial_state(), RED, time_limit=0.3)
    start = time.perf_counter()
    move = AlphaBetaBot().choose_move(obs)
    assert time.perf_counter() - start < 0.3
    assert move in obs.legal_moves


def test_returns_a_legal_move_with_no_time() -> None:
    obs = HexGame(11).observation(HexGame(11).initial_state(), RED, time_limit=0.0)
    assert AlphaBetaBot().choose_move(obs) in obs.legal_moves


@pytest.mark.parametrize("bot_color", [RED, BLUE], ids=["as-red", "as-blue"])
def test_beats_random_bot(bot_color: int) -> None:
    game = HexGame(5)
    wins = 0
    for seed in range(4):
        bot, rival = AlphaBetaBot(), RandomBot(seed=seed)
        red, blue = (bot, rival) if bot_color == RED else (rival, bot)
        wins += play_game(game, red, blue, time_limit=0.1).winner == bot_color
    assert wins == 4
