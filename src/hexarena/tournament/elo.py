"""Elo rating system."""

from __future__ import annotations

DEFAULT_K = 32.0
"""How much a single game can move a rating."""

DEFAULT_RATING = 1000.0
"""Rating every bot starts with."""


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that A beats B according to the Elo model.

    ``E_A = 1 / (1 + 10 ** ((R_B - R_A) / 400))``: a 400-point advantage
    means A is expected to win 10 times as often as B.
    """
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def update_elo(
    rating_a: float, rating_b: float, score_a: float, k: float = DEFAULT_K
) -> tuple[float, float]:
    """Return the new ratings of A and B after one game.

    Args:
        rating_a: Rating of A before the game.
        rating_b: Rating of B before the game.
        score_a: 1 if A won, 0 if A lost (Hex has no draws).
        k: K-factor.

    The update is zero-sum: whatever A gains, B loses.
    """
    expected_a = expected_score(rating_a, rating_b)
    delta = k * (score_a - expected_a)
    return rating_a + delta, rating_b - delta
