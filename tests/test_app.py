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


def start_app(**settings: object) -> AppTest:
    """Open the app; ``settings`` are sidebar values applied before the first run."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    for key, value in settings.items():
        at.session_state[key] = value
    at.run()
    assert not at.exception
    return at


def match(at: AppTest):
    return at.session_state["match"]


def click(at: AppTest, cell: tuple[int, int] | None = None, xy: tuple[float, float] | None = None) -> AppTest:
    """Simulate a click on ``cell`` (or on raw pixel ``xy``) and rerun the app."""
    global _click_counter
    _click_counter += 1
    size = match(at).size
    width, height = geometry(size).image_size
    x, y = xy if xy is not None else geometry(size).center(*cell)  # type: ignore[misc]
    key = f"board-{at.session_state['game_id']}"
    at.session_state[key] = {"x": x, "y": y, "width": width, "height": height, "unix_time": _click_counter}
    at.run()
    assert not at.exception
    return at


def stones(at: AppTest, player: int) -> int:
    return sum(row.count(player) for row in match(at).state.board)


def first_empty_cell(at: AppTest) -> tuple[int, int]:
    for r, row in enumerate(match(at).state.board):
        for c, value in enumerate(row):
            if value == EMPTY:
                return (r, c)
    raise AssertionError("Board is full")


def button(at: AppTest, text: str):
    return next(b for b in at.button if text in b.label)


# --------------------------------------------------------------------------- human vs bot


def test_app_starts_with_default_settings() -> None:
    at = start_app()
    assert at.session_state["mode"] == "Humano contra bot"
    assert at.session_state["human_colour"] == RED
    assert at.session_state["size"] == 7
    assert at.session_state["think_time"] == 0.25
    assert stones(at, RED) == stones(at, BLUE) == 0


def test_click_plays_human_move_and_bot_reply() -> None:
    at = click(start_app(think_time=0.1), (0, 0))
    assert match(at).state.board[0][0] == RED
    assert stones(at, RED) == 1 and stones(at, BLUE) == 1


def test_same_click_is_not_processed_twice() -> None:
    at = click(start_app(think_time=0.1), (0, 0))
    at.run()  # The component still reports the same click.
    at.run()
    assert stones(at, RED) == 1 and stones(at, BLUE) == 1


def test_click_outside_board_is_ignored() -> None:
    at = click(start_app(), xy=(1, 1))
    assert stones(at, RED) == 0


def test_click_on_occupied_cell_shows_notice() -> None:
    at = click(start_app(think_time=0.1), (3, 3))
    at = click(at, match(at).moves[-1])  # The cell the bot just took.
    assert stones(at, RED) == 1
    assert at.toast and "ocupada" in at.toast[0].value


def test_human_can_play_second() -> None:
    at = start_app(think_time=0.1)
    at.radio(key="human_colour").set_value(BLUE).run()
    assert not at.exception
    # The bot (Red) has already opened and it is the human's turn.
    assert stones(at, RED) == 1 and stones(at, BLUE) == 0
    assert match(at).is_human_turn()
    at = click(at, first_empty_cell(at))
    assert stones(at, BLUE) == 1 and stones(at, RED) == 2


def test_undo_button() -> None:
    at = click(start_app(think_time=0.1), (2, 2))
    button(at, "Deshacer").click().run()
    assert not at.exception
    assert match(at).moves == []


def test_full_game_ends_with_a_winner_message() -> None:
    at = start_app(rival="random", size=5, think_time=0.1)
    for _ in range(25):
        if match(at).finished:
            break
        click(at, first_empty_cell(at))
    assert match(at).finished
    assert [m.value for m in at.success] + [m.value for m in at.error]


def test_changing_size_starts_a_new_game() -> None:
    at = click(start_app(think_time=0.1), (1, 1))
    old_game = at.session_state["game_id"]
    at.select_slider(key="size").set_value(5).run()
    assert not at.exception
    assert match(at).size == 5 and match(at).moves == []
    assert at.session_state["game_id"] == old_game + 1


def test_new_game_button_resets_the_board() -> None:
    at = click(start_app(think_time=0.1), (2, 2))
    button(at, "Nueva partida").click().run()
    assert stones(at, RED) == stones(at, BLUE) == 0


# --------------------------------------------------------------------------- bot vs bot


def test_bot_vs_bot_step_by_step() -> None:
    at = start_app(think_time=0.1)
    at.radio(key="mode").set_value("Bot contra bot").run()
    assert not at.exception
    assert not match(at).has_human and match(at).moves == []
    button(at, "Siguiente jugada").click().run()
    assert len(match(at).moves) == 1
    button(at, "Siguiente jugada").click().run()
    assert len(match(at).moves) == 2


def test_bot_vs_bot_autoplay_finishes_the_game() -> None:
    at = start_app(mode="Bot contra bot", red_bot="shortest-path", blue_bot="random", size=5, think_time=0.1)
    button(at, "Jugar automáticamente").click().run(timeout=120)
    assert not at.exception
    assert match(at).finished
    assert at.session_state["autoplay"] is False
    assert any("Gana" in m.value for m in at.success)
