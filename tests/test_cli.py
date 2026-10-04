from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from actionsbench.cli import main
from actionsbench.corpus import require_valid_corpus
from actionsbench.taxonomy import WeaknessClass
from tests import fakes
from tests.conftest import CaseWriter
from tests.fakes import FakeAdapter


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


def _use_adapter(monkeypatch: pytest.MonkeyPatch, adapter: FakeAdapter) -> None:
    monkeypatch.setattr("actionsbench.cli.get_adapter", lambda name, options=None: adapter)


def test_run_writes_a_findings_file_that_scores(
    real_corpus: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, FakeAdapter(fakes.FINDS))
    out = tmp_path / "results"
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(out)]
    assert main([*args, "--cases", "AB-INJ-0001"]) == 0
    printed = capsys.readouterr().out
    assert "ran 1 of 1 case(s)" in printed
    assert "fake/other: 1 case(s)" in printed  # the unmapped rule is surfaced

    findings = out / "fake-9.9" / "findings.json"
    assert main(["score", str(findings), "--corpus", str(real_corpus), "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    injection = next(c for c in result["classes"] if c["class"] == "injection")
    assert (injection["tp"], injection["fp"], injection["fn"]) == (1, 0, 0)


def test_run_fails_loudly_when_a_case_does_not_run(
    real_corpus: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, FakeAdapter(fakes.EXIT_2))
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    assert main([*args, "--cases", "AB-INJ-0001"]) == 1
    err = capsys.readouterr().err
    assert "FAILED AB-INJ-0001: exit code 2: boom" in err
    assert "excluded from scoring" in err


def test_run_rejects_unknown_case_ids(real_corpus: Path, tmp_path: Path) -> None:
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    assert main([*args, "--cases", "AB-INJ-9999"]) == 1


def test_run_reports_a_missing_scanner_binary(
    real_corpus: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, FakeAdapter(fakes.OK_EMPTY, launcher="no-such-binary-xyz"))
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    assert main([*args, "--cases", "AB-INJ-0001"]) == 1
    assert "cannot start" in capsys.readouterr().err


def test_configuration_is_shown_by_run_and_by_score(
    real_corpus: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, FakeAdapter(fakes.FINDS, configuration="persona=regular"))
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    assert main([*args, "--cases", "AB-INJ-0001"]) == 0
    assert "configuration: persona=regular" in capsys.readouterr().out

    findings = tmp_path / "fake-9.9" / "findings.json"
    assert main(["score", str(findings), "--corpus", str(real_corpus)]) == 0
    assert "configuration: persona=regular" in capsys.readouterr().out
    assert main(["score", str(findings), "--corpus", str(real_corpus), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["configuration"] == "persona=regular"


def test_score_says_when_no_configuration_was_recorded(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(perfect_findings(real_corpus)), encoding="utf-8")
    assert main(["score", str(findings), "--corpus", str(real_corpus)]) == 0
    assert "configuration: not recorded" in capsys.readouterr().out


def test_run_passes_config_options_to_the_adapter(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    # An invalid persona is rejected before anything runs.
    assert main([*args, "--config", "persona=paranoid"]) == 1
    assert "unknown zizmor persona" in capsys.readouterr().err
    assert main([*args, "--config", "colour=red"]) == 1
    assert "unknown option" in capsys.readouterr().err


@pytest.mark.parametrize("bad", ["persona", "=regular", "persona="])
def test_run_rejects_malformed_config(
    bad: str, real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["run", "--tool", "zizmor", "--corpus", str(real_corpus), "--out", str(tmp_path)]
    assert main([*args, "--config", bad]) == 1
    assert "KEY=VALUE" in capsys.readouterr().err


OFFSET_FINDINGS = {
    # the four anchoring differences observed from real zizmor 1.30.1 and actionlint 1.7.12:
    # (case, file, line the tool reports); each label is on a different line of the same construct
    "AB-TRG-0001": ("privileged-trigger", ".github/workflows/pwn-request.yml", 2),
    "AB-SEC-0001": ("secrets-exposure", ".github/workflows/inherit.yml", 10),
    "AB-ART-0001": ("artifact-integrity", ".github/workflows/artipacked.yml", 12),
    "AB-INJ-0006": ("injection", ".github/workflows/github-script.yml", 15),
}


def _offset_findings_file(tmp_path: Path) -> Path:
    data = {
        "tool": "offset-tool",
        "version": "1.0",
        "scope": sorted(cls for cls, _, _ in OFFSET_FINDINGS.values()),
        "cases_run": sorted(OFFSET_FINDINGS),
        "findings": [
            {"case_id": cid, "weakness_class": cls, "file": file, "line": line}
            for cid, (cls, file, line) in OFFSET_FINDINGS.items()
        ],
    }
    path = tmp_path / "offsets.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _cells(output: str) -> dict[str, tuple[int, int, int]]:
    return {
        c["class"]: (c["tp"], c["fp"], c["fn"])
        for c in json.loads(output)["classes"]
        if c["class"] in {cls for cls, _, _ in OFFSET_FINDINGS.values()}
    }


def test_score_matches_the_same_step_by_default(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _offset_findings_file(tmp_path)
    assert main(["score", str(path), "--corpus", str(real_corpus), "--format", "json"]) == 0
    cells = _cells(capsys.readouterr().out)
    assert set(cells.values()) == {(1, 0, 0)}
    assert len(cells) == 4


def test_score_reports_the_matching_rule(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _offset_findings_file(tmp_path)
    assert main(["score", str(path), "--corpus", str(real_corpus)]) == 0
    assert "matching: region" in capsys.readouterr().out


def test_strict_line_matching_charges_each_offset_as_a_miss_and_a_false_alarm(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _offset_findings_file(tmp_path)
    args = ["score", str(path), "--corpus", str(real_corpus), "--format", "json"]
    assert main([*args, "--match", "line"]) == 0
    assert set(_cells(capsys.readouterr().out).values()) == {(0, 1, 1)}


def test_a_one_line_tolerance_in_line_mode_matches_them_again(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _offset_findings_file(tmp_path)
    args = ["score", str(path), "--corpus", str(real_corpus), "--format", "json"]
    assert main([*args, "--match", "line", "--tolerance", "1"]) == 0
    assert set(_cells(capsys.readouterr().out).values()) == {(1, 0, 0)}


def test_tolerance_without_line_matching_is_an_error(
    real_corpus: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _offset_findings_file(tmp_path)
    assert main(["score", str(path), "--corpus", str(real_corpus), "--tolerance", "1"]) == 1
    assert "--tolerance only applies with --match line" in capsys.readouterr().err
