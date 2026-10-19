"""Public bot API, bot registry and built-in bots (one file per bot).

Everything a bot author needs can be imported from here::

    from hexarena.bots import Bot, Move, Observation, register_bot
"""

from hexarena.bots.base import Bot
from hexarena.bots.registry import (
    available_bots,
    create_bot,
    discover_bots,
    discovery_errors,
    get_bot,
    register_bot,
    unregister_bot,
)
from hexarena.game.observation import Observation
from hexarena.game.state import BLUE, EMPTY, RED, Move

__all__ = [
    "BLUE",
    "EMPTY",
    "RED",
    "Bot",
    "Move",
    "Observation",
    "available_bots",
    "create_bot",
    "discover_bots",
    "discovery_errors",
    "get_bot",
    "register_bot",
    "unregister_bot",
]
