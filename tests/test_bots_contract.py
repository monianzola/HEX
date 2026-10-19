"""Contract tests applied automatically to EVERY registered bot.

A new bot file in ``src/hexarena/bots/`` is picked up here without
writing any new test: each test is parametrised over ``available_bots()``.
If your bot fails one of these tests, it is not ready to be merged.
"""

from __future__ import annotations

import random
import time

import pytest

from hexarena.bots import BLUE, EMPTY, RED, Bot, Observation, available_bots, discovery_errors, get_bot
from hexarena.bots.random_bot import RandomBot
from hexarena.game import HexGame, HexState, find_winner, play_game

BOT_NAMES = available_bots()

POSITION_TIME_LIMIT = 0.5
"""Seconds given to the bot in single-position tests."""

TIME_MARGIN = 1.5
"""A bot may use up to ``TIME_MARGIN * time_limit`` (overhead tolerance)."""

GAME_TIME_LIMIT = 0.1
"""Seconds per move in the full-game tests (kept low so the suite stays fast)."""


# --------------------------------------------------------------------------- positions


def _random_position(size: int, stones: int, seed: int) -> HexState:
    """Play ``stones`` random moves, retrying until the game is still open."""
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


def _single_move_position() -> HexState:
    """A 3x3 board with one empty cell and no winner yet (Red to move).

    R B R
     B . B
      R B R
    """
    board = (
        (RED, BLUE, RED),
        (BLUE, EMPTY, BLUE),
        (RED, BLUE, RED),
    )
    return HexState(board=board, to_move=RED, winner=None)


POSITIONS = {
    "start-7x7": HexGame(7).initial_state(),
    "start-11x11": HexGame(11).initial_state(),
    "midgame-7x7": _random_position(7, 20, seed=1),
    "midgame-11x11": _random_position(11, 50, seed=2),
    "near-end-5x5": _random_position(5, 21, seed=3),
    "single-move-3x3": _single_move_position(),
    "blue-to-move-7x7": _random_position(7, 7, seed=4),
}


def _observation(state: HexState, time_limit: float) -> Observation:
    game = HexGame(state.size)
    return game.observation(state, game.current_player(state), time_limit)


def test_single_move_position_is_valid() -> None:
    state = _single_move_position()
    assert find_winner(state.board) is None
    assert HexGame(3).legal_moves(state) == [(1, 1)]


def test_all_bot_modules_load() -> None:
    assert discovery_errors() == {}, f"Some bot files failed to import: {discovery_errors()}"


def test_at_least_one_bot_is_registered() -> None:
    assert "random" in BOT_NAMES


# --------------------------------------------------------------------------- contract


@pytest.mark.parametrize("name", BOT_NAMES)
def test_bot_can_be_created_without_arguments(name: str) -> None:
    bot = get_bot(name)()
    assert isinstance(bot, Bot)


@pytest.mark.parametrize("name", BOT_NAMES)
def test_bot_has_name_and_description(name: str) -> None:
    cls = get_bot(name)
    assert isinstance(cls.name, str) and cls.name.strip()
    assert isinstance(cls.description, str) and cls.description.strip()


@pytest.mark.parametrize("position", POSITIONS, ids=list(POSITIONS))
@pytest.mark.parametrize("name", BOT_NAMES)
def test_bot_returns_a_legal_move_in_time(name: str, position: str) -> None:
    obs = _observation(POSITIONS[position], POSITION_TIME_LIMIT)
    bot = get_bot(name)()

    start = time.perf_counter()
    move = bot.choose_move(obs)
    elapsed = time.perf_counter() - start

    assert isinstance(move, tuple) and len(move) == 2, f"{name} returned {move!r}, not a (row, col) tuple"
    assert all(isinstance(x, int) and not isinstance(x, bool) for x in move)
    assert move in obs.legal_moves, f"{name} returned illegal move {move} in {position}"
    assert elapsed <= POSITION_TIME_LIMIT * TIME_MARGIN, (
        f"{name} took {elapsed:.2f}s with a time limit of {POSITION_TIME_LIMIT}s"
    )


@pytest.mark.parametrize("name", BOT_NAMES)
def test_bot_does_not_modify_the_observation(name: str) -> None:
    obs = _observation(POSITIONS["midgame-7x7"], POSITION_TIME_LIMIT)
    snapshot = Observation(
        board=tuple(tuple(row) for row in obs.board),
        size=obs.size,
        player=obs.player,
        legal_moves=tuple(obs.legal_moves),
        time_limit=obs.time_limit,
    )
    get_bot(name)().choose_move(obs)
    assert obs == snapshot


@pytest.mark.parametrize("bot_color", [RED, BLUE], ids=["as-red", "as-blue"])
@pytest.mark.parametrize("name", BOT_NAMES)
def test_bot_completes_a_5x5_game_against_random(name: str, bot_color: int) -> None:
    game = HexGame(5)
    bot, opponent = get_bot(name)(), RandomBot(seed=0)
    red, blue = (bot, opponent) if bot_color == RED else (opponent, bot)
    result = play_game(game, red, blue, time_limit=GAME_TIME_LIMIT)
    assert result.winner in (RED, BLUE)
