"""Streamlit web app: a human (Red) plays a full game of Hex against a bot.

Run locally from the repository root with::

    streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

try:
    import hexarena  # noqa: F401
except ImportError:  # Allow running from a clone without ``pip install``.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hexarena.bots import available_bots, create_bot, get_bot
from hexarena.game import BLUE, EMPTY, RED, HexGame, HexState, IllegalMoveError, Move

HUMAN = RED
BOT = BLUE
DEFAULT_SIZE = 7
DEFAULT_BOT = "shortest-path"
BOT_TIME_LIMIT = 1.0

STONES = {EMPTY: "⚪", RED: "🔴", BLUE: "🔵"}
PLAYER_NAMES = {RED: "Rojo", BLUE: "Azul"}

ss = st.session_state


# --------------------------------------------------------------------------- game actions


def new_game() -> None:
    """Start a new game with the size and bot selected in the sidebar."""
    ss.game = HexGame(ss.size)
    ss.state = ss.game.initial_state()
    ss.moves = []
    ss.bot = create_bot(ss.bot_name)
    ss.message = None


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
        ss.message = f"Jugada ilegal: {exc}"
        return
    ss.moves.append(move)
    ss.message = None
    if not game.is_terminal(ss.state):
        bot_move()


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
            "- Tú eres **🔴 Rojo** y empiezas: une el borde de **arriba** con el de **abajo**.\n"
            "- El bot es **🔵 Azul**: une la **izquierda** con la **derecha**.\n"
            "- Cada casilla tiene 6 vecinas. En Hex nunca hay empate."
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
    """Draw the rhombus: each row is shifted half a cell to the right."""
    game: HexGame = ss.game
    state: HexState = ss.state
    size = state.size
    finished = game.is_terminal(state)
    last_move = ss.moves[-1] if ss.moves else None

    # Each row has: shift spacer, left Blue edge, N cells, right Blue edge, filler.
    total_shift = (size - 1) * 0.5

    def row_columns(shift: float) -> list:
        widths = [shift or 0.001, 0.6] + [1] * size + [0.6, (total_shift - shift) or 0.001]
        return st.columns(widths, gap="small")

    top = row_columns(0)
    for c in range(size):
        top[2 + c].markdown("<div style='text-align:center'>🟥</div>", unsafe_allow_html=True)

    for r, row in enumerate(state.board):
        cols = row_columns(r * 0.5)
        cols[1].markdown("<div style='text-align:center'>🟦</div>", unsafe_allow_html=True)
        for c, value in enumerate(row):
            cols[2 + c].button(
                STONES[value],
                key=f"cell-{r}-{c}",
                on_click=human_move,
                args=((r, c),),
                disabled=finished or value != EMPTY,
                type="primary" if (r, c) == last_move else "secondary",
                help=f"({r}, {c})",
                width="stretch",
            )
        cols[2 + size].markdown("<div style='text-align:center'>🟦</div>", unsafe_allow_html=True)

    bottom = row_columns(total_shift)
    for c in range(size):
        bottom[2 + c].markdown("<div style='text-align:center'>🟥</div>", unsafe_allow_html=True)


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
    st.markdown(
        "<style>div[data-testid='stButton'] button {padding: 0.1rem 0; min-height: 2.2rem;}</style>",
        unsafe_allow_html=True,
    )

    bot_names = available_bots()
    if "size" not in ss:
        ss.size = DEFAULT_SIZE
    if "bot_name" not in ss or ss.bot_name not in bot_names:
        ss.bot_name = DEFAULT_BOT if DEFAULT_BOT in bot_names else bot_names[0]
    if "state" not in ss:
        new_game()

    st.title("⬢ Hex Arena")
    st.caption("Juega una partida de Hex contra uno de los bots del proyecto **hexarena**.")
    render_sidebar(bot_names)
    render_status()
    render_board()
    render_history()


main()
