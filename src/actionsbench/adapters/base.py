"""The contract between the runner and a scanner.

An adapter knows four things about one tool: how to invoke it on a directory, which exit
codes mean "it ran", how to turn its output into normalized findings, and which weakness
classes it is judged on. Everything else (isolation, timeouts, the not-run rule, writing the
findings file) is the runner's job, so adapters stay small and reviewable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from actionsbench.models import Finding
from actionsbench.taxonomy import WeaknessClass


class ScannerOutputError(Exception):
    """The tool ran but its output could not be understood for this case."""


@dataclass(slots=True)
class ScannerOutput:
    findings: list[Finding] = field(default_factory=list)
    # Rule IDs the adapter has no mapping for. They are surfaced, never dropped silently.
    unmapped_rule_ids: set[str] = field(default_factory=set)
    # Rule IDs of results that had no usable file and line.
    locationless: list[str] = field(default_factory=list)
    # The tool version as reported by the tool's own output, when it reports one.
    reported_version: str | None = None


class ScannerAdapter(Protocol):
    name: str
    # The pinned version the adapter was written against. The runner fails a case whose output
    # reports a different version, so results always name the version they came from.
    expected_version: str | None
    # Classes the tool is judged on. This is the intersection of what the tool claims to cover
    # and what has a reviewed rule mapping; it grows as mappings are reviewed.
    scope: frozenset[WeaknessClass]
    ok_exit_codes: frozenset[int]
    raw_suffix: str

    @property
    def label(self) -> str:
        """Directory-safe identifier of this tool and pinned version."""
        ...

    def command(self, scan_dir: Path) -> list[str]: ...

    def parse(self, stdout: str, *, case_id: str, scan_dir: Path) -> ScannerOutput: ...
