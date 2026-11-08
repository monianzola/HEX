"""Tests for BridgeBot, its bridge jumps and its bridge-aware distance."""

from __future__ import annotations

import random
import time

import pytest

from hexarena.bots import BLUE, EMPTY, RED, Observation
from hexarena.bots.alpha_beta import AlphaBetaBot, AlphaBetaSearch
from hexarena.bots.bridges import BridgeBot, BridgeSearch, bridge_distance, bridge_jumps
from hexarena.bots.heuristics import shortest_path_distance
from hexarena.bots.random_bot import RandomBot
from hexarena.game import Board, HexGame, HexState, neighbors, play_game


def board_from(rows: list[str]) -> Board:
    symbol = {".": EMPTY, "R": RED, "B": BLUE}
    return tuple(tuple(symbol[ch] for ch in row.replace(" ", "")) for row in rows)


def observe(rows: list[str], player: int, time_limit: float = 1.0) -> Observation:
    board = board_from(rows)
    game = HexGame(len(board))
    return game.observation(HexState(board=board, to_move=player), player, time_limit)


# --------------------------------------------------------------------------- bridge_jumps


def test_a_central_cell_has_six_bridges() -> None:
    board = HexGame(5).initial_state().board
    jumps = bridge_jumps(board, (2, 2), BLUE)
    assert sorted(jumps) == sorted([(3, 3), (1, 1), (4, 1), (0, 3), (3, 0), (1, 4)])


def test_every_jump_shares_exactly_two_neighbours() -> None:
    """That is the definition of a bridge: two common neighbours, not adjacent."""
    size = 7
    board = HexGame(size).initial_state().board
    for r in range(size):
        for c in range(size):
            for target in bridge_jumps(board, (r, c), BLUE):
                assert target not in neighbors((r, c), size)
                assert len(set(neighbors((r, c), size)) & set(neighbors(target, size))) == 2


def test_jumps_stay_inside_the_board() -> None:
    board = HexGame(5).initial_state().board
    assert sorted(bridge_jumps(board, (0, 0), BLUE)) == [(1, 1)]


def test_a_rival_stone_in_the_carrier_cuts_the_bridge() -> None:
    board = board_from([
        "R . .",
        ". B .",
        ". . .",
    ])
    # (0,0)-(1,1) is a bridge whose carrier is (0,1) and (1,0): still free.
    assert (1, 1) not in bridge_jumps(board, (0, 0), BLUE)  # Target is a rival stone.
    board = board_from([
        "R B .",
        ". . .",
        ". . .",
    ])
    assert (1, 1) not in bridge_jumps(board, (0, 0), BLUE)  # Carrier cell taken.
    assert (1, 1) in bridge_jumps(board, (0, 0), RED)  # Blue's own stone does not cut.


# --------------------------------------------------------------------------- bridge_distance


@pytest.mark.parametrize("size", [3, 5, 7, 11])
def test_empty_board_needs_one_stone_every_two_rows(size: int) -> None:
    board = HexGame(size).initial_state().board
    assert shortest_path_distance(board, RED) == size
    assert bridge_distance(board, RED) == (size + 1) // 2
    assert bridge_distance(board, BLUE) == (size + 1) // 2


def test_two_stones_joined_by_a_bridge_are_connected() -> None:
    board = board_from([
        ". R .",
        ". . .",
        "R . .",
    ])
    assert shortest_path_distance(board, RED) == 1
    assert bridge_distance(board, RED) == 0


def test_cutting_the_bridge_costs_a_stone() -> None:
    board = board_from([
        ". R .",
        "B . .",
        "R . .",
    ])
    assert bridge_distance(board, RED) == 1


def test_never_larger_than_the_plain_distance() -> None:
    game = HexGame(7)
    rng = random.Random(0)
    for _ in range(50):
        state = game.initial_state()
        for _ in range(rng.randint(0, 20)):
            if game.is_terminal(state):
                break
            state = game.play(state, rng.choice(game.legal_moves(state)))
        for player in (RED, BLUE):
            assert bridge_distance(state.board, player) <= shortest_path_distance(state.board, player)


def test_blocked_player_has_infinite_distance() -> None:
    board = board_from([
        "B B B",
        ". . .",
        ". . .",
    ])
    assert bridge_distance(board, RED) == float("inf")


# --------------------------------------------------------------------------- search and bot


def test_alpha_beta_leaf_is_the_path_difference() -> None:
    board = HexGame(3).initial_state().board
    assert AlphaBetaSearch().evaluate_leaf(board, RED, own=2, rival=5) == 3


def test_bridge_leaf_adds_the_bridge_difference() -> None:
    board = board_from([
        ". R .",
        ". . .",
        "R . .",
    ])
    # Red: plain 1, with bridges 0. Blue: 3 both ways (Red's stones cut its bridges).
    assert bridge_distance(board, RED) == 0
    assert bridge_distance(board, BLUE) == 3
    assert BridgeSearch().evaluate_leaf(board, RED, own=1, rival=3) == (3 - 1) + (3 - 0)


def test_bridge_bot_is_an_alpha_beta_bot_with_another_search() -> None:
    assert issubclass(BridgeBot, AlphaBetaBot)
    assert BridgeBot.search_class is BridgeSearch
    assert AlphaBetaBot.search_class is AlphaBetaSearch


def test_takes_an_immediate_win() -> None:
    obs = observe([
        "R . . .",
        "R B B .",
        "R . . .",
        ". B . .",
    ], RED)
    assert BridgeBot().choose_move(obs) == (3, 0)


def test_blocks_an_immediate_loss() -> None:
    obs = observe([
        ". . R R",
        "B B B .",
        ". R . .",
        ". R . .",
    ], RED)
    assert BridgeBot().choose_move(obs) == (1, 3)


@pytest.mark.parametrize("size", [7, 11])
def test_respects_the_time_limit(size: int) -> None:
    obs = HexGame(size).observation(HexGame(size).initial_state(), RED, time_limit=0.3)
    start = time.perf_counter()
    move = BridgeBot().choose_move(obs)
    assert time.perf_counter() - start < 0.3
    assert move in obs.legal_moves


@pytest.mark.parametrize("bot_color", [RED, BLUE], ids=["as-red", "as-blue"])
def test_beats_random_bot(bot_color: int) -> None:
    game = HexGame(5)
    for seed in range(3):
        bot, rival = BridgeBot(), RandomBot(seed=seed)
        red, blue = (bot, rival) if bot_color == RED else (rival, bot)
        assert play_game(game, red, blue, time_limit=0.1).winner == bot_color
