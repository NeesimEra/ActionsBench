from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from actionsbench.cli import main
from actionsbench.corpus import require_valid_corpus
from actionsbench.taxonomy import WeaknessClass
from tests.conftest import CaseWriter


def perfect_findings(corpus: Path) -> dict[str, Any]:
    """A scanner that reports exactly the labeled findings, for the injection class only."""
    cases = require_valid_corpus(corpus)
    return {
        "tool": "oracle",
        "version": "1.0",
        "scope": [WeaknessClass.INJECTION.value],
        "cases_run": [c.id for c in cases],
        "findings": [
            {
                "case_id": c.id,
                "weakness_class": e.weakness_class.value,
                "file": e.file,
                "line": e.line,
            }
            for c in cases
            for e in c.expected
        ],
    }


def test_validate_real_corpus(real_corpus: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--corpus", str(real_corpus)]) == 0
    assert "OK:" in capsys.readouterr().out


def test_validate_reports_problems_and_fails(
    make_case: CaseWriter, capsys: pytest.CaptureFixture[str]
) -> None:
    case_dir = make_case(expected=[])
    assert main(["validate", "--corpus", str(case_dir.parent)]) == 1
    assert "at least one expected finding" in capsys.readouterr().err


def test_stats(real_corpus: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats", "--corpus", str(real_corpus)]) == 0
    out = capsys.readouterr().out
    assert "injection" in out
    assert "(negative)" in out


def test_score_with_a_perfect_scanner(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(perfect_findings(real_corpus)), encoding="utf-8")
    assert main(["score", str(findings), "--corpus", str(real_corpus), "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    injection = next(c for c in result["classes"] if c["class"] == "injection")
    assert injection["precision"] == 1.0
    assert injection["recall"] == 1.0
    assert result["mismatches"] == []


def test_score_text_output_lists_every_class(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(perfect_findings(real_corpus)), encoding="utf-8")
    assert main(["score", str(findings), "--corpus", str(real_corpus)]) == 0
    out = capsys.readouterr().out
    for cls in WeaknessClass:
        assert cls.value in out


def test_score_rejects_a_file_that_violates_the_schema(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps({"tool": "x"}), encoding="utf-8")
    assert main(["score", str(findings), "--corpus", str(real_corpus)]) == 1
    assert "required property" in capsys.readouterr().err


def test_score_rejects_findings_for_a_case_that_was_not_run(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = perfect_findings(real_corpus)
    data["cases_run"] = []
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(data), encoding="utf-8")
    assert main(["score", str(findings), "--corpus", str(real_corpus)]) == 1
    assert "not in cases_run" in capsys.readouterr().err


def test_score_reports_missing_findings_file(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["score", str(tmp_path / "nope.json"), "--corpus", str(real_corpus)]) == 1
    assert "cannot read findings file" in capsys.readouterr().err
