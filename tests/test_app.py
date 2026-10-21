"""Tests for the Streamlit app using Streamlit's AppTest (skipped without streamlit).

AppTest cannot click inside a custom component, so clicks on the board
are simulated by writing the component's value into session state, which
is exactly what the browser does.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("streamlit_image_coordinates")
from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from board_render import geometry  # noqa: E402

from hexarena.game import BLUE, EMPTY, RED  # noqa: E402

APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "app.py")

_click_counter = 0


def start_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def click(at: AppTest, cell: tuple[int, int] | None = None, xy: tuple[float, float] | None = None) -> AppTest:
    """Simulate a click on ``cell`` (or on raw pixel ``xy``) and rerun the app."""
    global _click_counter
    _click_counter += 1
    size = at.session_state["state"].size
    width, height = geometry(size).image_size
    x, y = xy if xy is not None else geometry(size).center(*cell)  # type: ignore[misc]
    key = f"board-{at.session_state['game_id']}"
    at.session_state[key] = {"x": x, "y": y, "width": width, "height": height, "unix_time": _click_counter}
    at.run()
    assert not at.exception
    return at


def stones(at: AppTest, player: int) -> int:
    return sum(row.count(player) for row in at.session_state["state"].board)


def first_empty_cell(at: AppTest) -> tuple[int, int]:
    for r, row in enumerate(at.session_state["state"].board):
        for c, value in enumerate(row):
            if value == EMPTY:
                return (r, c)
    raise AssertionError("Board is full")


def test_app_starts_with_empty_7x7_board() -> None:
    at = start_app()
    assert at.session_state["size"] == 7
    assert at.session_state["bot_name"] == "shortest-path"
    assert stones(at, RED) == stones(at, BLUE) == 0


def test_click_plays_human_move_and_bot_reply() -> None:
    at = click(start_app(), (0, 0))
    assert at.session_state["state"].board[0][0] == RED
    assert stones(at, RED) == 1 and stones(at, BLUE) == 1


def test_same_click_is_not_processed_twice() -> None:
    at = click(start_app(), (0, 0))
    at.run()  # The component still reports the same click.
    at.run()
    assert stones(at, RED) == 1 and stones(at, BLUE) == 1


def test_click_outside_board_is_ignored() -> None:
    at = click(start_app(), xy=(1, 1))
    assert stones(at, RED) == 0
    assert not at.toast


def test_click_on_occupied_cell_shows_notice() -> None:
    at = click(start_app(), (3, 3))
    bot_cell = at.session_state["moves"][-1]
    at = click(at, bot_cell)
    assert stones(at, RED) == 1
    assert at.toast and "ocupada" in at.toast[0].value


def test_full_game_ends_with_winner_message_and_further_clicks_ignored() -> None:
    at = start_app()
    for _ in range(49):
        if at.session_state["state"].winner is not None:
            break
        click(at, first_empty_cell(at))
    assert at.session_state["state"].winner in (RED, BLUE)
    assert [m.value for m in at.success] + [m.value for m in at.error]

    moves_before = len(at.session_state["moves"])
    if any(EMPTY in row for row in at.session_state["state"].board):
        click(at, first_empty_cell(at))
        assert len(at.session_state["moves"]) == moves_before
        assert at.toast and "terminado" in at.toast[0].value


def test_changing_size_starts_new_game() -> None:
    at = click(start_app(), (1, 1))
    at.select_slider(key="size").set_value(5).run()
    assert not at.exception
    assert at.session_state["state"].size == 5
    assert at.session_state["moves"] == []


def test_new_game_button_resets_board() -> None:
    at = click(start_app(), (2, 2))
    old_game = at.session_state["game_id"]
    next(b for b in at.button if "Nueva partida" in b.label).click().run()
    assert stones(at, RED) == stones(at, BLUE) == 0
    assert at.session_state["game_id"] == old_game + 1


def test_can_select_random_bot() -> None:
    at = start_app()
    at.selectbox(key="bot_name").set_value("random").run()
    assert not at.exception
    assert at.session_state["bot"].name == "RandomBot"
