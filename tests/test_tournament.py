"""Tests for the tournament: Elo, robustness against broken bots, reports and CLI."""

from __future__ import annotations

import json

import pytest

from hexarena.tournament import (
    Entrant,
    GameRecord,
    TournamentConfig,
    compute_standings,
    expected_score,
    run_tournament,
    to_html,
    update_elo,
    write_results,
)
from hexarena.tournament.__main__ import main

# Small and fast settings for tests.
FAST = TournamentConfig(board_size=5, games_per_pair=2, time_limit=0.3, seed=7)


# --------------------------------------------------------------------------- Elo


def test_expected_score_is_symmetric() -> None:
    assert expected_score(1000, 1000) == pytest.approx(0.5)
    assert expected_score(1400, 1000) == pytest.approx(10 / 11)
    assert expected_score(1200, 1000) + expected_score(1000, 1200) == pytest.approx(1)


def test_update_elo_is_zero_sum() -> None:
    a, b = update_elo(1000, 1000, 1.0, k=32)
    assert (a, b) == pytest.approx((1016, 984))
    assert a + b == pytest.approx(2000)


def test_beating_a_stronger_bot_gives_more_points() -> None:
    upset, _ = update_elo(1000, 1400, 1.0)
    expected_win, _ = update_elo(1400, 1000, 1.0)
    assert upset - 1000 > expected_win - 1400


def _record(i: int, winner: str, loser: str, reason: str = "connection") -> GameRecord:
    return GameRecord(i, winner, loser, winner, loser, reason, "", 10, i)


def test_standings_order_and_counts() -> None:
    entrants = [Entrant("a", "A"), Entrant("b", "B"), Entrant("c", "C")]
    records = [
        _record(0, "a", "b"),
        _record(1, "a", "c"),
        _record(2, "b", "c", reason="timeout"),
        _record(3, "a", "b"),
    ]
    standings = compute_standings(entrants, records, TournamentConfig())
    assert [s.bot for s in standings] == ["a", "b", "c"]
    a, b, c = standings
    assert (a.wins, a.losses, a.games, a.win_rate) == (3, 0, 3, 1.0)
    assert (b.wins, b.losses) == (1, 2)
    assert (c.wins, c.losses, c.forfeits) == (0, 2, 1)
    assert sum(s.elo for s in standings) == pytest.approx(3000)


# --------------------------------------------------------------------------- real games


def test_tournament_between_real_bots() -> None:
    result = run_tournament(["random", "shortest-path"], FAST)
    assert len(result.games) == 2
    # Each bot plays each colour once.
    assert {(g.red, g.blue) for g in result.games} == {("random", "shortest-path"), ("shortest-path", "random")}
    assert all(g.reason == "connection" for g in result.games)
    assert result.standings[0].bot == "shortest-path"
    assert result.head_to_head["shortest-path"]["random"] == 2


def test_tournament_is_reproducible_with_fixed_seed() -> None:
    """RandomBot receives the game seed, so the same seed replays the same games."""
    config = TournamentConfig(board_size=7, games_per_pair=4, time_limit=0.3, seed=11)
    first = run_tournament(["random", "shortest-path"], config)
    second = run_tournament(["random", "shortest-path"], config)
    assert [(g.winner, g.moves) for g in first.games] == [(g.winner, g.moves) for g in second.games]


@pytest.mark.parametrize(
    ("bot", "reason"),
    [
        ("faulty_bots:RaisingBot", "exception"),
        ("faulty_bots:InfiniteLoopBot", "timeout"),
        ("faulty_bots:IllegalBot", "illegal"),
        ("faulty_bots:WrongTypeBot", "illegal"),
        ("faulty_bots:DyingBot", "crash"),
        ("faulty_bots:BrokenInitBot", "exception"),
        ("faulty_bots:DoesNotExist", "exception"),
    ],
    ids=["exception", "infinite-loop", "illegal", "wrong-type", "process-dies", "broken-init", "missing"],
)
def test_broken_bot_loses_and_tournament_continues(bot: str, reason: str) -> None:
    result = run_tournament(["random", bot], FAST)
    assert len(result.games) == FAST.games_per_pair  # Every game was played.
    for game in result.games:
        assert game.loser == bot
        assert game.winner == "random"
        assert game.reason == reason
        assert game.detail
    broken = next(s for s in result.standings if s.bot == bot)
    assert broken.forfeits == FAST.games_per_pair
    assert result.standings[0].bot == "random"


def test_many_broken_bots_in_one_tournament() -> None:
    bots = ["random", "faulty_bots:RaisingBot", "faulty_bots:InfiniteLoopBot", "faulty_bots:IllegalBot"]
    result = run_tournament(bots, FAST)
    assert len(result.games) == 6 * FAST.games_per_pair
    assert result.standings[0].bot == "random"
    assert result.standings[0].wins == 3 * FAST.games_per_pair


def test_invalid_bot_lists() -> None:
    with pytest.raises(ValueError):
        run_tournament(["random"], FAST)
    with pytest.raises(ValueError):
        run_tournament(["random", "random"], FAST)


# --------------------------------------------------------------------------- reports and CLI


def test_reports_are_written(tmp_path) -> None:
    result = run_tournament(["random", "faulty_bots:RaisingBot"], FAST)
    json_path, html_path = write_results(result, tmp_path / "out")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["config"]["board_size"] == 5
    assert data["standings"][0]["bot"] == "random"
    assert data["standings"][0]["rank"] == 1
    assert len(data["games"]) == 2
    assert data["games"][0]["reason"] == "exception"

    html = html_path.read_text(encoding="utf-8")
    assert "<table" in html and "RandomBot" in html and "excepción" in html
    assert result.commit[:7] in html or result.commit == "unknown"


def test_html_escapes_bot_names() -> None:
    result = run_tournament(["random", "faulty_bots:RaisingBot"], FAST)
    result.standings[1].name = "<script>alert(1)</script>"
    assert "<script>alert" not in to_html(result)


def test_cli(tmp_path, capsys) -> None:
    code = main(["--bots", "random", "shortest-path", "--size", "5", "--games", "2",
                 "--time-limit", "0.3", "--output", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "ShortestPathBot" in out
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "results.json").exists()


def test_cli_rejects_bad_arguments(tmp_path) -> None:
    assert main(["--games", "0", "--output", str(tmp_path)]) == 2
    assert main(["--bots", "random", "--output", str(tmp_path)]) == 2


# --------------------------------------------------------------------------- worker protocol (in-process)


def _run_worker(spec: str, messages: list[tuple]) -> list[tuple]:
    """Drive ``worker_main`` in a thread through a real pipe and collect the replies."""
    import threading
    from multiprocessing import Pipe

    from hexarena.tournament.worker import worker_main

    parent, child = Pipe()
    thread = threading.Thread(target=worker_main, args=(child, spec), daemon=True)
    thread.start()
    replies = []
    for message in messages:
        parent.send(message)
        replies.append(parent.recv())
    parent.send(("stop",))
    thread.join(timeout=5)
    assert not thread.is_alive()
    return replies


def test_worker_protocol_with_a_good_bot() -> None:
    from hexarena.game import HexGame

    game = HexGame(3)
    obs = game.observation(game.initial_state(), 1)
    replies = _run_worker("random", [("new", 1), ("move", obs), ("bogus",)])
    assert replies[0] == ("ok", None)
    assert replies[1][0] == "ok" and replies[1][1] in obs.legal_moves
    assert replies[2][0] == "error" and "unknown request" in replies[2][1]


def test_worker_reports_bot_errors_without_dying() -> None:
    from hexarena.game import HexGame

    game = HexGame(3)
    obs = game.observation(game.initial_state(), 1)
    replies = _run_worker("faulty_bots:RaisingBot", [("new", 1), ("move", obs), ("move", obs)])
    assert replies[0] == ("ok", None)
    assert replies[1][0] == replies[2][0] == "error"
    assert "RuntimeError: boom" in replies[1][1]


def test_worker_reports_load_errors() -> None:
    replies = _run_worker("no_such_module:Bot", [("new", 1)])
    assert replies[0][0] == "error" and "cannot load bot" in replies[0][1]


def test_worker_stops_when_the_pipe_closes() -> None:
    import threading
    from multiprocessing import Pipe

    from hexarena.tournament.worker import worker_main

    parent, child = Pipe()
    thread = threading.Thread(target=worker_main, args=(child, "random"), daemon=True)
    thread.start()
    parent.close()
    thread.join(timeout=5)
    assert not thread.is_alive()
