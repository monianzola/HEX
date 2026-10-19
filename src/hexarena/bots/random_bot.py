"""RandomBot: the simplest possible bot, and a template for your own.

To write a new bot, copy this file into ``src/hexarena/bots/`` with a new
name (for example ``my_bot.py``) and change three things:

1. The name passed to ``@register_bot``: it must be unique.
2. The ``name``, ``author`` and ``description`` attributes.
3. The body of ``choose_move``.

Nothing else in the project needs to change: the registry imports every
file in this folder automatically, so the tournament, the web app and the
test suite will find the new bot on their own.
"""

from __future__ import annotations

import random

# Import only from the public API, never from the game internals.
from hexarena.bots import Bot, Move, Observation, register_bot


@register_bot("random")
class RandomBot(Bot):
    """Plays a uniformly random legal move.

    It is the weakest possible opponent, so it serves as a baseline: any
    bot worth including in the tournament should beat it almost always.

    Args:
        seed: Optional seed for reproducible games. Without a seed every
            game is different.
    """

    name = "RandomBot"
    author = "hex-arena team"
    description = "Plays a uniformly random legal move."

    def __init__(self, seed: int | None = None) -> None:
        # Each bot has its own random generator, so it never interferes
        # with other bots or with the global ``random`` module.
        self._rng = random.Random(seed)

    def choose_move(self, observation: Observation) -> Move:
        """Return a random cell among ``observation.legal_moves``.

        The observation also includes ``board``, ``size``, ``player``
        (1 = Red, top-bottom; 2 = Blue, left-right) and ``time_limit``,
        which smarter bots use to evaluate the position.
        """
        return self._rng.choice(observation.legal_moves)
