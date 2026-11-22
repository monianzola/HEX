"""InesBot: bridge-aware alpha-beta search with a wider candidate set."""

from __future__ import annotations

from hexarena.bots import register_bot
from hexarena.bots.bridges import BridgeBot


@register_bot("ines")
class InesBot(BridgeBot):
    """Build on the leading bridge strategy while searching more candidate moves."""

    name = "InesBot"
    author = "Inés"
    description = (
        "Búsqueda alfa-beta con evaluación de puentes y hasta 24 candidatas por nodo."
    )

    def __init__(self) -> None:
        super().__init__(max_candidates=24)
