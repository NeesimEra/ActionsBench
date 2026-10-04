"""Scanner adapters. One module per tool, added one at a time after the tool's real output has
been checked and its rule mapping reviewed (docs/adr/0003-scanner-scope-and-scoring.md)."""

from __future__ import annotations

from collections.abc import Callable

from actionsbench.adapters.base import ScannerAdapter
from actionsbench.adapters.zizmor import ZizmorAdapter

ADAPTERS: dict[str, Callable[[], ScannerAdapter]] = {
    "zizmor": ZizmorAdapter,
}


def get_adapter(name: str) -> ScannerAdapter:
    try:
        factory = ADAPTERS[name]
    except KeyError:
        known = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"unknown scanner '{name}' (known: {known})") from None
    return factory()
