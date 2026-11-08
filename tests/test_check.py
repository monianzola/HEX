"""Tests for ``python -m hexarena.check`` and the bot template."""

from __future__ import annotations

import pytest

from hexarena.bots import available_bots
from hexarena.check import check_bot, main
from hexarena.game import HexGame, play_game


def test_good_bot_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_bot("random", time_limit=0.5, games=1) is True
    out = capsys.readouterr().out
    assert "Todo correcto" in out
    assert "Contra RandomBot" in out and "Contra ShortestPathBot" in out


def test_cli_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["random", "--time-limit", "0.5", "--games", "1"]) == 0
    assert main(["does-not-exist"]) == 1
    out = capsys.readouterr().out
    assert "No se encuentra el bot" in out
    assert "Bots disponibles" in out


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ("faulty_bots:IllegalBot", "no es legal"),
        ("faulty_bots:WrongTypeBot", "no es una tupla"),
        ("faulty_bots:RaisingBot", "lanza RuntimeError"),
        ("faulty_bots:BrokenInitBot", "No se puede crear sin argumentos"),
    ],
)
def test_broken_bots_are_reported(spec: str, message: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert check_bot(spec, time_limit=0.5, games=1, show_board=False) is False
    out = capsys.readouterr().out
    assert message in out
    assert "Hay errores" in out


def test_slow_bot_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_bot("faulty_bots:SlowBot", time_limit=0.05, games=1, show_board=False) is False
    assert "tarda" in capsys.readouterr().out


def test_template_is_skipped_by_discovery() -> None:
    """Files starting with ``_`` are not bots: the template never enters the tournament."""
    assert "mi-bot" not in available_bots()


def test_template_works_when_copied() -> None:
    from hexarena.bots import unregister_bot
    from hexarena.bots.random_bot import RandomBot

    try:
        from hexarena.bots._plantilla import MiBot

        assert MiBot.name and MiBot.description
        assert check_bot("mi-bot", time_limit=0.5, games=1, show_board=False) is True
        result = play_game(HexGame(5), MiBot(), RandomBot(seed=0), time_limit=0.5)
        assert result.winner == 1
    finally:
        unregister_bot("mi-bot")
