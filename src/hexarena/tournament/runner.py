"""Round-robin tournament between bots, robust to broken bots."""

from __future__ import annotations

import multiprocessing
import os
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from typing import Any

from hexarena.game import BLUE, RED, HexGame, IllegalMoveError
from hexarena.tournament.elo import DEFAULT_K, DEFAULT_RATING, update_elo
from hexarena.tournament.worker import CRASH, ERROR, OK, TIMEOUT, BotProcess, load_bot_factory

WIN = "connection"
"""Reason of a normal win: the winner connected its edges."""

FORFEIT_REASONS = {ERROR: "exception", TIMEOUT: "timeout", CRASH: "crash"}
ILLEGAL = "illegal"

GRACE_SECONDS = 0.5
"""Extra time on top of ``time_limit`` for process communication."""

STARTUP_TIMEOUT = 15.0
"""Seconds allowed to start a bot process and create the bot."""


@dataclass(frozen=True)
class TournamentConfig:
    """Tournament settings.

    Attributes:
        board_size: Side of the board.
        games_per_pair: Games each pair of bots plays (half with each colour).
        time_limit: Seconds per move.
        seed: Base seed; game ``i`` uses ``seed + i``.
        k_factor: Elo K-factor.
        initial_elo: Starting Elo rating.
    """

    board_size: int = 7
    games_per_pair: int = 20
    time_limit: float = 1.0
    seed: int = 2026
    k_factor: float = DEFAULT_K
    initial_elo: float = DEFAULT_RATING


@dataclass(frozen=True)
class Entrant:
    """A bot taking part in the tournament."""

    bot: str
    name: str
    author: str = ""
    description: str = ""


@dataclass(frozen=True)
class GameRecord:
    """The result of one game.

    Attributes:
        index: Game number (0-based).
        red: Bot playing Red (moves first).
        blue: Bot playing Blue.
        winner: Winning bot.
        loser: Losing bot.
        reason: ``"connection"`` for a normal win, otherwise why the loser
            forfeited: ``"exception"``, ``"timeout"``, ``"illegal"`` or ``"crash"``.
        detail: Human-readable explanation of a forfeit.
        moves: Number of legal moves played.
        seed: Seed used for this game.
    """

    index: int
    red: str
    blue: str
    winner: str
    loser: str
    reason: str
    detail: str
    moves: int
    seed: int


@dataclass
class Standing:
    """A row of the leaderboard."""

    bot: str
    name: str
    author: str
    elo: float
    wins: int = 0
    losses: int = 0
    forfeits: int = 0

    @property
    def games(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0


@dataclass
class TournamentResult:
    """Everything the tournament produced."""

    config: TournamentConfig
    entrants: list[Entrant]
    games: list[GameRecord]
    standings: list[Standing]
    generated_at: str
    commit: str
    duration_seconds: float
    head_to_head: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "generated_at": self.generated_at,
            "commit": self.commit,
            "duration_seconds": round(self.duration_seconds, 1),
            "config": asdict(self.config),
            "entrants": [asdict(e) for e in self.entrants],
            "standings": [
                {
                    "rank": rank,
                    **asdict(s),
                    "elo": round(s.elo, 1),
                    "games": s.games,
                    "win_rate": round(s.win_rate, 4),
                }
                for rank, s in enumerate(self.standings, start=1)
            ],
            "head_to_head": self.head_to_head,
            "games": [asdict(g) for g in self.games],
        }


def play_safe_game(
    game: HexGame,
    red: BotProcess,
    blue: BotProcess,
    time_limit: float,
    seed: int,
) -> tuple[int, str, str, int]:
    """Play one game between two bot processes.

    A bot that raises, runs out of time, crashes or plays an illegal move
    loses immediately; the game never raises.

    Returns:
        ``(winner_colour, reason, detail, moves_played)``.
    """
    players = {RED: red, BLUE: blue}
    for colour, proc in players.items():
        status, payload = proc.request(("new", seed), timeout=STARTUP_TIMEOUT)
        if status != OK:
            return _other(colour), FORFEIT_REASONS[status], f"could not start: {payload}", 0

    state = game.initial_state()
    moves = 0
    while not game.is_terminal(state):
        colour = game.current_player(state)
        observation = game.observation(state, colour, time_limit)
        status, payload = players[colour].request(
            ("move", observation), timeout=time_limit + GRACE_SECONDS
        )
        if status != OK:
            return _other(colour), FORFEIT_REASONS[status], str(payload), moves
        try:
            state = game.play(state, payload)
        except IllegalMoveError as exc:
            return _other(colour), ILLEGAL, f"{payload!r}: {exc}", moves
        moves += 1
    winner = game.winner(state)
    assert winner is not None
    return winner, WIN, "", moves


def run_tournament(
    bots: Sequence[str] | None = None,
    config: TournamentConfig | None = None,
    progress: Callable[[GameRecord], None] | None = None,
) -> TournamentResult:
    """Play a round-robin tournament and compute the leaderboard.

    Args:
        bots: Registered bot names or ``"module:Class"`` paths. Defaults to
            every registered bot.
        config: Tournament settings.
        progress: Called after every game (useful for printing progress).

    Raises:
        ValueError: If fewer than two distinct bots are given.
    """
    from hexarena.bots import available_bots

    config = config or TournamentConfig()
    specs = list(bots) if bots is not None else available_bots()
    if len(specs) != len(set(specs)):
        raise ValueError(f"Duplicate bots in {specs}")
    if len(specs) < 2:
        raise ValueError("A tournament needs at least two bots")

    started = time.perf_counter()
    entrants = [_describe(spec) for spec in specs]
    game = HexGame(config.board_size)
    context = multiprocessing.get_context("spawn")
    processes = {spec: BotProcess(spec, context) for spec in specs}
    records: list[GameRecord] = []
    try:
        for a, b in combinations(specs, 2):
            for i in range(config.games_per_pair):
                red, blue = (a, b) if i % 2 == 0 else (b, a)
                index = len(records)
                seed = config.seed + index
                colour, reason, detail, moves = play_safe_game(
                    game, processes[red], processes[blue], config.time_limit, seed
                )
                winner, loser = (red, blue) if colour == RED else (blue, red)
                record = GameRecord(index, red, blue, winner, loser, reason, detail, moves, seed)
                records.append(record)
                if progress is not None:
                    progress(record)
    finally:
        for proc in processes.values():
            proc.close()

    return TournamentResult(
        config=config,
        entrants=entrants,
        games=records,
        standings=compute_standings(entrants, records, config),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        commit=current_commit(),
        duration_seconds=time.perf_counter() - started,
        head_to_head=_head_to_head(specs, records),
    )


def compute_standings(
    entrants: Sequence[Entrant], records: Sequence[GameRecord], config: TournamentConfig
) -> list[Standing]:
    """Win/loss counts and Elo (updated game by game, in order), best first."""
    table = {
        e.bot: Standing(bot=e.bot, name=e.name, author=e.author, elo=config.initial_elo)
        for e in entrants
    }
    for game in records:
        winner, loser = table[game.winner], table[game.loser]
        winner.wins += 1
        loser.losses += 1
        if game.reason != WIN:
            loser.forfeits += 1
        winner.elo, loser.elo = update_elo(winner.elo, loser.elo, 1.0, config.k_factor)
    return sorted(table.values(), key=lambda s: (-s.elo, -s.wins, s.bot))


def current_commit() -> str:
    """Commit being evaluated: ``GITHUB_SHA`` in CI, otherwise ``git rev-parse``."""
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _head_to_head(specs: Sequence[str], records: Sequence[GameRecord]) -> dict[str, dict[str, int]]:
    """``table[a][b]`` = games ``a`` won against ``b``."""
    table = {a: {b: 0 for b in specs if b != a} for a in specs}
    for game in records:
        table[game.winner][game.loser] += 1
    return table


def _describe(spec: str) -> Entrant:
    try:
        cls = load_bot_factory(spec)
    except Exception:  # noqa: BLE001 - it will lose its games with reason "exception"
        return Entrant(bot=spec, name=spec)
    return Entrant(
        bot=spec,
        name=getattr(cls, "name", "") or spec,
        author=getattr(cls, "author", "") or "",
        description=getattr(cls, "description", "") or "",
    )


def _other(colour: int) -> int:
    return BLUE if colour == RED else RED
