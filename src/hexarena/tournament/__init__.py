"""Round-robin tournament runner, Elo ranking and leaderboard generation.

Run it from the command line with ``python -m hexarena.tournament``.
"""

from hexarena.tournament.elo import expected_score, update_elo
from hexarena.tournament.report import to_html, to_json, write_results
from hexarena.tournament.runner import (
    Entrant,
    GameRecord,
    Standing,
    TournamentConfig,
    TournamentResult,
    compute_standings,
    play_safe_game,
    run_tournament,
)

__all__ = [
    "Entrant",
    "GameRecord",
    "Standing",
    "TournamentConfig",
    "TournamentResult",
    "compute_standings",
    "expected_score",
    "play_safe_game",
    "run_tournament",
    "to_html",
    "to_json",
    "update_elo",
    "write_results",
]
