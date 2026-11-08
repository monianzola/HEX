"""Check a bot before submitting it: ``python -m hexarena.check <bot>``.

It runs the same checks as ``tests/test_bots_contract.py`` but without
pytest, and prints a short report in Spanish:

* the bot file loads and the bot is registered;
* it can be created without arguments and has ``name`` and ``description``;
* it returns legal moves within the time limit in several positions;
* it finishes games against RandomBot and ShortestPathBot with both colours.

The exit code is 0 when every mandatory check passes.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import traceback
from collections.abc import Sequence
from typing import Any

from hexarena.bots import available_bots, discovery_errors, get_bot
from hexarena.game import BLUE, EMPTY, RED, HexGame, HexState, IllegalMoveError, Move, Observation

OK, FAIL, INFO = "✅", "❌", "ℹ️"
COLOUR_NAMES = {RED: "Rojo", BLUE: "Azul"}


class _Timed:
    """Wraps a bot and remembers the slowest answer."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        self.slowest = 0.0

    def choose_move(self, observation: Observation) -> Move:
        start = time.perf_counter()
        move = self.bot.choose_move(observation)
        self.slowest = max(self.slowest, time.perf_counter() - start)
        return move


def _load(spec: str) -> type:
    if ":" in spec:
        import importlib

        module, _, attr = spec.partition(":")
        return getattr(importlib.import_module(module), attr)
    return get_bot(spec)


def _positions() -> dict[str, HexState]:
    """A few positions every bot must handle."""
    rng = random.Random(0)
    game = HexGame(7)
    mid = game.initial_state()
    while sum(row.count(EMPTY) for row in mid.board) > 49 - 16:
        candidate = game.play(mid, rng.choice(game.legal_moves(mid)))
        if game.is_terminal(candidate):
            continue
        mid = candidate
    single = HexState(
        board=((RED, BLUE, RED), (BLUE, EMPTY, BLUE), (RED, BLUE, RED)), to_move=RED
    )
    return {
        "tablero vacío 7x7": game.initial_state(),
        "mitad de partida 7x7": mid,
        "tablero vacío 11x11": HexGame(11).initial_state(),
        "una sola casilla libre": single,
    }


def _play(game: HexGame, red: Any, blue: Any, time_limit: float) -> tuple[int, HexState, int]:
    state = game.initial_state()
    moves = 0
    players = {RED: red, BLUE: blue}
    while not game.is_terminal(state):
        colour = game.current_player(state)
        move = players[colour].choose_move(game.observation(state, colour, time_limit))
        state = game.play(state, move)
        moves += 1
    assert state.winner is not None
    return state.winner, state, moves


def check_bot(spec: str, time_limit: float = 1.0, games: int = 2, show_board: bool = True) -> bool:
    """Run every check on ``spec`` and print the report. Returns ``True`` if all passed."""
    print(f"\nComprobando el bot '{spec}'\n")
    passed = True

    def report(ok: bool, text: str) -> None:
        nonlocal passed
        passed = passed and ok
        print(f"  {OK if ok else FAIL} {text}")

    # 1. Load.
    try:
        cls = _load(spec)
    except Exception as exc:  # noqa: BLE001 - show the student what went wrong
        report(False, f"No se encuentra el bot: {exc}")
        errors = discovery_errors()
        if errors:
            print("\n  Archivos de bots que no se han podido cargar:")
            for module, error in errors.items():
                print(f"    - {module}: {error}")
        print(f"\n  {INFO} Bots disponibles: {', '.join(available_bots())}")
        print(f"  {INFO} El nombre es el que pones en @register_bot(\"...\"), no el del archivo.")
        return _verdict(False)
    report(True, f"Se carga correctamente ({cls.__module__}.{cls.__qualname__})")

    # 2. Construction and metadata.
    try:
        bot = cls()
    except Exception as exc:  # noqa: BLE001
        report(False, f"No se puede crear sin argumentos: {type(exc).__name__}: {exc}")
        return _verdict(False)
    report(True, "Se crea sin argumentos")
    report(bool(str(getattr(cls, "name", "")).strip()), f"Tiene nombre: {getattr(cls, 'name', '')!r}")
    report(bool(str(getattr(cls, "description", "")).strip()),
           f"Tiene descripción: {getattr(cls, 'description', '')!r}")

    # 3. Single positions: legal move, on time, observation untouched.
    for label, state in _positions().items():
        game = HexGame(state.size)
        obs = game.observation(state, game.current_player(state), time_limit)
        snapshot = (obs.board, obs.legal_moves)
        start = time.perf_counter()
        try:
            move = cls().choose_move(obs)
        except Exception as exc:  # noqa: BLE001
            report(False, f"{label}: lanza {type(exc).__name__}: {exc}")
            traceback.print_exc(limit=-2)
            continue
        elapsed = time.perf_counter() - start
        if not (isinstance(move, tuple) and len(move) == 2 and all(type(x) is int for x in move)):
            report(False, f"{label}: devuelve {move!r}, que no es una tupla (fila, columna)")
        elif move not in obs.legal_moves:
            report(False, f"{label}: la jugada {move} no es legal (casilla ocupada o fuera del tablero)")
        elif elapsed > time_limit:
            report(False, f"{label}: tarda {elapsed:.2f} s (máximo {time_limit:g} s)")
        else:
            report(True, f"{label}: juega {move} en {elapsed:.2f} s")
        if (obs.board, obs.legal_moves) != snapshot:
            report(False, f"{label}: ha modificado la observación")

    # 4. Full games against the built-in bots, both colours.
    print()
    last_state: HexState | None = None
    for rival_name in ("random", "shortest-path"):
        rival_cls = get_bot(rival_name)
        wins = 0
        for i in range(games):
            for colour in (RED, BLUE):
                timed = _Timed(cls())
                rival = rival_cls()
                red, blue = (timed, rival) if colour == RED else (rival, timed)
                try:
                    winner, last_state, moves = _play(HexGame(7), red, blue, time_limit)
                except IllegalMoveError as exc:
                    report(False, f"Contra {rival_cls.name} con {COLOUR_NAMES[colour]}: jugada ilegal ({exc})")
                    continue
                except Exception as exc:  # noqa: BLE001
                    report(False, f"Contra {rival_cls.name} con {COLOUR_NAMES[colour]}: "
                                  f"{type(exc).__name__}: {exc}")
                    continue
                if timed.slowest > time_limit:
                    report(False, f"Contra {rival_cls.name}: una jugada tardó {timed.slowest:.2f} s")
                wins += winner == colour
        total = 2 * games
        print(f"  {INFO} Contra {rival_cls.name}: {wins} de {total} partidas ganadas (7x7, {time_limit:g} s)")

    if show_board and last_state is not None:
        print("\n  Final de la última partida:\n")
        print("\n".join("    " + line for line in HexGame(7).render_ascii(last_state).splitlines()))

    return _verdict(passed)


def _verdict(passed: bool) -> bool:
    """Print the final line of the report."""
    print()
    if passed:
        print(f"{OK} Todo correcto: tu bot cumple las reglas. ¡Ya puedes abrir el pull request!\n")
    else:
        print(f"{FAIL} Hay errores: corrígelos antes de abrir el pull request.\n")
    return passed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m hexarena.check",
        description="Comprueba que un bot cumple las reglas de hex-arena antes de enviarlo.",
    )
    parser.add_argument("bot", help='nombre del bot (el de @register_bot("...")) o modulo:Clase')
    parser.add_argument("--time-limit", type=float, default=1.0, help="segundos por jugada (1 por defecto)")
    parser.add_argument("--games", type=int, default=2, help="partidas por color contra cada rival")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass
    return 0 if check_bot(args.bot, args.time_limit, args.games) else 1


if __name__ == "__main__":
    sys.exit(main())
