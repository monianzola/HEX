"""Draw the Hex board as an image and map clicks back to cells.

Geometry (pointy-top hexagons of circumradius ``R``)::

    hex width   w = sqrt(3) * R        (distance between centres in a row)
    row height  h = 1.5 * R            (vertical distance between rows)

    centre of (r, c):
        x = margin + w/2 + c*w + r*w/2     <- each row shifts half a hex right
        y = margin + R   + r*h

With that shift, (r+1, c-1) sits down-left and (r+1, c) down-right of
(r, c), which matches the neighbour rule of :mod:`hexarena.game`.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw

from hexarena.game import BLUE, EMPTY, RED, HexState, Move, neighbors

SQRT3 = math.sqrt(3)
SUPERSAMPLE = 2
"""The board is drawn at this scale and then reduced, for smooth edges."""

TARGET_WIDTH = 720
MAX_RADIUS = 36.0

BACKGROUND = "#f5f3ee"
EMPTY_FILL = "#ffffff"
RED_FILL = "#d62839"
BLUE_FILL = "#1f6fd1"
CELL_OUTLINE = "#3b3b3b"
WIN_OUTLINE = "#f2c14e"
FILLS = {EMPTY: EMPTY_FILL, RED: RED_FILL, BLUE: BLUE_FILL}

# Vertex angles of a pointy-top hexagon (y grows downwards):
# top, upper-right, lower-right, bottom, lower-left, upper-left.
_VERTEX_ANGLES = (-90, -30, 30, 90, 150, 210)
TOP, UPPER_RIGHT, LOWER_RIGHT, BOTTOM, LOWER_LEFT, UPPER_LEFT = range(6)

Point = tuple[float, float]


@dataclass(frozen=True)
class BoardGeometry:
    """Pixel geometry of an N×N board (in final, non-supersampled pixels)."""

    size: int
    radius: float

    @property
    def hex_width(self) -> float:
        return SQRT3 * self.radius

    @property
    def row_height(self) -> float:
        return 1.5 * self.radius

    @property
    def margin(self) -> float:
        # Leaves room for the coloured border around the board.
        return 0.8 * self.radius

    @property
    def image_size(self) -> tuple[int, int]:
        width = 2 * self.margin + self.hex_width * (1.5 * self.size - 0.5)
        height = 2 * self.margin + 2 * self.radius + self.row_height * (self.size - 1)
        return math.ceil(width), math.ceil(height)

    def center(self, r: int, c: int) -> Point:
        """Pixel centre of cell ``(r, c)``."""
        x = self.margin + self.hex_width / 2 + c * self.hex_width + r * self.hex_width / 2
        y = self.margin + self.radius + r * self.row_height
        return x, y

    def corners(self, r: int, c: int, scale: float = 1.0, shrink: float = 1.0) -> list[Point]:
        """The six vertices of cell ``(r, c)``, multiplied by ``scale``.

        ``shrink`` < 1 returns a smaller concentric hexagon.
        """
        cx, cy = self.center(r, c)
        radius = self.radius * shrink
        return [
            (
                (cx + radius * math.cos(math.radians(a))) * scale,
                (cy + radius * math.sin(math.radians(a))) * scale,
            )
            for a in _VERTEX_ANGLES
        ]


@lru_cache(maxsize=None)
def geometry(size: int) -> BoardGeometry:
    """Geometry for an N×N board, scaled so the image is about ``TARGET_WIDTH`` wide."""
    if size < 1:
        raise ValueError(f"Board size must be positive, got {size}")
    radius = min(MAX_RADIUS, TARGET_WIDTH / (SQRT3 * (1.5 * size - 0.5) + 1.6))
    return BoardGeometry(size=size, radius=radius)


def pixel_to_cell(x: float, y: float, size: int) -> tuple[int, int] | None:
    """Return the cell under pixel ``(x, y)``, or ``None`` if it is off the board.

    Picks the cell whose centre is nearest. Because hexagons tile the plane,
    the nearest centre is exactly the hexagon that contains the point. Clicks
    farther than one radius from every centre (margins, outside the
    rhombus) are discarded.
    """
    geo = geometry(size)
    best: tuple[int, int] | None = None
    best_dist = math.inf
    for r in range(size):
        for c in range(size):
            cx, cy = geo.center(r, c)
            dist = math.hypot(x - cx, y - cy)
            if dist < best_dist:
                best, best_dist = (r, c), dist
    return best if best_dist <= geo.radius else None


def winning_chain(state: HexState) -> set[Move]:
    """Stones of the winner that belong to a group touching both of its edges.

    Returns an empty set if there is no winner or the win was not by
    connection (for example, the opponent forfeited).
    """
    player = state.winner
    if player is None:
        return set()
    size = state.size
    board = state.board
    seen: set[Move] = set()
    chain: set[Move] = set()
    for r in range(size):
        for c in range(size):
            if board[r][c] != player or (r, c) in seen:
                continue
            group = {(r, c)}
            queue = deque([(r, c)])
            while queue:
                cell = queue.popleft()
                for nr, nc in neighbors(cell, size):
                    if board[nr][nc] == player and (nr, nc) not in group:
                        group.add((nr, nc))
                        queue.append((nr, nc))
            seen |= group
            axis = 0 if player == RED else 1
            coords = {cell[axis] for cell in group}
            if 0 in coords and size - 1 in coords:
                chain |= group
    return chain


def _border_lines(geo: BoardGeometry, scale: float) -> dict[str, list[list[Point]]]:
    """Polylines that follow the outer outline of the edge hexagons."""
    n = geo.size

    def v(r: int, c: int, k: int) -> Point:
        return geo.corners(r, c, scale)[k]

    top = [v(0, 0, UPPER_LEFT)]
    for c in range(n):
        top += [v(0, c, TOP), v(0, c, UPPER_RIGHT)]
    bottom = [v(n - 1, 0, LOWER_LEFT)]
    for c in range(n):
        bottom += [v(n - 1, c, BOTTOM), v(n - 1, c, LOWER_RIGHT)]
    left: list[Point] = []
    for r in range(n):
        left += [v(r, 0, UPPER_LEFT), v(r, 0, LOWER_LEFT)]
    right: list[Point] = []
    for r in range(n):
        right += [v(r, n - 1, UPPER_RIGHT), v(r, n - 1, LOWER_RIGHT)]
    return {RED_FILL: [top, bottom], BLUE_FILL: [left, right]}


def draw_board(state: HexState, last_move: Move | None = None, size: int | None = None) -> Image.Image:
    """Render ``state`` as an RGB image.

    Args:
        state: Position to draw.
        last_move: Cell to mark with a small circle (the most recent move).
        size: Board side N. Defaults to ``state.size``; if given it must match.

    Returns:
        A PIL image of size ``geometry(size).image_size``.
    """
    size = state.size if size is None else size
    if size != state.size:
        raise ValueError(f"size={size} does not match the {state.size}x{state.size} state")
    geo = geometry(size)
    s = SUPERSAMPLE
    width, height = geo.image_size
    image = Image.new("RGB", (width * s, height * s), BACKGROUND)
    draw = ImageDraw.Draw(image)

    # 1. Thick coloured border. The hexagons are drawn on top, so only the
    #    outer half of the line stays visible.
    border_width = round(geo.radius * 0.45 * s)
    for color, lines in _border_lines(geo, s).items():
        for line in lines:
            draw.line(line, fill=color, width=border_width, joint="curve")

    # 2. Cells.
    outline_width = max(2, round(geo.radius * 0.06 * s))
    for r, row in enumerate(state.board):
        for c, value in enumerate(row):
            draw.polygon(geo.corners(r, c, s), fill=FILLS[value], outline=CELL_OUTLINE, width=outline_width)

    # 3. Winning chain: golden inner outline.
    for r, c in winning_chain(state):
        draw.polygon(geo.corners(r, c, s, shrink=0.8), outline=WIN_OUTLINE, width=outline_width * 2)

    # 4. Last move marker: small white dot.
    if last_move is not None:
        cx, cy = geo.center(*last_move)
        dot = geo.radius * 0.22
        draw.ellipse(
            [(cx - dot) * s, (cy - dot) * s, (cx + dot) * s, (cy + dot) * s],
            fill="#ffffff",
            outline=CELL_OUTLINE,
            width=max(1, outline_width // 2),
        )

    return image.resize((width, height), Image.Resampling.LANCZOS)
