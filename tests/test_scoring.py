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
from actionsbench.report import to_json, to_text
from actionsbench.scoring import ScoreResult, ScoringInputError, score
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


def test_wrong_line_does_not_match_in_line_mode_at_zero_tolerance() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=5))]
    result = score(
        cases, report([found("AB-INJ-0001", line=6)], run={"AB-INJ-0001"}), matching="line"
    )
    s = result.per_class[INJ]
    assert (s.tp, s.fp, s.fn) == (0, 1, 1)


def test_tolerance_allows_nearby_line() -> None:
    cases = [make_case("AB-INJ-0001", exp(line=5))]
    result = score(
        cases,
        report([found("AB-INJ-0001", line=7)], run={"AB-INJ-0001"}),
        matching="line",
        line_tolerance=2,
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
    result = score(cases, report(findings, run={"AB-INJ-0001"}), matching="line", line_tolerance=2)
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


# ---- region matching (the default)

WORKFLOW = """\
name: Example
on:
  pull_request:
  push:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v4
      - name: Upload
        uses: actions/upload-artifact@v4
  deploy:
    uses: example/repo/.github/workflows/x.yml@v1
    secrets: inherit
"""
FILE = ".github/workflows/wf.yml"


def line_of(fragment: str, text: str = WORKFLOW) -> int:
    """1-based line number of the first line containing `fragment` (never a hand-counted number)."""
    for number, line in enumerate(text.splitlines(), start=1):
        if fragment in line:
            return number
    raise AssertionError(f"{fragment!r} not found")


def _rebuild(base: Case, root: Path) -> Case:
    return Case(
        id=base.id,
        root=root,
        title=base.title,
        is_negative=base.is_negative,
        expected=base.expected,
        rationale=base.rationale,
        references=base.references,
        provenance=base.provenance,
        status=base.status,
        author=base.author,
        reviewer=base.reviewer,
        added_in=base.added_in,
    )


def case_on_disk(tmp_path: Path, text: str, *expected: ExpectedFinding) -> Case:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / FILE).write_text(text, encoding="utf-8")
    return _rebuild(make_case("AB-PIN-0001", *expected), tmp_path)


def region_score(
    tmp_path: Path,
    label_line: int,
    finding_lines: list[int],
    *,
    matching: str = "region",
    line_tolerance: int = 0,
) -> ScoreResult:
    case = case_on_disk(tmp_path, WORKFLOW, exp(PIN, label_line))
    findings = [found("AB-PIN-0001", PIN, line) for line in finding_lines]
    return score(
        [case],
        report(findings, scope={PIN}, run={"AB-PIN-0001"}),
        matching=matching,
        line_tolerance=line_tolerance,
    )


CHECKOUT_USES = line_of("uses: actions/checkout@v4")
CHECKOUT_HEADER = line_of("- name: Check out")
UPLOAD_HEADER = line_of("- name: Upload")


def test_a_step_header_matches_a_label_on_a_line_inside_the_step(tmp_path: Path) -> None:
    cell = region_score(tmp_path, CHECKOUT_USES, [CHECKOUT_HEADER]).per_class[PIN]
    assert (cell.tp, cell.fp, cell.fn) == (1, 0, 0)


def test_the_same_offset_is_a_miss_and_a_false_alarm_in_strict_line_mode(tmp_path: Path) -> None:
    result = region_score(tmp_path, CHECKOUT_USES, [CHECKOUT_HEADER], matching="line")
    cell = result.per_class[PIN]
    assert (cell.tp, cell.fp, cell.fn) == (0, 1, 1)


def test_a_finding_in_the_next_step_does_not_match(tmp_path: Path) -> None:
    cell = region_score(tmp_path, CHECKOUT_USES, [UPLOAD_HEADER]).per_class[PIN]
    assert (cell.tp, cell.fp, cell.fn) == (0, 1, 1)


def test_the_on_line_matches_the_trigger_but_the_permissions_block_does_not(
    tmp_path: Path,
) -> None:
    trigger = line_of("pull_request:")
    assert region_score(tmp_path / "a", trigger, [line_of("on:")]).per_class[PIN].tp == 1
    assert region_score(tmp_path / "b", trigger, [line_of("contents: read")]).per_class[PIN].tp == 0


def test_job_keys_outside_steps_are_one_region(tmp_path: Path) -> None:
    # a reusable-workflow call: the label is `secrets: inherit`, the tool reports its `uses:` line
    label = line_of("secrets: inherit")
    tool = line_of("uses: example/repo")
    assert region_score(tmp_path, label, [tool]).per_class[PIN].tp == 1


def test_region_matching_is_still_one_to_one(tmp_path: Path) -> None:
    cell = region_score(tmp_path, CHECKOUT_USES, [CHECKOUT_HEADER, CHECKOUT_USES]).per_class[PIN]
    assert (cell.tp, cell.fp, cell.fn) == (1, 1, 0)


def test_the_closest_finding_in_the_region_is_the_one_that_matches(tmp_path: Path) -> None:
    result = region_score(tmp_path, CHECKOUT_USES, [CHECKOUT_HEADER, CHECKOUT_USES])
    assert [f.line for m in result.mismatches for f in m.extra] == [CHECKOUT_HEADER]


def test_unparseable_files_fall_back_to_exact_line(tmp_path: Path) -> None:
    broken = "name: x\non: [unclosed\njobs:\n  a: 1\n"
    case = case_on_disk(tmp_path, broken, exp(PIN, 3))
    near = score([case], report([found("AB-PIN-0001", PIN, 4)], scope={PIN}, run={"AB-PIN-0001"}))
    assert near.per_class[PIN].tp == 0  # one line off is not a match without a parse
    exact = score([case], report([found("AB-PIN-0001", PIN, 3)], scope={PIN}, run={"AB-PIN-0001"}))
    assert exact.per_class[PIN].tp == 1


def test_a_missing_file_falls_back_to_exact_line() -> None:
    cases = [make_case("AB-PIN-0001", exp(PIN, 5))]  # root "." has no such file
    near = score(cases, report([found("AB-PIN-0001", PIN, 6)], scope={PIN}, run={"AB-PIN-0001"}))
    assert near.per_class[PIN].tp == 0


def test_a_finding_in_another_file_never_matches(tmp_path: Path) -> None:
    case = case_on_disk(tmp_path, WORKFLOW, exp(PIN, CHECKOUT_USES))
    other = found("AB-PIN-0001", PIN, CHECKOUT_USES, file="other.yml")
    assert score([case], report([other], scope={PIN}, run={"AB-PIN-0001"})).per_class[PIN].tp == 0


def test_a_tolerance_is_rejected_in_region_mode_and_unknown_modes_are_rejected() -> None:
    cases = [make_case("AB-INJ-0001", exp())]
    with pytest.raises(ScoringInputError, match="only applies to matching='line'"):
        score(cases, report([], run={"AB-INJ-0001"}), line_tolerance=1)
    with pytest.raises(ScoringInputError, match="unknown matching rule"):
        score(cases, report([], run={"AB-INJ-0001"}), matching="fuzzy")


def test_the_matching_rule_is_part_of_the_result(tmp_path: Path) -> None:
    default = region_score(tmp_path / "a", CHECKOUT_USES, [CHECKOUT_USES])
    assert default.matching == "region"
    assert to_json(default)["matching"] == "region"
    assert to_json(default)["line_tolerance"] is None
    assert "matching: region" in to_text(default)

    strict = region_score(
        tmp_path / "b", CHECKOUT_USES, [CHECKOUT_USES], matching="line", line_tolerance=2
    )
    assert to_json(strict)["matching"] == "line"
    assert to_json(strict)["line_tolerance"] == 2
    assert "matching: line (tolerance 2)" in to_text(strict)
