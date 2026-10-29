"""Tests for MCTSBot: UCB1, rollouts and behaviour."""

from __future__ import annotations

import math
import random
import time

import pytest

from hexarena.bots import BLUE, EMPTY, RED, Observation
from hexarena.bots.mcts import EXPLORATION, MCTSBot, Node, full_board_winner, ucb1
from hexarena.bots.random_bot import RandomBot
from hexarena.game import Board, HexGame, HexState, find_winner, play_game


def board_from(rows: list[str]) -> Board:
    symbol = {".": EMPTY, "R": RED, "B": BLUE}
    return tuple(tuple(symbol[ch] for ch in row.replace(" ", "")) for row in rows)


def observe(rows: list[str], player: int, time_limit: float = 1.0) -> Observation:
    board = board_from(rows)
    game = HexGame(len(board))
    return game.observation(HexState(board=board, to_move=player), player, time_limit)


# --------------------------------------------------------------------------- UCB1


def test_ucb1_formula() -> None:
    assert ucb1(3, 4, 10) == pytest.approx(3 / 4 + math.sqrt(2) * math.sqrt(math.log(10) / 4))
    assert EXPLORATION == pytest.approx(math.sqrt(2))


def test_unvisited_children_are_tried_first() -> None:
    assert ucb1(0, 0, 10) == math.inf


def test_exploration_term_favours_rarely_visited_moves() -> None:
    # Same win rate, fewer visits -> higher score.
    assert ucb1(5, 10, 1000) > ucb1(50, 100, 1000)


def test_exploration_constant_zero_is_pure_exploitation() -> None:
    assert ucb1(7, 10, 1000, c=0) == pytest.approx(0.7)


def test_select_child_uses_ucb1() -> None:
    root = Node(None, None, BLUE, [])
    root.visits = 100
    for move, (wins, visits) in enumerate([(30, 50), (9, 10), (20, 40)]):
        child = Node(move, root, RED, [])
        child.wins, child.visits = wins, visits
        root.children.append(child)
    assert root.select_child(EXPLORATION).move == 1


# --------------------------------------------------------------------------- rollouts


@pytest.mark.parametrize("size", [1, 2, 3, 5, 7, 11])
def test_full_board_winner_matches_game_logic(size: int) -> None:
    rng = random.Random(size)
    for _ in range(200):
        cells = [rng.choice((RED, BLUE)) for _ in range(size * size)]
        board = tuple(tuple(cells[r * size : (r + 1) * size]) for r in range(size))
        assert full_board_winner(cells, size) == find_winner(board)


# --------------------------------------------------------------------------- bot behaviour


def test_takes_the_winning_move() -> None:
    obs = observe(["B.R..", "B.R..", "..R..", "B.R..", "....B"], RED)
    move = MCTSBot(seed=0).choose_move(obs)
    assert HexGame(5).play(HexState(board=obs.board, to_move=RED), move).winner == RED


def test_blocks_a_single_winning_threat() -> None:
    obs = observe(["B.R..", "B.R..", "..R..", "..R..", ".B..."], BLUE)
    assert MCTSBot(seed=0).choose_move(obs) == (4, 2)


def test_single_legal_move() -> None:
    board = ((RED, BLUE, RED), (BLUE, EMPTY, BLUE), (RED, BLUE, RED))
    obs = HexGame(3).observation(HexState(board=board, to_move=RED), RED)
    assert MCTSBot().choose_move(obs) == (1, 1)


def test_is_reproducible_with_seed_and_iteration_cap() -> None:
    obs = HexGame(7).observation(HexGame(7).initial_state(), RED)
    a = MCTSBot(seed=3, max_iterations=500).choose_move(obs)
    b = MCTSBot(seed=3, max_iterations=500).choose_move(obs)
    assert a == b


def test_runs_the_requested_iterations() -> None:
    bot = MCTSBot(seed=1, max_iterations=300)
    bot.choose_move(HexGame(5).observation(HexGame(5).initial_state(), RED))
    assert bot.last_iterations == 300


def test_prefers_the_center_on_an_empty_board() -> None:
    """With enough simulations, central cells win more often than corners."""
    obs = HexGame(5).observation(HexGame(5).initial_state(), RED)
    r, c = MCTSBot(seed=0, max_iterations=4000).choose_move(obs)
    assert 1 <= r <= 3 and 1 <= c <= 3


@pytest.mark.parametrize("size", [7, 11])
def test_respects_the_time_limit(size: int) -> None:
    obs = HexGame(size).observation(HexGame(size).initial_state(), RED, time_limit=0.3)
    bot = MCTSBot(seed=0)
    start = time.perf_counter()
    move = bot.choose_move(obs)
    assert time.perf_counter() - start < 0.3
    assert move in obs.legal_moves
    assert bot.last_iterations > 0


def test_returns_a_legal_move_with_no_time() -> None:
    obs = HexGame(7).observation(HexGame(7).initial_state(), RED, time_limit=0.0)
    assert MCTSBot().choose_move(obs) in obs.legal_moves


@pytest.mark.parametrize("bot_color", [RED, BLUE], ids=["as-red", "as-blue"])
def test_beats_random_bot(bot_color: int) -> None:
    game = HexGame(5)
    wins = 0
    for seed in range(4):
        bot, rival = MCTSBot(seed=seed), RandomBot(seed=seed)
        red, blue = (bot, rival) if bot_color == RED else (rival, bot)
        wins += play_game(game, red, blue, time_limit=0.1).winner == bot_color
    assert wins == 4
