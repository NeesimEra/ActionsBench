"""P0 platform API tests: the JSON contract, safe file serving, and the ADR 0007 guardrails.

Everything rendered by the web UI comes from these endpoints, so the tests pin the JSON
shapes, the 404-on-unknown-resource rule, and the provenance wording the UI must show.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import Any

import actionsbench
import pytest
from actionsbench.corpus import validate_json
from actionsbench.models import Case, Provenance, ScannerReport, Status
from actionsbench.taxonomy import WeaknessClass
from fastapi.testclient import TestClient

from actionsbench_platform.app import create_app, label_status, rows
from actionsbench_platform.data import PlatformData, read_findings, score_findings

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "corpus" / "cases"


@cache
def platform_data() -> PlatformData:
    return PlatformData.load(CORPUS)


def client(data: PlatformData | None = None, results: Path | None = None) -> TestClient:
    return TestClient(create_app(data if data is not None else platform_data(), results))


def client_json(path: str, results: Path | None = None) -> Any:
    response = client(results=results).get(path)
    assert response.status_code == 200, f"{path}: {response.status_code} {response.text}"
    assert response.headers["content-type"].startswith("application/json")
    return response.json()


def findings_document(
    cases: dict[str, Case],
    scope: list[str],
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A minimal, schema-valid findings document the platform can score."""
    return {
        "tool": "zizmor",
        "version": "1.30.1",
        "scope": scope,
        "cases_run": sorted(cases),
        "findings": findings if findings is not None else [],
    }


def labeled_values(data: PlatformData) -> set[str]:
    """Class values the corpus actually labels, positive or negative."""
    return {e.weakness_class.value for case in data.cases.values() for e in case.expected}


def test_summary_lists_every_labeled_class_with_derived_counts() -> None:
    data = platform_data()
    summary = client_json("/api/summary")
    assert summary["case_count"] == len(data.cases)
    values = {row["value"] for row in summary["class_rows"]}
    assert values == labeled_values(data), (values, labeled_values(data))
    for row in summary["class_rows"]:
        positives = sum(
            1
            for case in data.cases.values()
            if not case.is_negative and row["value"] in data.classes_of(case)
        )
        negatives = sum(
            1
            for case in data.cases.values()
            if case.is_negative and row["value"] in data.classes_of(case)
        )
        assert row["positives"] == positives
        assert row["negatives"] == negatives


def test_summary_statement_says_the_labels_are_ai_reviewed() -> None:
    sentence = client_json("/api/summary")["provenance"]
    assert "ai-reviewed" in sentence
    assert "no label has independent human agreement" in sentence


def test_case_list_covers_the_whole_corpus_with_the_pinned_fields() -> None:
    data = platform_data()
    cases = client_json("/api/cases")["cases"]
    assert len(cases) == len(data.cases)
    for entry in cases:
        case = data.cases[entry["id"]]
        assert entry["title"] == case.title
        assert entry["is_negative"] == case.is_negative
        assert entry["classes"] == data.classes_of(case)
        assert entry["status"] == case.status.value
        assert entry["added_in"] == case.added_in


def test_case_detail_serves_the_full_detail_contract() -> None:
    data = platform_data()
    case = data.case("AB-INJ-0001")
    assert case is not None
    detail = client_json(f"/api/cases/{case.id}")
    assert detail["title"] == case.title
    assert detail["status"] == "ai-reviewed"
    assert detail["provenance"] == "synthetic-minimal"
    assert detail["expected"] == [
        {
            "weakness_class": e.weakness_class.value,
            "file": e.file,
            "line": e.line,
            "evidence": e.evidence,
        }
        for e in case.expected
    ]
    assert detail["files"] == [p.relative_to(case.root).as_posix() for p in data.case_files(case)]
    assert detail["author"] == case.author
    assert detail["added_in"] == case.added_in
    assert detail["rationale"] == case.rationale
    assert detail["references"] == list(case.references)


def test_case_detail_links_the_record_file_behind_the_stored_anchor() -> None:
    """`review_record` can carry a `#section` anchor; the link keeps it and the existence
    check strips it off."""
    data = platform_data()
    case = data.case("AB-INJ-0001")
    assert case is not None
    record = case.review_record
    assert record is not None
    assert record.startswith("docs/")
    assert "#" in record
    link = client_json(f"/api/cases/{case.id}")["review_record_link"]
    assert link is not None
    served_path = link.removeprefix("records/").partition("#")[0]
    assert (data.repo_docs / served_path).is_file()
    assert link == f"records/{record.removeprefix('docs/')}"


def test_case_file_view_serves_the_exact_file_text_as_plain_text() -> None:
    data = platform_data()
    case = data.case("AB-INJ-0001")
    assert case is not None
    files = [p.relative_to(case.root).as_posix() for p in data.case_files(case)]
    assert files
    relative = files[0]
    response = client().get(f"/api/cases/{case.id}/files/{relative}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    # One clean comparison: what the API serves is exactly the file's text.
    assert response.text == (case.root / relative).read_text(encoding="utf-8")


def test_case_file_view_refuses_to_escape_the_case() -> None:
    assert client().get("/api/cases/AB-INJ-0001/files/../../../pyproject.toml").status_code == 404


@pytest.mark.parametrize(
    ("escape", "description"),
    [
        ("/files/%2e%2e%2f%2e%2e%2fpyproject.toml", "dot-segment percent-encoding"),
        ("/files/..%2F..%2Fpyproject.toml", "slash percent-encoding"),
        ("/files/..\\..\\pyproject.toml", "backslash separators"),
    ],
)
def test_case_file_view_refuses_every_traversal_spelling(escape: str, description: str) -> None:
    """Different spellings of the same escape must not slip past the resolve() guard."""
    assert client().get(f"/api/cases/AB-INJ-0001{escape}").status_code == 404, description


def test_case_file_view_refuses_the_case_metadata_file() -> None:
    """case.yaml is rendered structurally on the case page, so both the listing and the
    endpoint hide it (the two must agree)."""
    assert client().get("/api/cases/AB-INJ-0001/files/case.yaml").status_code == 404


def test_case_file_view_refuses_oversized_files(tmp_path: Path) -> None:
    """Nothing larger than the byte cap is ever read into memory. The corpus fixtures are
    all small, so this drives file_text directly with a synthetic case in a tmp root."""
    from actionsbench_platform.data import MAX_FILE_BYTES, ReloadError

    (tmp_path / "big.yml").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    synthetic = replace(scaffold_case("AB-TST-0009", Status.AI_REVIEWED), root=tmp_path)
    with pytest.raises(ReloadError) as refusal:
        platform_data().file_text(synthetic, "big.yml")
    assert "too large" in str(refusal.value)


def test_results_survives_an_invalid_utf8_document(tmp_path: Path) -> None:
    """The UTF-8 refusal must be a problem line on a 200 page, never a 500, and valid
    documents next to it must still be scored."""
    (tmp_path / "garbled").mkdir()
    (tmp_path / "garbled" / "findings.json").write_bytes(b'{"tool": "x\xff"}')
    valid = findings_document(platform_data().cases, ["injection"])
    (tmp_path / "valid").mkdir()
    (tmp_path / "valid" / "findings.json").write_text(json.dumps(valid), encoding="utf-8")
    payload = client_json("/api/results", results=tmp_path)
    assert len(payload["entries"]) == 1
    assert [entry["tool"] for entry in payload["entries"]] == ["zizmor"]
    assert any("findings.json" in problem for problem in payload["problems"])


def test_records_route_refuses_symlink_escapes(tmp_path: Path) -> None:
    """A symlink planted under the docs directory must not follow out of it."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / "escape.md").symlink_to("/etc/hosts")
    data = PlatformData(cases={}, corpus_cases_dir=tmp_path / "corpus" / "cases")
    response = TestClient(create_app(data)).get("/api/records/escape.md")
    assert response.status_code == 404


def test_case_file_view_refuses_unknown_files() -> None:
    response = client().get("/api/cases/AB-INJ-0001/files/.github/workflows/no-such-file.yml")
    assert response.status_code == 404


def test_records_route_serves_only_document_files_under_repo_docs() -> None:
    """`review_record` URIs end at this route, so it must refuse everything else."""
    data = platform_data()
    case = data.case("AB-INJ-0001")
    assert case is not None
    assert case.review_record is not None
    served_path = case.review_record.removeprefix("docs/").partition("#")[0]
    response = client().get(f"/api/records/{served_path}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "ai-reviewed" in response.text
    # Traversal out of the docs directory and simply missing files both 404.
    assert client().get("/api/records/../../pyproject.toml").status_code == 404
    assert client().get("/api/records/no-such-record.md").status_code == 404


def test_unknown_case_id_is_404() -> None:
    response = client().get("/api/cases/AB-XXX-9999")
    assert response.status_code == 404


def test_unknown_weakness_class_is_404_not_422() -> None:
    """A class value the taxonomy does not know is an unknown resource, not a request
    validation failure: unknown resources answer 404."""
    response = client().get("/api/classes/definitely-not-a-class")
    assert response.status_code == 404, response.text


def test_class_without_cases_is_404() -> None:
    """Same rule for a known class the corpus simply never labels."""
    data = platform_data()
    unlabeled = [cls for cls in WeaknessClass if cls.value not in labeled_values(data)]
    assert unlabeled, "corpus changed: some taxonomized class must still lack cases"
    response = client().get(f"/api/classes/{unlabeled[0].value}")
    assert response.status_code == 404


def test_class_page_lists_its_cases() -> None:
    payload = client_json("/api/classes/injection")
    assert payload["value"] == "injection"
    assert payload["cases"], "the corpus labels injection cases"
    for entry in payload["cases"]:
        assert set(entry) == {"id", "title", "is_negative", "status"}


def test_results_empty_state_when_the_results_directory_is_missing(tmp_path: Path) -> None:
    payload = client_json("/api/results", results=tmp_path / "absent")
    assert payload["entries"] == []
    assert any("No results directory" in problem for problem in payload["problems"])


def test_results_scores_a_valid_document_per_class(tmp_path: Path) -> None:
    data = platform_data()
    document = findings_document(data.cases, ["injection"])
    (tmp_path / "zizmor").mkdir()
    (tmp_path / "zizmor" / "findings.json").write_text(json.dumps(document), encoding="utf-8")
    payload = client_json("/api/results", results=tmp_path)

    assert payload["entries"], payload["problems"]
    entry = payload["entries"][0]
    assert entry["tool"] == "zizmor"
    assert entry["version"] == "1.30.1"
    assert entry["scope"] == "injection"
    assert entry["configuration"] == "(not recorded)"
    assert entry["case_count"] == len(data.cases)
    assert entry["cases_scored"] == len(document["cases_run"])
    assert entry["not_run"] == sorted(set(data.cases) - set(document["cases_run"]))

    # The rendered rows equal the harness's own score() output for the same document...
    report = ScannerReport(
        tool="zizmor",
        version="1.30.1",
        scope=frozenset({WeaknessClass.INJECTION}),
        cases_run=frozenset(data.cases),
        findings=(),
    )
    scored = score_findings(data.cases, report)
    assert entry["rows"] == rows(scored)
    # Every taxonomized class gets a row; exactly one is in scope here.
    assert len(entry["rows"]) == len(list(WeaknessClass))
    assert next(row for row in entry["rows"] if row["in_scope"])["cls"] == "injection"
    # ...and the injection row also checks out by hand, without re-implementing scoring:
    # a findings-less run reports nothing, so the class has as many false negatives as the
    # positives the corpus labels, which is exactly the fn the harness counted.
    hand_counted = sum(
        1
        for case in data.cases.values()
        if not case.is_negative and "injection" in data.classes_of(case)
    )
    injection_row = next(row for row in entry["rows"] if row["in_scope"])
    assert injection_row["tp"] == 0
    assert injection_row["fp"] == 0
    assert injection_row["fn"] == hand_counted == scored.per_class[WeaknessClass.INJECTION].fn
    assert injection_row["uncovered"] == 0
    assert injection_row["precision"] == "—"
    assert injection_row["recall"] == "0%"
    assert injection_row["f1"] == "0%"
    # Out-of-scope rows are present but marked as such: a document that never declares a
    # class leaves its positives uncovered, stated rather than silently dropped.
    out_of_scope_rows = [row for row in entry["rows"] if not row["in_scope"]]
    assert len(out_of_scope_rows) == len(list(WeaknessClass)) - 1
    assert all(row["out_of_scope_findings"] == 0 for row in out_of_scope_rows)
    assert any(row["uncovered"] > 0 for row in out_of_scope_rows)
    # ADR 0003: the result states the rule that produced it.
    assert entry["matching"] == "region"
    # ADR 0007 reproducibility guardrail: corpus and harness versions travel with scores.
    assert payload["harness_version"] == actionsbench.__version__
    changelog = (CORPUS.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.search(r"^## (\S+)", changelog, flags=re.MULTILINE)
    assert heading is not None
    assert payload["corpus_version"] == heading.group(1)


def test_results_ignores_but_reports_invalid_documents(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "findings.json").write_text(json.dumps({"tool": "nope"}), encoding="utf-8")
    payload = client_json("/api/results", results=tmp_path)
    assert payload["entries"] == []
    assert any("findings.json" in problem for problem in payload["problems"]), payload
    assert payload["provenance"].startswith("Every label was reviewed")


def test_results_survives_a_document_the_corpus_cannot_score(tmp_path: Path) -> None:
    """Schema-valid is not the same as scoreable: a doc naming unknown case ids must be
    reported as a problem instead of raising a 500."""
    (tmp_path / "unknown-ids").mkdir()
    unscoreable = findings_document(
        {"AB-XXX-9999": scaffold_case("AB-XXX-9999", Status.PROPOSED)}, ["injection"]
    )
    (tmp_path / "unknown-ids" / "findings.json").write_text(
        json.dumps(unscoreable), encoding="utf-8"
    )
    payload = client_json("/api/results", results=tmp_path)
    assert payload["entries"] == []
    assert any("AB-XXX-9999" in problem for problem in payload["problems"]), payload
    # A valid document next to it is still scored.
    valid = findings_document(platform_data().cases, ["injection"])
    (tmp_path / "valid").mkdir()
    (tmp_path / "valid" / "findings.json").write_text(json.dumps(valid), encoding="utf-8")
    payload = client_json("/api/results", results=tmp_path)
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["tool"] == "zizmor"


def test_findings_readback_and_rows_use_the_harness_shapes(tmp_path: Path) -> None:
    """The read/score path is exercised with no leakage into the process CWD."""
    document = findings_document(platform_data().cases, ["injection", "secrets-exposure"])
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    loaded, problems = read_findings(path)
    assert loaded is not None
    assert not problems
    grid = rows(score_findings(platform_data().cases, loaded))
    assert {row["cls"] for row in grid if row["in_scope"]} == {
        "injection",
        "secrets-exposure",
    }
    for row in grid:
        assert set(row) == {
            "cls",
            "in_scope",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
            "uncovered",
            "out_of_scope_findings",
        }
        assert isinstance(row["tp"], int)
        assert isinstance(row["precision"], str)
        assert isinstance(row["in_scope"], bool)
    # Rows are sorted by class value.
    assert [row["cls"] for row in grid] == sorted(row["cls"] for row in grid)


def test_schema_contract_a_minimal_document_is_what_we_send() -> None:
    """Pin the findings schema contract the results endpoint depends on (draft 2020-12)."""
    document = findings_document(
        platform_data().cases,
        ["injection"],
        [
            {
                "case_id": "AB-INJ-0001",
                "weakness_class": "injection",
                "file": ".github/workflows/f.yml",
                "line": 1,
                "rule_id": "R1",
            }
        ],
    )
    assert validate_json(document, "findings.schema.json", "test") == []
    assert validate_json({"tool": "x", "version": "1"}, "findings.schema.json", "test") != []
    assert (
        validate_json(
            findings_document(platform_data().cases, ["not-a-class"]),
            "findings.schema.json",
            "test",
        )
        != []
    )
    extra: dict[str, Any] = findings_document(platform_data().cases, ["injection"])
    extra["surprise"] = True
    assert validate_json(extra, "findings.schema.json", "test") != []
    bad_finding = findings_document(
        platform_data().cases, ["injection"], [{"case_id": "AB-INJ-0001"}]
    )
    assert validate_json(bad_finding, "findings.schema.json", "test") != []


def test_label_status_keeps_the_guardrail_wording_and_reserves_agreed() -> None:
    sentence = label_status(platform_data())
    assert "ai-reviewed" in sentence
    assert "no label has independent human agreement" in sentence
    assert "agreed" not in sentence.replace("agreement", "")

    # Once a human has agreed, the sentence names the statuses instead of claiming otherwise.
    agreed = scaffold_case("AB-TST-0001", Status.AGREED)
    reviewed = scaffold_case("AB-TST-0002", Status.AI_REVIEWED)
    mixed = PlatformData(cases={c.id: c for c in (agreed, reviewed)}, corpus_cases_dir=CORPUS)
    assert label_status(mixed) == "Label statuses on this corpus: agreed, ai-reviewed."


def test_platform_package_never_executes_anything() -> None:
    """Guardrail, readable in one place: nothing in the package (nor any other test
    module) spawns, evaluates or pickles code. Ordered against ADR 0007: corpus content
    is data. This file itself is excluded — it must name the tokens it hunts for."""
    api_dir = Path(__file__).resolve().parents[1]
    sources = sorted((api_dir / "src" / "actionsbench_platform").rglob("*.py"))
    sources += [src for src in sorted((api_dir / "tests").glob("*.py")) if src != Path(__file__)]
    assert len(sources) >= 3, "scanned fewer files than the package has"
    forbidden = (
        "import subprocess",
        "from subprocess",
        "os.system",
        "popen",
        "eval(",
        "exec(",
        "__import__",
        "pickle",
    )
    for source in sources:
        text = source.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in text, f"{source.name} contains {pattern!r}"


def test_results_report_out_of_scope_findings_instead_of_dropping_them(tmp_path: Path) -> None:
    """Methodology §5 / ADR 0003: findings outside a declared scope are counted and
    reported, never silently dropped. A document that only scopes injection but reports a
    secrets-exposure finding on a run case must keep that count visible."""
    data = platform_data()
    case = data.case("AB-INJ-0001")
    assert case is not None
    target = case.expected[0]
    finding = {
        "case_id": case.id,
        "weakness_class": "secrets-exposure",  # real class, but outside the scope below
        "file": target.file,
        "line": target.line,
    }
    document = findings_document(data.cases, ["injection"], [finding])
    (tmp_path / "overscoped").mkdir()
    (tmp_path / "overscoped" / "findings.json").write_text(json.dumps(document), encoding="utf-8")
    payload = client_json("/api/results", results=tmp_path)
    entry = payload["entries"][0]
    row = next(row for row in entry["rows"] if row["cls"] == "secrets-exposure")
    assert row["in_scope"] is False
    assert row["out_of_scope_findings"] == 1


def scaffold_case(case_id: str, status: Status) -> Case:
    """A minimal synthetic Case, for tests that need a snapshot they control."""
    return Case(
        id=case_id,
        root=CORPUS / "AB-INJ-0001",
        title="test scaffold",
        is_negative=False,
        expected=(),
        rationale="not exercised by these tests",
        references=(),
        provenance=Provenance.SYNTHETIC_MINIMAL,
        status=status,
        author="test",
        reviewer=None,
        added_in="0.1.0",
    )
