"""Tests for app/game_controller.py: the web app's game logic, without Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from game_controller import HUMAN, Match  # noqa: E402

from hexarena.bots import Bot, Move, Observation, register_bot, unregister_bot  # noqa: E402
from hexarena.game import BLUE, RED  # noqa: E402


@pytest.fixture
def crashing_bot():
    @register_bot("test-crasher")
    class Crasher(Bot):
        name = "Crasher"
        description = "Always raises."

        def choose_move(self, observation: Observation) -> Move:
            raise RuntimeError("boom")

    yield "test-crasher"
    unregister_bot("test-crasher")


def test_human_plays_red_and_moves_first() -> None:
    match = Match(size=5, players={RED: HUMAN, BLUE: "random"})
    assert match.is_human_turn()
    assert match.play_human((2, 2)) is None
    assert match.is_bot_turn()
    assert match.play_bot() is not None
    assert match.is_human_turn()
    assert len(match.moves) == 2


def test_human_can_play_second() -> None:
    match = Match(size=5, players={RED: "shortest-path", BLUE: HUMAN})
    assert match.is_bot_turn() and not match.is_human_turn()
    assert match.play_human((0, 0)) == "Espera: le toca al bot."
    match.play_bot()
    assert match.moves == [(2, 2)]  # ShortestPathBot opens in the centre.
    assert match.is_human_turn()


def test_occupied_cell_and_finished_game_are_refused() -> None:
    match = Match(size=1, players={RED: HUMAN, BLUE: "random"})
    assert match.play_human((0, 0)) is None
    assert match.finished and match.winner == RED
    assert "terminado" in (match.play_human((0, 0)) or "")
    other = Match(size=3, players={RED: HUMAN, BLUE: "random"})
    other.play_human((1, 1))
    other.play_bot()
    assert "ocupada" in (other.play_human((1, 1)) or "")


def test_bot_against_bot_plays_a_full_game() -> None:
    match = Match(size=5, players={RED: "shortest-path", BLUE: "random"}, time_limit=0.1)
    assert not match.has_human
    while not match.finished:
        assert match.play_bot() is not None
    assert match.winner in (RED, BLUE)
    assert match.player_name(RED) == "ShortestPathBot"


def test_undo_takes_back_the_human_move_and_the_bot_reply() -> None:
    match = Match(size=5, players={RED: HUMAN, BLUE: "random"})
    assert not match.can_undo()
    match.play_human((2, 2))
    match.play_bot()
    match.play_human((1, 1))
    match.play_bot()
    match.undo()
    assert match.moves[0] == (2, 2) and len(match.moves) == 2
    assert match.is_human_turn()
    match.undo()
    assert match.moves == [] and not match.can_undo()


def test_undo_when_human_plays_blue_keeps_the_bot_opening() -> None:
    match = Match(size=5, players={RED: "shortest-path", BLUE: HUMAN})
    match.play_bot()
    match.play_human((0, 0))
    match.play_bot()
    match.undo()
    assert match.moves == [(2, 2)]
    assert match.is_human_turn()


def test_crashing_bot_loses_without_crashing_the_app(crashing_bot: str) -> None:
    match = Match(size=5, players={RED: HUMAN, BLUE: crashing_bot})
    match.play_human((2, 2))
    assert match.play_bot() is None
    assert match.finished and match.winner == RED
    assert match.forfeit and "boom" in match.forfeit
    match.undo()  # Undo also clears the forfeit.
    assert not match.finished and match.forfeit is None


def test_bot_receives_the_selected_time_limit() -> None:
    seen: list[float] = []

    @register_bot("test-spy")
    class Spy(Bot):
        name = "Spy"
        description = "Records the time limit."

        def choose_move(self, observation: Observation) -> Move:
            seen.append(observation.time_limit)
            return observation.legal_moves[0]

    try:
        match = Match(size=3, players={RED: "test-spy", BLUE: HUMAN}, time_limit=0.5)
        match.play_bot()
        assert seen == [0.5]
        assert match.last_think_time >= 0
    finally:
        unregister_bot("test-spy")
