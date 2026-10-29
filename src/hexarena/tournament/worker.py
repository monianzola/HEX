"""Run each bot in its own process, so a broken bot cannot break the tournament.

The tournament never executes bot code itself. Every bot lives in a child
process and receives requests through a :class:`multiprocessing.Pipe`:

* ``("new", seed)``: create a fresh bot instance for a new game.
* ``("move", observation)``: return a move.
* ``("stop",)``: exit.

The parent waits for each answer with a timeout. If the bot does not
answer in time (for example, an infinite loop), the process is killed and
started again for the next game.
"""

from __future__ import annotations

import importlib
import inspect
import os
import random
import traceback
from collections.abc import Callable
from multiprocessing.connection import Connection
from multiprocessing.context import BaseContext
from typing import Any

# Possible statuses of a request.
OK = "ok"
ERROR = "error"  # The bot raised an exception (or could not be loaded).
TIMEOUT = "timeout"  # No answer in time: the process was killed.
CRASH = "crash"  # The process died or the pipe broke.

Reply = tuple[str, Any]


def load_bot_factory(spec: str) -> Callable[..., Any]:
    """Return the bot class described by ``spec``.

    ``spec`` is either the name of a registered bot (``"random"``) or an
    import path ``"package.module:ClassName"``.
    """
    if ":" in spec:
        module_name, _, attr = spec.partition(":")
        return getattr(importlib.import_module(module_name), attr)
    from hexarena.bots import get_bot

    return get_bot(spec)


def instantiate(factory: Callable[..., Any], seed: int) -> Any:
    """Create a bot, passing ``seed`` if its constructor accepts one."""
    try:
        params = inspect.signature(factory).parameters
    except (TypeError, ValueError):
        params = {}
    return factory(seed=seed) if "seed" in params else factory()


def _short_error(exc: BaseException) -> str:
    last = traceback.extract_tb(exc.__traceback__)[-1:] if exc.__traceback__ else []
    where = f" ({os.path.basename(last[0].filename)}:{last[0].lineno})" if last else ""
    return f"{type(exc).__name__}: {exc}{where}"


def worker_main(conn: Connection, spec: str) -> None:
    """Entry point of a bot process: answer requests until told to stop."""
    try:
        factory: Callable[..., Any] | None = load_bot_factory(spec)
        load_error = ""
    except Exception as exc:  # noqa: BLE001 - report it, do not crash
        factory, load_error = None, f"cannot load bot: {_short_error(exc)}"

    bot: Any = None
    while True:
        try:
            message = conn.recv()
        except (EOFError, OSError):
            return
        kind = message[0]
        if kind == "stop":
            return
        try:
            if kind == "new":
                if factory is None:
                    reply: Reply = (ERROR, load_error)
                else:
                    random.seed(message[1])  # Reproducible even for bots using `random`.
                    bot = instantiate(factory, message[1])
                    reply = (OK, None)
            elif kind == "move":
                reply = (OK, bot.choose_move(message[1]))
            else:
                reply = (ERROR, f"unknown request {kind!r}")
        except Exception as exc:  # noqa: BLE001 - the bot's fault, report it
            reply = (ERROR, _short_error(exc))
        try:
            conn.send(reply)
        except Exception as exc:  # noqa: BLE001 - e.g. the move cannot be pickled
            conn.send((ERROR, f"cannot send the answer: {_short_error(exc)}"))


class BotProcess:
    """Parent-side handle of a bot process, restarted on demand."""

    def __init__(self, spec: str, context: BaseContext) -> None:
        self.spec = spec
        self._context = context
        self._process: Any = None
        self._conn: Connection | None = None

    def _start(self) -> None:
        parent_conn, child_conn = self._context.Pipe()
        process = self._context.Process(
            target=worker_main, args=(child_conn, self.spec), daemon=True
        )
        process.start()
        child_conn.close()
        self._process, self._conn = process, parent_conn

    def request(self, message: tuple[Any, ...], timeout: float) -> Reply:
        """Send ``message`` and wait at most ``timeout`` seconds for the reply."""
        if self._process is None or not self._process.is_alive():
            self.kill()
            self._start()
        assert self._conn is not None
        try:
            self._conn.send(message)
            if not self._conn.poll(timeout):
                self.kill()
                return TIMEOUT, f"no answer within {timeout:.2f}s"
            return self._conn.recv()
        except (EOFError, OSError) as exc:
            exit_code = self._process.exitcode if self._process is not None else None
            self.kill()
            return CRASH, f"bot process died (exit code {exit_code}): {type(exc).__name__}"

    def kill(self) -> None:
        """Terminate the process immediately."""
        if self._process is not None:
            if self._process.is_alive():
                self._process.kill()
            self._process.join(timeout=5)
        if self._conn is not None:
            self._conn.close()
        self._process, self._conn = None, None

    def close(self) -> None:
        """Ask the process to stop, killing it if it does not."""
        if self._process is not None and self._process.is_alive() and self._conn is not None:
            try:
                self._conn.send(("stop",))
                self._process.join(timeout=2)
            except OSError:
                pass
        self.kill()
