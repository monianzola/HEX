"""Bot registry and automatic discovery of the files in ``hexarena/bots/``."""

from __future__ import annotations

import importlib
import pkgutil
import warnings
from collections.abc import Callable
from typing import Any, TypeVar

from hexarena.bots.base import Bot

B = TypeVar("B", bound=type[Bot])

_REGISTRY: dict[str, type[Bot]] = {}
_DISCOVERY_ERRORS: dict[str, str] = {}
_discovered = False

# Modules of the bots package that are infrastructure, not bots.
_INTERNAL_MODULES = frozenset({"base", "registry"})


def register_bot(name: str) -> Callable[[B], B]:
    """Class decorator that registers a bot under ``name``.

    Example:
        >>> from hexarena.bots import Bot, register_bot
        >>> @register_bot("first-cell")
        ... class FirstCellBot(Bot):
        ...     description = "Always plays the first legal move."
        ...     def choose_move(self, observation):
        ...         return observation.legal_moves[0]

    If the class does not define ``name`` itself, ``name`` is set to the
    registry key.

    Args:
        name: Unique identifier of the bot (used by the tournament and the web).

    Raises:
        ValueError: If ``name`` is empty or already used by another bot.
        TypeError: If the decorated object is not a subclass of :class:`Bot`.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Bot name must be a non-empty string, got {name!r}")

    def decorator(cls: B) -> B:
        if not (isinstance(cls, type) and issubclass(cls, Bot)):
            raise TypeError(f"@register_bot can only decorate subclasses of Bot, got {cls!r}")
        existing = _REGISTRY.get(name)
        if existing is not None and _qualified_name(existing) != _qualified_name(cls):
            raise ValueError(
                f"Bot name {name!r} is already used by {_qualified_name(existing)}"
            )
        if not cls.__dict__.get("name"):
            cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def unregister_bot(name: str) -> None:
    """Remove a bot from the registry (mainly useful in tests)."""
    _REGISTRY.pop(name, None)


def discover_bots() -> dict[str, type[Bot]]:
    """Import every module in the ``hexarena.bots`` package.

    Importing a module runs its ``@register_bot`` decorators, so every
    bot file is registered without being listed anywhere. A module that
    fails to import does not stop the others: the error is recorded in
    :func:`discovery_errors` and a warning is emitted.

    Returns:
        A copy of the registry: ``{name: bot class}``.
    """
    global _discovered
    package = importlib.import_module("hexarena.bots")
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_") or info.name in _INTERNAL_MODULES:
            continue
        module_name = f"{package.__name__}.{info.name}"
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - a broken bot must not break the platform
            _DISCOVERY_ERRORS[module_name] = f"{type(exc).__name__}: {exc}"
            warnings.warn(f"Could not load bot module {module_name}: {exc}", stacklevel=2)
        else:
            _DISCOVERY_ERRORS.pop(module_name, None)
    _discovered = True
    return dict(_REGISTRY)


def available_bots() -> list[str]:
    """Return the names of every registered bot, sorted alphabetically."""
    _ensure_discovered()
    return sorted(_REGISTRY)


def get_bot(name: str) -> type[Bot]:
    """Return the bot class registered under ``name``.

    Raises:
        KeyError: If no bot has that name.
    """
    _ensure_discovered()
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"No bot named {name!r}. Available bots: {', '.join(sorted(_REGISTRY))}"
        ) from None


def create_bot(name: str, **kwargs: Any) -> Bot:
    """Create an instance of the bot registered under ``name``."""
    return get_bot(name)(**kwargs)


def discovery_errors() -> dict[str, str]:
    """Return the modules that failed to load: ``{module: error}``."""
    _ensure_discovered()
    return dict(_DISCOVERY_ERRORS)


def _ensure_discovered() -> None:
    if not _discovered:
        discover_bots()


def _qualified_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"
