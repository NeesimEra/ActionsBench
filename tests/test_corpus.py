from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from actionsbench.corpus import CorpusError, load_case, load_corpus, require_valid_corpus
from actionsbench.models import Status
from tests.conftest import CaseWriter


def _messages(case_dir: Path) -> list[str]:
    case, problems = load_case(case_dir)
    assert case is None
    return [p.message for p in problems]


def test_real_corpus_is_valid(real_corpus: Path) -> None:
    cases, problems = load_corpus(real_corpus)
    assert problems == []
    assert len(cases) >= 9


def test_real_corpus_has_negatives_and_positives(real_corpus: Path) -> None:
    cases = require_valid_corpus(real_corpus)
    assert any(c.is_negative for c in cases)
    assert any(not c.is_negative for c in cases)


def test_valid_case_loads(make_case: CaseWriter) -> None:
    case, problems = load_case(make_case())
    assert problems == []
    assert case is not None
    assert case.status is Status.PROPOSED
    assert case.expected[0].line == 7


def test_id_must_match_directory_name(make_case: CaseWriter) -> None:
    messages = _messages(make_case(dirname="AB-INJ-0099"))
    assert any("does not match directory name" in m for m in messages)


def test_negative_case_must_not_list_findings(make_case: CaseWriter) -> None:
    messages = _messages(make_case(id="AB-NEG-0001", is_negative=True))
    assert any("negative case must not list expected findings" in m for m in messages)


def test_positive_case_needs_a_finding(make_case: CaseWriter) -> None:
    messages = _messages(make_case(expected=[]))
    assert any("at least one expected finding" in m for m in messages)


def test_id_prefix_must_match_primary_class(make_case: CaseWriter) -> None:
    messages = _messages(make_case(id="AB-PIN-0001"))
    assert any("id prefix must be 'INJ'" in m for m in messages)


def test_line_past_end_of_file(make_case: CaseWriter) -> None:
    expected: list[dict[str, Any]] = [
        {
            "weakness_class": "injection",
            "file": ".github/workflows/wf.yml",
            "line": 99,
            "evidence": "echo hi",
        }
    ]
    assert any("past the end of the file" in m for m in _messages(make_case(expected=expected)))


def test_evidence_must_appear_on_the_labeled_line(make_case: CaseWriter) -> None:
    expected: list[dict[str, Any]] = [
        {
            "weakness_class": "injection",
            "file": ".github/workflows/wf.yml",
            "line": 1,
            "evidence": "echo hi",
        }
    ]
    assert any("does not contain evidence" in m for m in _messages(make_case(expected=expected)))


def test_missing_expected_file(make_case: CaseWriter) -> None:
    expected: list[dict[str, Any]] = [
        {
            "weakness_class": "injection",
            "file": ".github/workflows/nope.yml",
            "line": 1,
            "evidence": "x",
        }
    ]
    assert any("does not exist" in m for m in _messages(make_case(expected=expected)))


@pytest.mark.parametrize("bad_path", ["../outside.yml", "/etc/hosts"])
def test_expected_file_cannot_escape_the_case_directory(
    make_case: CaseWriter, bad_path: str
) -> None:
    expected: list[dict[str, Any]] = [
        {"weakness_class": "injection", "file": bad_path, "line": 1, "evidence": "x"}
    ]
    assert any("escapes the case directory" in m for m in _messages(make_case(expected=expected)))


def test_agreed_status_needs_independent_reviewer(make_case: CaseWriter) -> None:
    same = _messages(make_case(status="agreed", reviewer="alice"))
    assert any("different from the author" in m for m in same)


def test_agreed_status_with_independent_reviewer_is_valid(make_case: CaseWriter) -> None:
    case, problems = load_case(make_case(status="agreed", reviewer="bob"))
    assert problems == []
    assert case is not None
    assert case.reviewer == "bob"


def test_unknown_weakness_class_is_rejected_by_schema(make_case: CaseWriter) -> None:
    expected: list[dict[str, Any]] = [
        {
            "weakness_class": "made-up",
            "file": ".github/workflows/wf.yml",
            "line": 7,
            "evidence": "echo hi",
        }
    ]
    assert _messages(make_case(expected=expected))


def test_reference_must_be_a_url(make_case: CaseWriter) -> None:
    assert _messages(make_case(references=["see my notes"]))


def test_unknown_field_is_rejected(make_case: CaseWriter) -> None:
    assert _messages(make_case(severity="high"))


def test_missing_case_file(tmp_path: Path) -> None:
    (tmp_path / "AB-INJ-0001").mkdir()
    assert any("missing case.yaml" in m for m in _messages(tmp_path / "AB-INJ-0001"))


def test_reusing_an_id_in_another_directory_is_rejected(make_case: CaseWriter) -> None:
    # Uniqueness of ids follows from "id must equal the directory name".
    make_case()
    make_case(dirname="AB-INJ-0002")  # carries id AB-INJ-0001 inside
    cases, problems = load_corpus(make_case(id="AB-INJ-0003").parent)
    assert [c.id for c in cases] == ["AB-INJ-0001", "AB-INJ-0003"]
    assert any("does not match directory name" in p.message for p in problems)


def test_missing_corpus_directory(tmp_path: Path) -> None:
    cases, problems = load_corpus(tmp_path / "nope")
    assert cases == []
    assert problems


def test_require_valid_corpus_raises_with_all_problems(make_case: CaseWriter) -> None:
    make_case(expected=[])
    corpus_root = make_case(id="AB-INJ-0002", expected=[]).parent
    with pytest.raises(CorpusError) as excinfo:
        require_valid_corpus(corpus_root)
    assert len(excinfo.value.problems) == 2
