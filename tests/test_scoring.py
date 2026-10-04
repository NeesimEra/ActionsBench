from __future__ import annotations

from pathlib import Path

import pytest

from actionsbench.models import (
    Case,
    ExpectedFinding,
    Finding,
    Provenance,
    ScannerReport,
    Status,
)
from actionsbench.scoring import ScoringInputError, score
from actionsbench.taxonomy import WeaknessClass

INJ = WeaknessClass.INJECTION
PIN = WeaknessClass.UNPINNED_DEPENDENCY
WF = ".github/workflows/wf.yml"


def make_case(case_id: str, *expected: ExpectedFinding, negative: bool = False) -> Case:
    return Case(
        id=case_id,
        root=Path("."),
        title="t",
        is_negative=negative,
        expected=tuple(expected),
        rationale="r" * 20,
        references=("https://example.com",),
        provenance=Provenance.SYNTHETIC_MINIMAL,
        status=Status.PROPOSED,
        author="a",
        reviewer=None,
        added_in="0.1.0",
    )


def exp(cls: WeaknessClass = INJ, line: int = 5, file: str = WF) -> ExpectedFinding:
    return ExpectedFinding(cls, file, line, "x")


def found(case_id: str, cls: WeaknessClass = INJ, line: int = 5, file: str = WF) -> Finding:
    return Finding(case_id, cls, file, line)


def report(
    findings: list[Finding],
    *,
    scope: set[WeaknessClass] | None = None,
    run: set[str] | None = None,
) -> ScannerReport:
    ids = run if run is not None else {f.case_id for f in findings}
    return ScannerReport(
        tool="t",
        version="1",
        scope=frozenset(scope if scope is not None else {INJ}),
        cases_run=frozenset(ids),
        findings=tuple(findings),
    )


def test_true_positive_and_perfect_scores() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    result = score(cases, report([found("AB-INJ-0001")], run={"AB-INJ-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (1, 0, 0)
    assert s.precision == 1.0
    assert s.recall == 1.0
    assert s.f1 == 1.0
    assert result.mismatches == []


def test_missed_finding_is_a_false_negative() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    result = score(cases, report([], run={"AB-INJ-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (0, 0, 1)
    assert s.recall == 0.0
    assert s.precision is None
    assert result.mismatches[0].missed


def test_finding_on_a_negative_case_is_a_false_positive() -> None:
    cases = [make_case("AB-NEG-0001", negative=True)]
    result = score(cases, report([found("AB-NEG-0001")], run={"AB-NEG-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (0, 1, 0)
    assert s.precision == 0.0
    assert s.recall is None


def test_clean_negative_scores_nothing() -> None:
    cases = [make_case("AB-NEG-0001", negative=True)]
    result = score(cases, report([], run={"AB-NEG-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (0, 0, 0)
    assert s.f1 is None
    assert result.cases_scored == 1


def test_wrong_line_does_not_match_at_zero_tolerance() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=5))]
    result = score(cases, report([found("AB-INJ-0001", line=6)], run={"AB-INJ-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (0, 1, 1)


def test_tolerance_allows_nearby_line() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=5))]
    result = score(
        cases, report([found("AB-INJ-0001", line=7)], run={"AB-INJ-0001"}), line_tolerance=2
    )
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (1, 0, 0)


def test_wrong_file_does_not_match() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    result = score(cases, report([found("AB-INJ-0001", file="other.yml")], run={"AB-INJ-0001"}))
    assert (result.per_class[INJ].tp, result.per_class[INJ].fp) == (0, 1)


def test_matching_is_one_to_one() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=5))]
    findings = [found("AB-INJ-0001", line=5), found("AB-INJ-0001", line=5)]
    result = score(cases, report(findings, run={"AB-INJ-0001"}))
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (1, 1, 0)


def test_closest_finding_wins_with_tolerance() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=10))]
    findings = [found("AB-INJ-0001", line=12), found("AB-INJ-0001", line=10)]
    result = score(cases, report(findings, run={"AB-INJ-0001"}), line_tolerance=2)
    s = result.per_class[INJ]
    assert (s.tp, s.fp) == (1, 1)


def test_expected_finding_outside_scope_is_uncovered_not_a_miss() -> None:
    cases = [make_case("AB-PIN-0001", exp(PIN))]
    result = score(cases, report([], scope={INJ}, run={"AB-PIN-0001"}))
    s = result.per_class[PIN]
    assert not s.in_scope
    assert (s.tp, s.fp, s.fn) == (0, 0, 0)
    assert s.uncovered == 1
    assert result.mismatches == []


def test_finding_outside_scope_is_not_a_false_positive() -> None:
    cases = [make_case("AB-NEG-0001", negative=True)]
    result = score(cases, report([found("AB-NEG-0001", PIN)], scope={INJ}, run={"AB-NEG-0001"}))
    s = result.per_class[PIN]
    assert s.fp == 0
    assert s.out_of_scope_findings == 1


def test_cases_not_run_are_excluded_not_counted_clean() -> None:
    cases = [make_case("AB-INJ-0001", exp()), make_case("AB-INJ-0002", exp())]
    result = score(cases, report([found("AB-INJ-0001")], run={"AB-INJ-0001"}))
    assert result.not_run == ["AB-INJ-0002"]
    assert result.cases_scored == 1
    assert result.per_class[INJ].fn == 0  # AB-INJ-0002 was never run, so it is not a miss


def test_findings_for_a_case_not_in_cases_run_are_rejected() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    with pytest.raises(ScoringInputError, match="not in cases_run"):
        score(cases, report([found("AB-INJ-0001")], run=set()))


def test_unknown_case_in_cases_run_is_rejected() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    with pytest.raises(ScoringInputError, match="unknown case ids"):
        score(cases, report([], run={"AB-INJ-9999"}))


def test_there_is_no_overall_score() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    result = score(cases, report([], run={"AB-INJ-0001"}))
    assert not hasattr(result, "overall")
    assert not hasattr(result, "f1")
