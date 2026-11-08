"""Streamlit web app: play Hex against a bot, or watch two bots play.

Run locally from the repository root with::

    streamlit run app/app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit_image_coordinates import streamlit_image_coordinates

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))  # So ``board_render`` imports on Streamlit Cloud.
try:
    import hexarena  # noqa: F401
except ImportError:  # Allow running from a clone without ``pip install``.
    sys.path.insert(0, str(APP_DIR.parent / "src"))

from board_render import draw_board, geometry, pixel_to_cell  # noqa: E402
from game_controller import COLOUR_NAMES, HUMAN, Match  # noqa: E402

from hexarena.bots import available_bots, get_bot  # noqa: E402
from hexarena.game import BLUE, RED  # noqa: E402

DEFAULT_SIZE = 7
DEFAULT_BOT = "alpha-beta"
THINK_TIMES = [0.1, 0.25, 0.5, 1.0]
DEFAULT_THINK_TIME = 0.25
AUTOPLAY_DELAY = 0.4
"""Pause between moves when watching two bots, so the game can be followed."""

MODE_HUMAN = "Humano contra bot"
MODE_BOTS = "Bot contra bot"
STONES = {RED: "🔴", BLUE: "🔵"}

ss = st.session_state


# --------------------------------------------------------------------------- state


def new_game() -> None:
    """Start a new game with the options selected in the sidebar."""
    if ss.mode == MODE_HUMAN:
        bot_colour = BLUE if ss.human_colour == RED else RED
        players = {ss.human_colour: HUMAN, bot_colour: ss.rival}
    else:
        players = {RED: ss.red_bot, BLUE: ss.blue_bot}
    ss.match = Match(size=ss.size, players=players, time_limit=ss.think_time)
    ss.game_id = ss.get("game_id", -1) + 1
    ss.last_click = None
    ss.autoplay = False


def board_key() -> str:
    """Key of the board component. It changes every game, so a new game
    starts with a fresh component instead of replaying the previous click."""
    return f"board-{ss.game_id}"


def handle_click(click: dict[str, Any] | None) -> None:
    """Turn a click on the board image into a move, at most once per click.

    ``streamlit_image_coordinates`` keeps returning the last click on every
    rerun, so the processed click is remembered in ``ss.last_click``.
    """
    if not click or click == ss.last_click:
        return
    ss.last_click = click
    match: Match = ss.match
    if not match.has_human:
        return
    width, height = geometry(match.size).image_size
    # The browser may shrink the image: convert to image pixels.
    x = click["x"] * width / click.get("width", width)
    y = click["y"] * height / click.get("height", height)
    cell = pixel_to_cell(x, y, match.size)
    if cell is None:
        return  # Click on the margin or outside the rhombus.
    if message := match.play_human(cell):
        st.toast(message, icon="⚠️")


def rerun_board() -> None:
    """Redraw only the board fragment if possible, otherwise the whole page."""
    try:
        st.rerun(scope="fragment")
    except StreamlitAPIException:  # Not inside a fragment rerun (e.g. first page load).
        st.rerun()


# --------------------------------------------------------------------------- sidebar


def bot_label(name: str) -> str:
    return get_bot(name).name


def render_sidebar(bot_names: list[str]) -> None:
    with st.sidebar:
        st.header("Configuración")
        st.radio("Modo de juego", [MODE_HUMAN, MODE_BOTS], key="mode", on_change=new_game)
        if ss.mode == MODE_HUMAN:
            st.radio(
                "Juegas con",
                [RED, BLUE],
                format_func=lambda c: "🔴 Rojo · empiezas tú" if c == RED else "🔵 Azul · empieza el bot",
                key="human_colour",
                on_change=new_game,
            )
            st.selectbox("Bot rival", bot_names, format_func=bot_label, key="rival", on_change=new_game)
        else:
            st.selectbox("🔴 Bot Rojo", bot_names, format_func=bot_label, key="red_bot", on_change=new_game)
            st.selectbox("🔵 Bot Azul", bot_names, format_func=bot_label, key="blue_bot", on_change=new_game)
        st.select_slider("Tamaño del tablero", options=list(range(5, 12)), key="size", on_change=new_game)
        st.select_slider(
            "Tiempo de pensar de los bots",
            options=THINK_TIMES,
            format_func=lambda t: f"{t:g} s",
            key="think_time",
            on_change=new_game,
            help="Más tiempo = bots más fuertes pero más lentos. El torneo usa 1 s.",
        )
        st.button("🔄 Nueva partida", on_click=new_game, width="stretch", type="primary")

        st.divider()
        with st.expander("Bots disponibles"):
            for name in bot_names:
                cls = get_bot(name)
                st.markdown(f"**{cls.name}**: {cls.description}")
        st.markdown(
            "**Reglas**\n\n"
            "- 🔴 **Rojo** empieza y une el borde **de arriba** con el **de abajo**.\n"
            "- 🔵 **Azul** une el borde **izquierdo** con el **derecho**.\n"
            "- Por turnos, cada uno pone una ficha en un hexágono vacío. En Hex nunca hay empate."
        )


# --------------------------------------------------------------------------- game area


def render_status(match: Match) -> None:
    if match.finished:
        winner = match.winner
        assert winner is not None
        name = match.player_name(winner)
        if match.has_human and match.is_human(winner):
            st.success(f"🎉 ¡Has ganado con {STONES[winner]} {COLOUR_NAMES[winner]}! ({len(match.moves)} jugadas)")
        elif match.has_human:
            st.error(f"🤖 Ha ganado {name} con {STONES[winner]} {COLOUR_NAMES[winner]}. ¡Prueba otra vez!")
        else:
            st.success(f"🏆 Gana {name} con {STONES[winner]} {COLOUR_NAMES[winner]} ({len(match.moves)} jugadas).")
        if match.forfeit:
            st.warning(match.forfeit)
        return
    colour = match.to_move
    who = "tu turno: haz clic en un hexágono vacío" if match.is_human(colour) else f"turno de {match.player_name(colour)}"
    st.info(f"Jugada {len(match.moves) + 1} · {STONES[colour]} {COLOUR_NAMES[colour]}: {who}")


def render_controls(match: Match) -> None:
    if match.has_human:
        st.button(
            "↩️ Deshacer mi última jugada",
            on_click=lambda: match.undo(),
            disabled=not match.can_undo(),
        )
        return
    left, right = st.columns(2)
    left.button(
        "⏭️ Siguiente jugada",
        on_click=lambda: match.play_bot(),
        disabled=match.finished or ss.autoplay,
        width="stretch",
    )
    if ss.autoplay:
        right.button("⏸️ Pausar", on_click=lambda: ss.update(autoplay=False), width="stretch")
    else:
        right.button(
            "▶️ Jugar automáticamente",
            on_click=lambda: ss.update(autoplay=True),
            disabled=match.finished,
            width="stretch",
        )


def render_history(match: Match) -> None:
    with st.expander(f"Historial ({len(match.moves)} jugadas)"):
        if not match.moves:
            st.write("Aún no hay jugadas.")
        lines = [
            f"{i + 1}. {STONES[RED if i % 2 == 0 else BLUE]} ({r}, {c})" for i, (r, c) in enumerate(match.moves)
        ]
        st.markdown("  \n".join(lines))


@st.fragment
def game_area() -> None:
    """Status, board, controls and history.

    It is a *fragment*: clicking the board or the buttons reruns only this
    part of the page, not the sidebar.
    """
    match: Match = ss.match
    handle_click(ss.get(board_key()))

    render_status(match)
    image = draw_board(match.state, match.last_move, match.size)
    # Compressed PNG: ~40 KB per move instead of ~1 MB.
    streamlit_image_coordinates(
        image,
        key=board_key(),
        width="content",
        cursor="pointer" if match.is_human_turn() else "default",
        png_compression_level=6,
    )
    render_controls(match)
    render_history(match)

    # The bot moves AFTER the board is drawn, so the human's stone appears
    # immediately and a spinner shows while the bot thinks.
    if match.is_bot_turn() and (match.has_human or ss.autoplay):
        with st.spinner(f"🤖 {match.player_name(match.to_move)} está pensando…"):
            match.play_bot()
            if not match.has_human:
                time.sleep(AUTOPLAY_DELAY)
        if match.finished:
            ss.autoplay = False
        rerun_board()


# --------------------------------------------------------------------------- page


def init_state(bot_names: list[str]) -> None:
    default_bot = DEFAULT_BOT if DEFAULT_BOT in bot_names else bot_names[-1]
    defaults = {
        "mode": MODE_HUMAN,
        "human_colour": RED,
        "rival": default_bot,
        "red_bot": default_bot,
        "blue_bot": "shortest-path" if "shortest-path" in bot_names else bot_names[0],
        "size": DEFAULT_SIZE,
        "think_time": DEFAULT_THINK_TIME,
        "autoplay": False,
    }
    for key, value in defaults.items():
        if key not in ss:
            ss[key] = value
    for key in ("rival", "red_bot", "blue_bot"):
        if ss[key] not in bot_names:  # A bot was removed from the registry.
            ss[key] = default_bot
    if "match" not in ss:
        new_game()


def main() -> None:
    st.set_page_config(page_title="Hex Arena", page_icon="⬢", layout="wide")
    bot_names = available_bots()
    init_state(bot_names)
    st.title("⬢ Hex Arena")
    st.caption(
        "Juega a Hex contra los bots del proyecto **hexarena**, o mira cómo juegan entre ellos. "
        "[Cómo crear tu propio bot](https://hex-arena-cunef.readthedocs.io/es/latest/tutorial-bot/)"
    )
    render_sidebar(bot_names)
    game_area()


main()
