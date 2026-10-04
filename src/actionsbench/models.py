"""Data model shared by the corpus loader, the SARIF parser and the scorer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from actionsbench.taxonomy import WeaknessClass


class Provenance(StrEnum):
    SYNTHETIC_MINIMAL = "synthetic-minimal"
    DERIVED_FROM_ADVISORY = "derived-from-advisory"


class Status(StrEnum):
    # One reviewer so far: the label is the author's claim, not yet independently checked.
    PROPOSED = "proposed"
    AGREED = "agreed"
    DISPUTED = "disputed"


@dataclass(frozen=True, slots=True)
class ExpectedFinding:
    """A weakness a scanner is expected to report, anchored at the sink.

    `evidence` is a substring that must appear on `line`; it keeps labels honest when
    a case file is edited and the line numbers move.
    """

    weakness_class: WeaknessClass
    file: str
    line: int
    evidence: str


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    root: Path
    title: str
    is_negative: bool
    expected: tuple[ExpectedFinding, ...]
    rationale: str
    references: tuple[str, ...]
    provenance: Provenance
    status: Status
    author: str
    reviewer: str | None
    added_in: str
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class Finding:
    """A scanner finding, normalized to the benchmark's vocabulary."""

    case_id: str
    weakness_class: WeaknessClass
    file: str
    line: int
    rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class ScannerReport:
    """Everything a scanner run produced, plus what it claims to cover.

    `cases_run` makes "ran and found nothing" distinct from "never ran": cases outside
    it are excluded from scoring instead of being counted as clean.
    """

    tool: str
    version: str
    scope: frozenset[WeaknessClass]
    cases_run: frozenset[str]
    findings: tuple[Finding, ...]
