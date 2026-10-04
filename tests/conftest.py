from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    "name: t\non: push\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n"
)

BASE_CASE: dict[str, Any] = {
    "id": "AB-INJ-0001",
    "title": "A valid test case",
    "is_negative": False,
    "expected": [
        {
            "weakness_class": "injection",
            "file": ".github/workflows/wf.yml",
            "line": 7,
            "evidence": "echo hi",
        }
    ],
    "rationale": "A rationale that is comfortably longer than twenty characters.",
    "references": ["https://example.com/ref"],
    "provenance": "synthetic-minimal",
    "status": "proposed",
    "author": "alice",
    "reviewer": None,
    "added_in": "0.1.0",
}

CaseWriter = Callable[..., Path]


@pytest.fixture
def real_corpus() -> Path:
    return REPO_ROOT / "corpus" / "cases"


@pytest.fixture
def make_case(tmp_path: Path) -> CaseWriter:
    """Write a case directory under tmp_path/corpus and return it.

    Keyword arguments override fields of BASE_CASE. Pass `workflow=` to change the
    workflow file contents, and `dirname=` to change the directory name.
    """

    def _make(*, workflow: str = WORKFLOW, dirname: str | None = None, **overrides: Any) -> Path:
        raw = {**BASE_CASE, **overrides}
        case_dir = tmp_path / "corpus" / (dirname or str(raw["id"]))
        (case_dir / ".github" / "workflows").mkdir(parents=True)
        (case_dir / ".github" / "workflows" / "wf.yml").write_text(workflow, encoding="utf-8")
        (case_dir / "case.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
        return case_dir

    return _make
