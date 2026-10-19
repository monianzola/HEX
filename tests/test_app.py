"""Tests for the Streamlit app using Streamlit's AppTest (skipped without streamlit)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from hexarena.game import BLUE, EMPTY, RED  # noqa: E402

APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "app.py")


def start_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def stones(at: AppTest, player: int) -> int:
    return sum(row.count(player) for row in at.session_state["state"].board)


def first_empty_cell(at: AppTest) -> str:
    board = at.session_state["state"].board
    for r, row in enumerate(board):
        for c, value in enumerate(row):
            if value == EMPTY:
                return f"cell-{r}-{c}"
    raise AssertionError("Board is full")


def test_app_starts_with_empty_7x7_board() -> None:
    at = start_app()
    assert at.session_state["size"] == 7
    assert at.session_state["bot_name"] == "shortest-path"
    assert stones(at, RED) == stones(at, BLUE) == 0
    assert len([b for b in at.button if b.key and b.key.startswith("cell-")]) == 49


def test_click_plays_human_move_and_bot_reply() -> None:
    at = start_app()
    at.button(key="cell-0-0").click().run()
    assert not at.exception
    assert at.session_state["state"].board[0][0] == RED
    assert stones(at, RED) == 1 and stones(at, BLUE) == 1
    assert at.button(key="cell-0-0").disabled


def test_full_game_ends_with_winner_message() -> None:
    at = start_app()
    for _ in range(49):
        if at.session_state["state"].winner is not None:
            break
        at.button(key=first_empty_cell(at)).click().run()
        assert not at.exception
    assert at.session_state["state"].winner in (RED, BLUE)
    messages = [m.value for m in at.success] + [m.value for m in at.error]
    assert messages
    assert all(b.disabled for b in at.button if b.key and b.key.startswith("cell-"))


def test_changing_size_starts_new_game() -> None:
    at = start_app()
    at.button(key="cell-1-1").click().run()
    at.select_slider(key="size").set_value(5).run()
    assert not at.exception
    assert at.session_state["state"].size == 5
    assert at.session_state["moves"] == []


def test_new_game_button_resets_board() -> None:
    at = start_app()
    at.button(key="cell-2-2").click().run()
    new_game = next(b for b in at.button if "Nueva partida" in b.label)
    new_game.click().run()
    assert stones(at, RED) == stones(at, BLUE) == 0


def test_can_select_random_bot() -> None:
    at = start_app()
    at.selectbox(key="bot_name").set_value("random").run()
    assert not at.exception
    assert at.session_state["bot"].name == "RandomBot"
