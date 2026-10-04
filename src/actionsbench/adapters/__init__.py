"""Scanner adapters. One module per tool, added one at a time after the tool's real output has
been checked and its rule mapping reviewed (docs/adr/0003-scanner-scope-and-scoring.md)."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from actionsbench.adapters.actionlint import ActionlintAdapter
from actionsbench.adapters.base import ScannerAdapter
from actionsbench.adapters.zizmor import ZizmorAdapter

AdapterFactory = Callable[[Mapping[str, str]], ScannerAdapter]

ADAPTERS: dict[str, AdapterFactory] = {
    "actionlint": ActionlintAdapter.from_options,
    "zizmor": ZizmorAdapter.from_options,
}


def get_adapter(name: str, options: Mapping[str, str] | None = None) -> ScannerAdapter:
    """Build an adapter. Raises ValueError for an unknown tool or an unknown/invalid option."""
    try:
        factory = ADAPTERS[name]
    except KeyError:
        known = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"unknown scanner '{name}' (known: {known})") from None
    return factory(options or {})
