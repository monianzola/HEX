"""Smoke tests: the package and its subpackages are importable."""

import importlib

import pytest

import hexarena


def test_version_is_defined() -> None:
    assert isinstance(hexarena.__version__, str)
    assert hexarena.__version__


@pytest.mark.parametrize(
    "module", ["hexarena.game", "hexarena.bots", "hexarena.tournament"]
)
def test_subpackages_import(module: str) -> None:
    assert importlib.import_module(module) is not None
