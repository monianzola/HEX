"""Tests for the shortest-path heuristic and ShortestPathBot."""

from __future__ import annotations

import math

import pytest

from hexarena.bots import BLUE, EMPTY, RED, Observation
from hexarena.bots.heuristics import (
    WIN_SCORE,
    center_distance,
    evaluate,
    shortest_path_distance,
    with_stone,
)
from hexarena.bots.random_bot import RandomBot
from hexarena.bots.shortest_path import ShortestPathBot
from hexarena.game import Board, HexGame, HexState, play_game


def board_from(rows: list[str]) -> Board:
    symbol = {".": EMPTY, "R": RED, "B": BLUE}
    return tuple(tuple(symbol[ch] for ch in row.replace(" ", "")) for row in rows)


def observe(rows: list[str], player: int, time_limit: float = 1.0) -> Observation:
    board = board_from(rows)
    game = HexGame(len(board))
    return game.observation(HexState(board=board, to_move=player), player, time_limit)


# --------------------------------------------------------------------------- heuristic


@pytest.mark.parametrize("size", [1, 3, 7, 11])
def test_distance_on_empty_board_is_board_size(size: int) -> None:
    board = HexGame(size).initial_state().board
    assert shortest_path_distance(board, RED) == size
    assert shortest_path_distance(board, BLUE) == size


def test_own_stones_cost_zero() -> None:
    board = board_from(["...", ".R.", "..."])
    assert shortest_path_distance(board, RED) == 2
    assert shortest_path_distance(board, BLUE) == 3


def test_distance_follows_hex_diagonal() -> None:
    board = board_from(["..R", ".R.", "..."])
    assert shortest_path_distance(board, RED) == 1  # (2,0) completes the path.


def test_connected_player_has_distance_zero() -> None:
    board = board_from([".R.", ".R.", ".R."])
    assert shortest_path_distance(board, RED) == 0


def test_blocked_player_has_infinite_distance() -> None:
    board = board_from(["...", "BBB", "..."])
    assert shortest_path_distance(board, RED) == math.inf
    assert shortest_path_distance(board, BLUE) == 0


def test_opponent_stones_force_a_detour() -> None:
    #   . . .
    #    B B .
    #     . . .
    board = board_from(["...", "BB.", "..."])
    assert shortest_path_distance(board, RED) == 3  # Must pass through (1,2).


def test_evaluate() -> None:
    assert evaluate(board_from([".R.", ".R.", ".R."]), RED) == WIN_SCORE
    assert evaluate(board_from([".R.", ".R.", ".R."]), BLUE) == -WIN_SCORE
    assert evaluate(board_from(["...", ".R.", "..."]), RED) == 1  # 3 - 2
    assert evaluate(board_from(["...", ".R.", "..."]), BLUE) == -1


def test_evaluate_is_zero_sum_on_empty_board() -> None:
    board = HexGame(5).initial_state().board
    assert evaluate(board, RED) == evaluate(board, BLUE) == 0


def test_with_stone_does_not_modify_original() -> None:
    board = HexGame(3).initial_state().board
    new = with_stone(board, (1, 2), BLUE)
    assert board[1][2] == EMPTY
    assert new[1][2] == BLUE
    assert new[0] is board[0]


def test_center_distance() -> None:
    assert center_distance((2, 2), 5) == 0
    assert center_distance((1, 2), 5) == 1
    assert center_distance((1, 3), 5) == 1  # Hex neighbour of the centre.
    assert center_distance((1, 1), 5) == 2  # Not a hex neighbour.
    assert center_distance((0, 0), 5) == 4


# --------------------------------------------------------------------------- bot


@pytest.mark.parametrize("size", [3, 5, 7, 11])
def test_first_move_is_the_center(size: int) -> None:
    obs = HexGame(size).observation(HexGame(size).initial_state(), RED)
    assert ShortestPathBot().choose_move(obs) == (size // 2, size // 2)


def test_takes_the_winning_move() -> None:
    obs = observe(
        [
            "B.R..",
            "B.R..",
            "..R..",
            "B.R..",
            "....B",
        ],
        RED,
    )
    move = ShortestPathBot().choose_move(obs)
    assert move in {(4, 1), (4, 2)}  # Both complete Red's column.
    assert HexGame(5).play(HexState(board=obs.board, to_move=RED), move).winner == RED


def test_blocks_the_only_winning_cell() -> None:
    obs = observe(
        [
            "B.R..",
            "B.R..",
            "..R..",
            "..R..",
            ".B...",
        ],
        BLUE,
    )
    assert ShortestPathBot().choose_move(obs) == (4, 2)


def test_blue_takes_its_winning_move() -> None:
    obs = observe(
        [
            "R....",
            "R....",
            "BBBB.",
            ".R...",
            "....R",
        ],
        BLUE,
    )
    assert ShortestPathBot().choose_move(obs) in {(2, 4), (1, 4)}


def test_is_deterministic() -> None:
    obs = observe(["R....", ".....", "..B..", ".....", "....."], RED)
    assert ShortestPathBot().choose_move(obs) == ShortestPathBot().choose_move(obs)


def test_returns_a_legal_move_even_with_no_time() -> None:
    game = HexGame(11)
    obs = game.observation(game.initial_state(), RED, time_limit=0.0)
    assert ShortestPathBot().choose_move(obs) in obs.legal_moves


@pytest.mark.parametrize("bot_color", [RED, BLUE], ids=["as-red", "as-blue"])
def test_beats_random_bot_almost_always(bot_color: int) -> None:
    game = HexGame(7)
    wins = 0
    for seed in range(10):
        bot, rival = ShortestPathBot(), RandomBot(seed=seed)
        red, blue = (bot, rival) if bot_color == RED else (rival, bot)
        wins += play_game(game, red, blue).winner == bot_color
    assert wins >= 9
