"""Base class that every bot must inherit from."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from hexarena.game.observation import Observation
from hexarena.game.state import Move


class Bot(ABC):
    """Base class for Hex bots.

    To create a bot, subclass ``Bot``, implement :meth:`choose_move` and
    register the class with :func:`~hexarena.bots.register_bot`.

    A bot must be constructible without arguments: the tournament and
    the web app create bots by calling ``BotClass()``.

    Attributes:
        name: Human-readable name shown in the web app and the leaderboard.
            Defaults to the name used in ``@register_bot``.
        author: Author or team.
        description: One sentence explaining how the bot plays.
    """

    name: ClassVar[str] = ""
    author: ClassVar[str] = ""
    description: ClassVar[str] = ""

    @abstractmethod
    def choose_move(self, observation: Observation) -> Move:
        """Choose the next move.

        Args:
            observation: Read-only view of the game: board, size, which
                player you are, legal moves and time available.

        Returns:
            A move ``(row, col)`` that must be in ``observation.legal_moves``.
            The bot must answer within ``observation.time_limit`` seconds.
        """
