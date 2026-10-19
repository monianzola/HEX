"""Tests for the bot API: base class, registry, discovery and RandomBot."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from hexarena.bots import (
    Bot,
    Move,
    Observation,
    available_bots,
    create_bot,
    discover_bots,
    discovery_errors,
    get_bot,
    register_bot,
    unregister_bot,
)
from hexarena.bots.random_bot import RandomBot
from hexarena.game import HexGame

TEMP_NAMES = ("test-first", "test-other", "test-named")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    yield
    for name in TEMP_NAMES:
        unregister_bot(name)


def make_bot_class(description: str = "test bot") -> type[Bot]:
    class FirstCellBot(Bot):
        def choose_move(self, observation: Observation) -> Move:
            return observation.legal_moves[0]

    FirstCellBot.description = description
    return FirstCellBot


def test_bot_is_abstract() -> None:
    with pytest.raises(TypeError):
        Bot()  # type: ignore[abstract]


def test_register_and_create() -> None:
    cls = register_bot("test-first")(make_bot_class())
    assert "test-first" in available_bots()
    assert get_bot("test-first") is cls
    bot = create_bot("test-first")
    obs = HexGame(3).observation(HexGame(3).initial_state(), 1)
    assert bot.choose_move(obs) == (0, 0)


def test_registry_name_becomes_default_display_name() -> None:
    cls = register_bot("test-first")(make_bot_class())
    assert cls.name == "test-first"


def test_explicit_display_name_is_kept() -> None:
    @register_bot("test-named")
    class Named(Bot):
        name = "Pretty Name"

        def choose_move(self, observation: Observation) -> Move:
            return observation.legal_moves[0]

    assert Named.name == "Pretty Name"


def test_duplicate_name_from_other_class_is_rejected() -> None:
    register_bot("test-first")(make_bot_class())

    class Other(Bot):
        def choose_move(self, observation: Observation) -> Move:
            return observation.legal_moves[0]

    with pytest.raises(ValueError, match="already used"):
        register_bot("test-first")(Other)


def test_registering_the_same_class_twice_is_allowed() -> None:
    cls = make_bot_class()
    register_bot("test-first")(cls)
    register_bot("test-first")(cls)  # e.g. a module imported twice
    assert get_bot("test-first") is cls


@pytest.mark.parametrize("name", ["", "   ", None, 3])
def test_invalid_names_are_rejected(name: object) -> None:
    with pytest.raises(ValueError):
        register_bot(name)  # type: ignore[arg-type]


def test_only_bot_subclasses_can_be_registered() -> None:
    class NotABot:
        def choose_move(self, observation: Observation) -> Move:
            return (0, 0)

    with pytest.raises(TypeError):
        register_bot("test-other")(NotABot)  # type: ignore[type-var]


def test_unknown_bot_gives_helpful_error() -> None:
    with pytest.raises(KeyError, match="Available bots"):
        get_bot("does-not-exist")


def test_discovery_finds_builtin_bots_without_errors() -> None:
    bots = discover_bots()
    assert bots["random"] is RandomBot
    assert discovery_errors() == {}


def test_broken_bot_module_does_not_break_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    import hexarena.bots.registry as registry

    real_import = importlib.import_module

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "hexarena.bots.random_bot":
            raise RuntimeError("boom")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(registry.importlib, "import_module", fake_import)
    with pytest.warns(UserWarning, match="boom"):
        bots = discover_bots()
    assert "hexarena.bots.random_bot" in discovery_errors()
    assert "random" in bots  # Already registered bots stay available.

    monkeypatch.undo()
    discover_bots()
    assert discovery_errors() == {}


def test_random_bot_metadata() -> None:
    assert RandomBot.name == "RandomBot"
    assert RandomBot.author
    assert RandomBot.description


def test_random_bot_is_reproducible_with_seed() -> None:
    game = HexGame(7)
    obs = game.observation(game.initial_state(), 1)
    a = [RandomBot(seed=5).choose_move(obs) for _ in range(3)]
    b = [RandomBot(seed=5).choose_move(obs) for _ in range(3)]
    assert a == b
