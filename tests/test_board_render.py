"""Tests for app/board_render.py: pixel <-> cell geometry and board drawing."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from board_render import (  # noqa: E402
    BLUE_FILL,
    EMPTY_FILL,
    RED_FILL,
    draw_board,
    geometry,
    pixel_to_cell,
    winning_chain,
)

from hexarena.game import BLUE, RED, HexGame, HexState, neighbors  # noqa: E402

SIZES = [1, 5, 7, 11]


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def close(a: tuple[int, ...], b: tuple[int, ...], tol: int = 12) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# --------------------------------------------------------------------------- geometry


@pytest.mark.parametrize("size", SIZES)
def test_center_of_each_cell_maps_to_that_cell(size: int) -> None:
    geo = geometry(size)
    for r in range(size):
        for c in range(size):
            x, y = geo.center(r, c)
            assert pixel_to_cell(x, y, size) == (r, c)


@pytest.mark.parametrize("size", SIZES)
def test_points_inside_a_hexagon_map_to_it(size: int) -> None:
    geo = geometry(size)
    inradius = geo.hex_width / 2
    for r in range(size):
        for c in range(size):
            cx, cy = geo.center(r, c)
            for angle in range(0, 360, 30):
                x = cx + 0.9 * inradius * math.cos(math.radians(angle))
                y = cy + 0.9 * inradius * math.sin(math.radians(angle))
                assert pixel_to_cell(x, y, size) == (r, c)


@pytest.mark.parametrize("size", SIZES)
def test_points_outside_the_board_return_none(size: int) -> None:
    width, height = geometry(size).image_size
    for x, y in [(-50, -50), (1, 1), (width - 1, 1), (1, height - 1), (width + 100, height / 2), (width / 2, -40)]:
        assert pixel_to_cell(x, y, size) is None


def test_neighbor_centers_match_game_neighbors() -> None:
    """Centres at one hex-width distance are exactly the game's neighbours."""
    size = 7
    geo = geometry(size)
    for r in range(size):
        for c in range(size):
            x, y = geo.center(r, c)
            close_cells = {
                (rr, cc)
                for rr in range(size)
                for cc in range(size)
                if (rr, cc) != (r, c) and math.dist((x, y), geo.center(rr, cc)) < geo.hex_width * 1.01
            }
            assert close_cells == set(neighbors((r, c), size))


def test_board_fits_in_target_width() -> None:
    for size in range(5, 12):
        width, _ = geometry(size).image_size
        assert 300 <= width <= 760


# --------------------------------------------------------------------------- drawing


@pytest.mark.parametrize("size", SIZES)
def test_draw_board_returns_image_of_expected_size(size: int) -> None:
    state = HexGame(size).initial_state()
    image = draw_board(state, None, size)
    assert image.size == geometry(size).image_size
    assert image.mode == "RGB"


def test_draw_board_colours_cells() -> None:
    game = HexGame(5)
    state = game.play(game.play(game.initial_state(), (2, 2)), (0, 0))
    image = draw_board(state, None, 5)
    geo = geometry(5)

    def pixel(r: int, c: int) -> tuple[int, int, int]:
        x, y = geo.center(r, c)
        return image.getpixel((round(x), round(y)))  # type: ignore[return-value]

    assert close(pixel(2, 2), hex_to_rgb(RED_FILL))
    assert close(pixel(0, 0), hex_to_rgb(BLUE_FILL))
    assert close(pixel(4, 4), hex_to_rgb(EMPTY_FILL))


def test_last_move_is_marked_with_white_dot() -> None:
    game = HexGame(5)
    state = game.play(game.initial_state(), (2, 2))
    geo = geometry(5)
    x, y = geo.center(2, 2)
    with_marker = draw_board(state, (2, 2), 5).getpixel((round(x), round(y)))
    without = draw_board(state, None, 5).getpixel((round(x), round(y)))
    assert close(with_marker, (255, 255, 255))
    assert close(without, hex_to_rgb(RED_FILL))


def test_draw_board_rejects_mismatched_size() -> None:
    with pytest.raises(ValueError):
        draw_board(HexGame(5).initial_state(), None, 7)


# --------------------------------------------------------------------------- winning chain


def test_winning_chain_for_red_column() -> None:
    game = HexGame(3)
    state = game.initial_state()
    for move in [(0, 1), (0, 0), (1, 1), (2, 2), (2, 1)]:
        state = game.play(state, move)
    assert state.winner == RED
    assert winning_chain(state) == {(0, 1), (1, 1), (2, 1)}


def test_winning_chain_for_blue_row() -> None:
    game = HexGame(3)
    state = game.initial_state()
    for move in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 2), (1, 2)]:
        state = game.play(state, move)
    assert state.winner == BLUE
    assert winning_chain(state) == {(1, 0), (1, 1), (1, 2)}


def test_no_chain_without_winner_or_on_forfeit() -> None:
    state = HexGame(3).initial_state()
    assert winning_chain(state) == set()
    forfeit = HexState(board=state.board, to_move=BLUE, winner=RED)
    assert winning_chain(forfeit) == set()
