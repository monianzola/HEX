"""Command line interface: ``python -m hexarena.tournament``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from hexarena.tournament.report import REASON_LABELS, write_results
from hexarena.tournament.runner import WIN, GameRecord, TournamentConfig, run_tournament


def build_parser() -> argparse.ArgumentParser:
    defaults = TournamentConfig()
    parser = argparse.ArgumentParser(
        prog="python -m hexarena.tournament",
        description="Round-robin tournament between hexarena bots, with Elo ranking.",
    )
    parser.add_argument("--bots", nargs="+", metavar="BOT",
                        help="bots to include (registered names or module:Class); default: all")
    parser.add_argument("--size", type=int, default=defaults.board_size, help="board size")
    parser.add_argument("--games", type=int, default=defaults.games_per_pair,
                        help="games per pair of bots")
    parser.add_argument("--time-limit", type=float, default=defaults.time_limit,
                        help="seconds per move")
    parser.add_argument("--seed", type=int, default=defaults.seed, help="base random seed")
    parser.add_argument("--output", default="results", help="output directory")
    parser.add_argument("--quiet", action="store_true", help="do not print each game")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.games < 1 or args.size < 1 or args.time_limit <= 0:
        print("error: --games, --size and --time-limit must be positive", file=sys.stderr)
        return 2
    config = TournamentConfig(
        board_size=args.size, games_per_pair=args.games, time_limit=args.time_limit, seed=args.seed
    )

    def progress(game: GameRecord) -> None:
        if args.quiet:
            return
        note = "" if game.reason == WIN else f"  [{game.loser} pierde: {REASON_LABELS[game.reason]}]"
        print(f"#{game.index + 1:>4}  {game.red} (R) vs {game.blue} (B) -> {game.winner}{note}", flush=True)

    try:
        result = run_tournament(args.bots, config, progress)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json_path, html_path = write_results(result, args.output)
    print(f"\n{'#':>2}  {'Bot':<22}{'Elo':>7}{'V':>5}{'D':>5}{'%':>6}")
    for rank, s in enumerate(result.standings, start=1):
        print(f"{rank:>2}  {s.name:<22}{s.elo:>7.0f}{s.wins:>5}{s.losses:>5}{s.win_rate:>6.0%}")
    print(f"\n{len(result.games)} partidas en {result.duration_seconds:.1f} s")
    print(f"Resultados: {json_path}\nClasificación: {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
