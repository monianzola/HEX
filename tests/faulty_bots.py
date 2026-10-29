"""Deliberately broken bots used by the tournament tests.

They are NOT registered, so they never appear in the real tournament or in
the contract tests. The tournament loads them by import path, for example
``"faulty_bots:RaisingBot"``.
"""

from __future__ import annotations

import os

from hexarena.bots import Bot, Move, Observation


class RaisingBot(Bot):
    name = "RaisingBot"
    description = "Raises an exception on its first move."

    def choose_move(self, observation: Observation) -> Move:
        raise RuntimeError("boom")


class InfiniteLoopBot(Bot):
    name = "InfiniteLoopBot"
    description = "Never returns."

    def choose_move(self, observation: Observation) -> Move:
        while True:
            pass


class IllegalBot(Bot):
    name = "IllegalBot"
    description = "Plays off the board."

    def choose_move(self, observation: Observation) -> Move:
        return (-1, -1)


class WrongTypeBot(Bot):
    name = "WrongTypeBot"
    description = "Returns a string instead of a move."

    def choose_move(self, observation: Observation) -> Move:
        return "a1"  # type: ignore[return-value]


class DyingBot(Bot):
    name = "DyingBot"
    description = "Kills its own process."

    def choose_move(self, observation: Observation) -> Move:
        os._exit(3)


class BrokenInitBot(Bot):
    name = "BrokenInitBot"
    description = "Fails when created."

    def __init__(self) -> None:
        raise ValueError("cannot start")

    def choose_move(self, observation: Observation) -> Move:  # pragma: no cover
        return observation.legal_moves[0]
