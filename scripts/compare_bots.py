"""Compare the built-in bots head to head.

Plays every pair of bots on a 7x7 board, 20 games per pair alternating
colours, and prints the leaderboard and the head-to-head matrix. It reuses
the tournament engine, so every bot runs in its own process with a time
limit.

Usage::

    python scripts/compare_bots.py
    python scripts/compare_bots.py --games 10 --time-limit 0.5
    python scripts/compare_bots.py --bots mcts alpha-beta

Note: AlphaBetaBot and ShortestPathBot are deterministic, so between the
two of them only two different games exist (one per colour); the 20 games
repeat them. MCTSBot and RandomBot receive a different seed every game.
"""

from __future__ import annotations

import argparse
import sys

from hexarena.tournament import TournamentConfig, run_tournament

DEFAULT_BOTS = ["mcts", "alpha-beta", "shortest-path", "random"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--bots", nargs="+", default=DEFAULT_BOTS)
    parser.add_argument("--size", type=int, default=7)
    parser.add_argument("--games", type=int, default=20, help="games per pair")
    parser.add_argument("--time-limit", type=float, default=1.0, help="seconds per move")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args(argv)

    config = TournamentConfig(
        board_size=args.size, games_per_pair=args.games, time_limit=args.time_limit, seed=args.seed
    )
    total = len(args.bots) * (len(args.bots) - 1) // 2 * args.games
    print(f"{total} games on {args.size}x{args.size}, {args.time_limit}s per move...\n", flush=True)
    result = run_tournament(
        args.bots,
        config,
        progress=lambda g: print(f"\r{g.index + 1}/{total}", end="", flush=True),
    )

    names = {e.bot: e.name for e in result.entrants}
    print(f"\n\n{'#':>2}  {'Bot':<18}{'Elo':>6}{'W':>5}{'L':>5}{'Win %':>7}")
    for rank, s in enumerate(result.standings, start=1):
        print(f"{rank:>2}  {s.name:<18}{s.elo:>6.0f}{s.wins:>5}{s.losses:>5}{s.win_rate:>7.0%}")

    order = [s.bot for s in result.standings]
    width = max(len(names[b]) for b in order) + 2
    print("\nHead to head (row's wins - losses against column):\n")
    print(" " * width + "".join(f"{names[b]:>{width}}" for b in order))
    for a in order:
        cells = "".join(
            f"{'-':>{width}}" if a == b
            else f"{result.head_to_head[a][b]}-{result.head_to_head[b][a]}".rjust(width)
            for b in order
        )
        print(f"{names[a]:<{width}}{cells}")

    forfeits = [g for g in result.games if g.reason != "connection"]
    if forfeits:
        print(f"\n{len(forfeits)} forfeits:")
        for g in forfeits:
            print(f"  game {g.index + 1}: {g.loser} ({g.reason}) {g.detail}")
    print(f"\nFinished in {result.duration_seconds:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
