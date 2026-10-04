from __future__ import annotations

from pathlib import Path

import pytest

from actionsbench.adapters.base import ScannerNotFoundError, ScannerVersionError
from actionsbench.corpus import require_valid_corpus, validate_json
from actionsbench.models import Case
from actionsbench.runner import findings_document, materialize_case, run_scanner
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass
from tests import fakes
from tests.fakes import FakeAdapter


@pytest.fixture
def cases(real_corpus: Path) -> list[Case]:
    wanted = {"AB-INJ-0001", "AB-NEG-0001"}
    return [c for c in require_valid_corpus(real_corpus) if c.id in wanted]


@pytest.fixture
def one_case(cases: list[Case]) -> list[Case]:
    return [c for c in cases if c.id == "AB-INJ-0001"]


def test_materialize_copies_only_the_github_directory(cases: list[Case], tmp_path: Path) -> None:
    case = cases[0]
    scan_dir = materialize_case(case, tmp_path)
    assert (scan_dir / ".github").is_dir()
    assert not (scan_dir / "case.yaml").exists()
    assert sorted(p.name for p in scan_dir.iterdir()) == [".github"]


def test_materialize_keeps_nested_action_files(real_corpus: Path, tmp_path: Path) -> None:
    case = next(c for c in require_valid_corpus(real_corpus) if c.id == "AB-INJ-0007")
    scan_dir = materialize_case(case, tmp_path)
    assert (scan_dir / ".github" / "actions" / "greet" / "action.yml").is_file()


def test_runs_every_case_and_records_raw_output(cases: list[Case], tmp_path: Path) -> None:
    result = run_scanner(FakeAdapter(fakes.OK_EMPTY), cases, tmp_path)
    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "9.9"
    assert result.report.findings == ()
    assert sorted(p.name for p in (tmp_path / "fake-9.9" / "raw").iterdir()) == [
        "AB-INJ-0001.sarif",
        "AB-NEG-0001.sarif",
    ]


def test_isolation_probe_sees_no_label_and_no_corpus_path(
    cases: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.ISOLATION_PROBE), cases, tmp_path)
    assert result.failures == {}


def test_mapped_findings_are_kept_and_unmapped_rules_are_surfaced(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.FINDS), one_case, tmp_path)
    assert [(f.weakness_class, f.line) for f in result.report.findings] == [
        (WeaknessClass.INJECTION, 13)
    ]
    assert result.unmapped_rules == {"fake/other": ["AB-INJ-0001"]}


def test_nonzero_exit_excludes_the_case_instead_of_counting_it_clean(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.EXIT_2), one_case, tmp_path)
    assert result.report.cases_run == frozenset()
    assert result.failures["AB-INJ-0001"] == "exit code 2: boom"


def test_unparseable_output_excludes_the_case(one_case: list[Case], tmp_path: Path) -> None:
    result = run_scanner(FakeAdapter(fakes.GARBAGE), one_case, tmp_path)
    assert result.report.cases_run == frozenset()
    assert "unparseable output" in result.failures["AB-INJ-0001"]


def test_timeout_excludes_the_case(one_case: list[Case], tmp_path: Path) -> None:
    result = run_scanner(FakeAdapter(fakes.SLEEP), one_case, tmp_path, timeout=0.3)
    assert result.report.cases_run == frozenset()
    assert "timed out" in result.failures["AB-INJ-0001"]


def test_path_that_does_not_resolve_in_the_copy_fails_the_case(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.BAD_PATH), one_case, tmp_path)
    assert result.report.cases_run == frozenset()
    assert "does not resolve inside the isolated copy" in result.failures["AB-INJ-0001"]


def test_version_drift_from_the_pinned_version_fails_the_case(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.WRONG_VERSION), one_case, tmp_path)
    assert result.report.cases_run == frozenset()
    assert "pinned to 9.9" in result.failures["AB-INJ-0001"]


def test_missing_scanner_binary_is_an_error_not_a_clean_run(
    one_case: list[Case], tmp_path: Path
) -> None:
    adapter = FakeAdapter(fakes.OK_EMPTY, launcher="definitely-not-a-real-binary-xyz")
    with pytest.raises(ScannerNotFoundError):
        run_scanner(adapter, one_case, tmp_path)


def test_findings_document_matches_the_public_schema(one_case: list[Case], tmp_path: Path) -> None:
    result = run_scanner(FakeAdapter(fakes.FINDS), one_case, tmp_path)
    document = findings_document(result.report)
    assert validate_json(document, "findings.schema.json", "doc") == []
    assert document["scope"] == ["injection"]
    assert document["cases_run"] == ["AB-INJ-0001"]


def test_run_output_feeds_straight_into_scoring(
    real_corpus: Path, one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.FINDS), one_case, tmp_path)
    scored = score(require_valid_corpus(real_corpus), result.report)
    injection = scored.per_class[WeaknessClass.INJECTION]
    assert (injection.tp, injection.fp, injection.fn) == (1, 0, 0)
    assert scored.cases_scored == 1
    assert "AB-INJ-0002" in scored.not_run


def test_prepare_hook_runs_on_the_copy_before_the_scanner(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.NEEDS_MARKER, marker=".marker"), one_case, tmp_path)
    assert result.failures == {}
    # and it never touches the corpus itself
    assert not (one_case[0].root / ".marker").exists()


def test_scanner_without_the_prepare_marker_fails_the_case(
    one_case: list[Case], tmp_path: Path
) -> None:
    result = run_scanner(FakeAdapter(fakes.NEEDS_MARKER), one_case, tmp_path)
    assert result.report.cases_run == frozenset()
    assert "exit code 4" in result.failures["AB-INJ-0001"]


def test_probed_version_is_recorded_when_the_tool_does_not_report_one_in_its_output(
    one_case: list[Case], tmp_path: Path
) -> None:
    # SARIF with no tool version, like a scanner that only reports it via a separate command
    script = (
        "import json; print(json.dumps({'version': '2.1.0', "
        "'runs': [{'tool': {'driver': {'name': 'x'}}, 'results': []}]}))"
    )
    result = run_scanner(FakeAdapter(script, probed_version="9.9"), one_case, tmp_path)
    assert result.failures == {}
    assert result.report.version == "9.9"


def test_wrong_probed_version_stops_the_whole_run(one_case: list[Case], tmp_path: Path) -> None:
    with pytest.raises(ScannerVersionError, match=r"pinned to 9\.9"):
        run_scanner(FakeAdapter(fakes.OK_EMPTY, probed_version="1.0"), one_case, tmp_path)
