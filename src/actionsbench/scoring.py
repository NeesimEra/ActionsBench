"""Score a scanner run against the labeled corpus.

Rules (see docs/methodology.md and docs/adr/0003-scanner-scope-and-scoring.md):

* Matching is one-to-one: one finding can satisfy at most one expected finding, so a
  scanner cannot inflate recall by reporting the same line twice.
* A finding matches an expected finding when class and file are equal and the lines are
  within `line_tolerance`. The default of 0 is a placeholder; the tolerance is a decision
  for the M0 spike.
* A tool is only judged on the classes it declares in `scope`. Expected findings outside
  scope count as `uncovered`; findings outside scope count as `out_of_scope_findings`.
  Neither is a false negative or a false positive.
* Cases the tool did not run on are excluded and listed in `not_run`.
* There is deliberately no overall score: results are per class so the output cannot be
  read as a leaderboard.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from actionsbench.models import Case, ExpectedFinding, Finding, ScannerReport
from actionsbench.taxonomy import WeaknessClass


class ScoringInputError(ValueError):
    """The scanner report is inconsistent with the corpus (unknown or un-run cases)."""


@dataclass(slots=True)
class ClassScore:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    uncovered: int = 0
    out_of_scope_findings: int = 0
    in_scope: bool = False

    @property
    def precision(self) -> float | None:
        denominator = self.tp + self.fp
        return self.tp / denominator if denominator else None

    @property
    def recall(self) -> float | None:
        denominator = self.tp + self.fn
        return self.tp / denominator if denominator else None

    @property
    def f1(self) -> float | None:
        precision, recall = self.precision, self.recall
        if precision is None or recall is None or precision + recall == 0:
            return None
        return 2 * precision * recall / (precision + recall)


@dataclass(frozen=True, slots=True)
class CaseMismatch:
    case_id: str
    missed: tuple[ExpectedFinding, ...]
    extra: tuple[Finding, ...]


@dataclass(slots=True)
class ScoreResult:
    tool: str
    version: str
    line_tolerance: int
    scope: frozenset[WeaknessClass]
    per_class: dict[WeaknessClass, ClassScore]
    mismatches: list[CaseMismatch] = field(default_factory=list)
    not_run: list[str] = field(default_factory=list)
    cases_scored: int = 0


def _match(
    expected: Sequence[ExpectedFinding], found: Sequence[Finding], tolerance: int
) -> tuple[int, list[ExpectedFinding], list[Finding]]:
    unmatched = list(found)
    missed: list[ExpectedFinding] = []
    matched = 0
    for exp in expected:
        best: Finding | None = None
        best_distance = tolerance + 1
        for candidate in unmatched:
            if candidate.file != exp.file:
                continue
            distance = abs(candidate.line - exp.line)
            if distance < best_distance:
                best, best_distance = candidate, distance
        if best is None:
            missed.append(exp)
        else:
            unmatched.remove(best)
            matched += 1
    return matched, missed, unmatched


def _check_inputs(cases_by_id: dict[str, Case], report: ScannerReport) -> None:
    unknown_run = sorted(report.cases_run - cases_by_id.keys())
    if unknown_run:
        raise ScoringInputError(f"cases_run lists unknown case ids: {', '.join(unknown_run)}")
    stray = sorted({f.case_id for f in report.findings} - report.cases_run)
    if stray:
        raise ScoringInputError(
            "findings reference cases that are not in cases_run (a tool cannot report on a case "
            f"it did not run): {', '.join(stray)}"
        )


def score(cases: Sequence[Case], report: ScannerReport, *, line_tolerance: int = 0) -> ScoreResult:
    cases_by_id = {case.id: case for case in cases}
    _check_inputs(cases_by_id, report)

    result = ScoreResult(
        tool=report.tool,
        version=report.version,
        line_tolerance=line_tolerance,
        scope=report.scope,
        per_class={cls: ClassScore(in_scope=cls in report.scope) for cls in WeaknessClass},
    )

    for case in sorted(cases, key=lambda c: c.id):
        if case.id not in report.cases_run:
            result.not_run.append(case.id)
            continue
        result.cases_scored += 1
        case_findings = [f for f in report.findings if f.case_id == case.id]
        missed_all: list[ExpectedFinding] = []
        extra_all: list[Finding] = []

        for cls in WeaknessClass:
            expected = [e for e in case.expected if e.weakness_class == cls]
            found = [f for f in case_findings if f.weakness_class == cls]
            counts = result.per_class[cls]
            matched, missed, extra = _match(expected, found, line_tolerance)
            if counts.in_scope:
                counts.tp += matched
                counts.fn += len(missed)
                counts.fp += len(extra)
                missed_all.extend(missed)
                extra_all.extend(extra)
            else:
                counts.uncovered += len(expected)
                counts.out_of_scope_findings += len(found)

        if missed_all or extra_all:
            result.mismatches.append(CaseMismatch(case.id, tuple(missed_all), tuple(extra_all)))
    return result
