"""Streamlit web app: a human (Red) plays a full game of Hex against a bot.

Run locally from the repository root with::

    streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))  # So ``board_render`` imports on Streamlit Cloud.
try:
    import hexarena  # noqa: F401
except ImportError:  # Allow running from a clone without ``pip install``.
    sys.path.insert(0, str(APP_DIR.parent / "src"))

from board_render import draw_board, geometry, pixel_to_cell  # noqa: E402

from hexarena.bots import available_bots, create_bot, get_bot  # noqa: E402
from hexarena.game import BLUE, EMPTY, RED, HexGame, HexState, IllegalMoveError, Move  # noqa: E402

HUMAN = RED
BOT = BLUE
DEFAULT_SIZE = 7
DEFAULT_BOT = "shortest-path"
BOT_TIME_LIMIT = 1.0

STONES = {EMPTY: "⚪", RED: "🔴", BLUE: "🔵"}
PLAYER_NAMES = {RED: "Rojo", BLUE: "Azul"}

ss = st.session_state


# --------------------------------------------------------------------------- game actions


def board_key() -> str:
    """Key of the board component. It changes every game, so a new game
    starts with a fresh component instead of replaying the previous click."""
    return f"board-{ss.game_id}"


def new_game() -> None:
    """Start a new game with the size and bot selected in the sidebar."""
    ss.game_id = ss.get("game_id", -1) + 1
    ss.game = HexGame(ss.size)
    ss.state = ss.game.initial_state()
    ss.moves = []
    ss.bot = create_bot(ss.bot_name)
    ss.message = None
    ss.last_click = None


def bot_move() -> None:
    """Let the bot play. If it fails or plays illegally, it loses the game."""
    game: HexGame = ss.game
    state: HexState = ss.state
    observation = game.observation(state, BOT, BOT_TIME_LIMIT)
    try:
        move = ss.bot.choose_move(observation)
        ss.state = game.play(state, move)
    except Exception as exc:  # noqa: BLE001 - a broken bot must not crash the app
        ss.state = HexState(board=state.board, to_move=state.to_move, winner=HUMAN)
        ss.message = f"El bot ha fallado ({type(exc).__name__}: {exc}) y pierde la partida."
        return
    ss.moves.append(move)


def human_move(move: Move) -> None:
    """Play the human's move and, if the game continues, the bot's reply."""
    game: HexGame = ss.game
    state: HexState = ss.state
    if game.is_terminal(state) or game.current_player(state) != HUMAN:
        return
    try:
        ss.state = game.play(state, move)
    except IllegalMoveError as exc:
        ss.notice = f"Jugada ilegal: {exc}"
        return
    ss.moves.append(move)
    ss.message = None
    if not game.is_terminal(ss.state):
        bot_move()


def handle_click(click: dict[str, Any] | None) -> None:
    """Turn a click from the board image into a move, at most once per click.

    ``streamlit_image_coordinates`` keeps returning the last click on every
    rerun, so the processed click is remembered in ``ss.last_click``.
    """
    if not click or click == ss.last_click:
        return
    ss.last_click = click

    size = ss.state.size
    width, height = geometry(size).image_size
    # The browser may shrink the image; convert to image pixels.
    x = click["x"] * width / click.get("width", width)
    y = click["y"] * height / click.get("height", height)
    cell = pixel_to_cell(x, y, size)
    if cell is None:
        return  # Click on the margin or outside the rhombus.

    game: HexGame = ss.game
    state: HexState = ss.state
    if game.is_terminal(state):
        ss.notice = "La partida ha terminado. Pulsa «Nueva partida» para jugar otra."
    elif game.current_player(state) != HUMAN:
        return
    elif state.board[cell[0]][cell[1]] != EMPTY:
        ss.notice = f"La casilla {cell} ya está ocupada."
    else:
        human_move(cell)


# --------------------------------------------------------------------------- rendering


def bot_label(name: str) -> str:
    cls = get_bot(name)
    return f"{cls.name} – {cls.description}" if cls.description else cls.name


def render_sidebar(bot_names: list[str]) -> None:
    with st.sidebar:
        st.header("Configuración")
        st.select_slider(
            "Tamaño del tablero",
            options=list(range(5, 12)),
            key="size",
            on_change=new_game,
        )
        st.selectbox(
            "Bot oponente",
            options=bot_names,
            format_func=bot_label,
            key="bot_name",
            on_change=new_game,
        )
        st.button("🔄 Nueva partida", on_click=new_game, width="stretch")
        st.divider()
        st.markdown(
            "**Reglas**\n\n"
            "- Tú eres **🔴 Rojo** y empiezas: une el borde **rojo de arriba** con el **de abajo**.\n"
            "- El bot es **🔵 Azul**: une el borde **azul de la izquierda** con el **de la derecha**.\n"
            "- Haz clic en un hexágono vacío para jugar. En Hex nunca hay empate."
        )


def render_status() -> None:
    game: HexGame = ss.game
    state: HexState = ss.state
    winner = game.winner(state)
    if winner == HUMAN:
        st.success("🎉 ¡Has ganado!")
    elif winner == BOT:
        st.error(f"🤖 Ha ganado {ss.bot.name}.")
    else:
        st.info(f"Turno de {STONES[state.to_move]} {PLAYER_NAMES[state.to_move]} · jugada {len(ss.moves) + 1}")
    if ss.message:
        st.warning(ss.message)


def render_board() -> None:
    last_move = ss.moves[-1] if ss.moves else None
    image = draw_board(ss.state, last_move, ss.state.size)
    streamlit_image_coordinates(image, key=board_key(), width="content", cursor="pointer")


def render_history() -> None:
    with st.expander(f"Historial ({len(ss.moves)} jugadas)"):
        if not ss.moves:
            st.write("Aún no hay jugadas.")
        for i, (r, c) in enumerate(ss.moves):
            player = RED if i % 2 == 0 else BLUE
            st.write(f"{i + 1}. {STONES[player]} ({r}, {c})")


# --------------------------------------------------------------------------- page


def main() -> None:
    st.set_page_config(page_title="Hex Arena", page_icon="⬢", layout="wide")

    bot_names = available_bots()
    if "size" not in ss:
        ss.size = DEFAULT_SIZE
    if "bot_name" not in ss or ss.bot_name not in bot_names:
        ss.bot_name = DEFAULT_BOT if DEFAULT_BOT in bot_names else bot_names[0]
    if "state" not in ss:
        new_game()

    # Process the click *before* drawing, so the image already shows the
    # human move and the bot's reply in this same run.
    handle_click(ss.get(board_key()))

    st.title("⬢ Hex Arena")
    st.caption("Juega una partida de Hex contra uno de los bots del proyecto **hexarena**.")
    render_sidebar(bot_names)
    if notice := ss.pop("notice", None):
        st.toast(notice, icon="⚠️")
    render_status()
    render_board()
    render_history()


main()
