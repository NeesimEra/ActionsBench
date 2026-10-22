"""Corpus and results loading for the platform, through the harness's own code.

Everything here reuses `actionsbench` so that the site can never disagree with the CLI:
the same loader validates the corpus, the same schema validator accepts findings
documents, and the same `score()` call produces the numbers the site renders.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from actionsbench.cli import default_corpus
from actionsbench.corpus import require_valid_corpus, validate_json
from actionsbench.models import Case, Finding, ScannerReport
from actionsbench.scoring import ScoreResult, score
from actionsbench.taxonomy import WeaknessClass

# Nothing bigger than a case fixture is ever served; a byte cap keeps the file view honest.
MAX_FILE_BYTES = 64_000
# Findings documents are scored in-process on every request; reject absurd inputs up front.
MAX_FINDINGS_BYTES = 1_000_000


class FindingsDocumentError(ValueError):
    """The findings document is not a schema-valid harness output."""


class ReloadError(ValueError):
    """A file the platform was asked to serve does not exist, or escaped its case."""


@dataclass(frozen=True, slots=True)
class PlatformData:
    """An immutable snapshot: validated corpus plus the paths a request may reach."""

    cases: dict[str, Case]  # every case by id, insertion order = corpus order
    corpus_cases_dir: Path  # directory the case file text is read from

    @property
    def repo_docs(self) -> Path:
        # The corpus lives at <repo>/corpus/cases; dated audit records live in <repo>/docs.
        return self.corpus_cases_dir.parent.parent / "docs"

    @property
    def corpus_version(self) -> str:
        """The corpus release this snapshot came from, per corpus/CHANGELOG.md.

        ADR 0007 requires results to name the corpus version they were scored against;
        the changelog's first `## X.Y.Z` heading is the released version.
        """
        changelog = self.corpus_cases_dir.parent / "CHANGELOG.md"
        try:
            for line in changelog.read_text(encoding="utf-8").splitlines():
                if line.startswith("## "):
                    return line.removeprefix("## ").split()[0]
        except OSError:
            pass
        return "unknown"

    @staticmethod
    def load(corpus_dir: Path | None = None) -> PlatformData:
        root = corpus_dir if corpus_dir is not None else default_corpus()
        cases: dict[str, Case] = {}
        for case in require_valid_corpus(root):
            cases[case.id] = case
        return PlatformData(cases=cases, corpus_cases_dir=root)

    def case(self, case_id: str) -> Case | None:
        return self.cases.get(case_id)

    def counts(self) -> tuple[Counter[str], Counter[str]]:
        by_class: Counter[str] = Counter()
        by_status: Counter[str] = Counter()
        for case in self.cases.values():
            by_status[case.status.value] += 1
            if case.is_negative:
                by_class["(negative case)"] += 1
            for cls in {e.weakness_class for e in case.expected}:
                by_class[cls.value] += 1
        return by_class, by_status

    def cases_in_class(self, cls: WeaknessClass) -> list[Case]:
        selected = [c for c in self.cases.values() if cls in {e.weakness_class for e in c.expected}]
        # Negatives first keeps "the twin the positive is measured against" adjacent.
        return sorted(selected, key=lambda c: (not c.is_negative, c.id))

    def class_listing(self) -> list[tuple[WeaknessClass, int, int]]:
        """Every weakness class in the taxonomy with (positive, negative) case counts."""
        listing: list[tuple[WeaknessClass, int, int]] = []
        for cls in WeaknessClass:
            positives = sum(
                1
                for c in self.cases.values()
                if not c.is_negative and cls in {e.weakness_class for e in c.expected}
            )
            negatives = sum(
                1
                for c in self.cases.values()
                if c.is_negative and cls in {e.weakness_class for e in c.expected}
            )
            if positives or negatives:
                listing.append((cls, positives, negatives))
        return listing

    def classes_of(self, case: Case) -> list[str]:
        """Unique class values of a case's expected findings, in first-mentioned order."""
        seen: list[str] = []
        for e in case.expected:
            if e.weakness_class.value not in seen:
                seen.append(e.weakness_class.value)
        return seen

    def case_files(self, case: Case) -> list[Path]:
        """Every file of the case, fixture or otherwise, in stable order."""
        return sorted(p for p in case.root.rglob("*") if p.is_file() and p.name != "case.yaml")

    def file_text(self, case: Case, relative: str) -> str:
        """Text of one case file at `relative` (no leading slash backslash), plain UTF-8.

        Serves only files that belong to this case, so a URL cannot read anything else.
        """
        if not relative or relative.startswith(("/", "\\")):
            raise ReloadError("expected a path inside the case directory")
        path = (case.root / relative).resolve()
        if not path.is_relative_to(case.root.resolve()) or not path.is_file():
            raise ReloadError(f"no such file in case {case.id}: {relative}")
        if path.name == "case.yaml":
            # The listing hides it, so the endpoint refuses it too: case metadata is
            # rendered structurally on the case page instead.
            raise ReloadError(f"case.yaml is shown on the case page, not as a file: {relative}")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ReloadError(f"file too large to show: {relative}")
        return path.read_text(encoding="utf-8", errors="replace")


def read_findings(path: Path) -> tuple[ScannerReport | None, tuple[str, ...]]:
    """Build a ScannerReport from a schema-valid findings document.

    Returns the error strings instead of raising, so one malformed stored file cannot
    abort the whole page. The report is constructed exactly like the CLI's
    `_report_from_json`, against the same schema.
    """
    try:
        text = path.read_text(encoding="utf-8")
        if len(text) > MAX_FINDINGS_BYTES:
            return None, (f"{path.name}: findings document too large to score",)
        data: Any = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, (f"{path}: unreadable findings file ({exc})",)
    problems = validate_json(data, "findings.schema.json", str(path))
    if problems:
        return None, tuple(f"{path.name}: {p!s}" for p in problems)
    report = ScannerReport(
        tool=data["tool"],
        version=data["version"],
        scope=frozenset(WeaknessClass(c) for c in data["scope"]),
        cases_run=frozenset(data["cases_run"]),
        configuration=data.get("configuration"),
        findings=tuple(
            Finding(
                case_id=f["case_id"],
                weakness_class=WeaknessClass(f["weakness_class"]),
                file=f["file"],
                line=f["line"],
                rule_id=f.get("rule_id"),
            )
            for f in data["findings"]
        ),
    )
    return report, ()


def score_findings(cases_dict: dict[str, Case], report: ScannerReport) -> ScoreResult:
    """Score a validated report of full cases using the harness scorer, region matching."""
    return score(list(cases_dict.values()), report, matching="region")
