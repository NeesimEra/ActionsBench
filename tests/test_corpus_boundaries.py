"""Static guards for ADR 0006. Never execute the signing or artifact workflows."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml

from actionsbench.corpus import require_valid_corpus
from actionsbench.models import Finding, ScannerReport
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass as W


def workflow(root: Path, file: str) -> dict[str, Any]:
    document: dict[str, Any] = yaml.safe_load((root / ".github" / "workflows" / file).read_text())
    return document


def test_echo_only_negative_requests_no_token_scopes(real_corpus: Path) -> None:
    document = workflow(real_corpus / "AB-NEG-0004", "read-only.yml")
    assert document["permissions"] == {}
    assert document["jobs"]["build"]["steps"] == [{"name": "Build", "run": 'echo "building"'}]


def test_named_secret_negative_consumes_only_its_signing_key(real_corpus: Path) -> None:
    document = workflow(real_corpus / "AB-NEG-0015", "named-secret.yml")
    assert document["permissions"] == {}
    step = document["jobs"]["build"]["steps"][0]
    assert step["env"] == {"SIGNING_KEY": "${{ secrets.SIGNING_KEY }}"}
    script = step["run"]
    assert "${{" not in script
    assert script.startswith("python3 - <<'PY'\n")
    assert script.endswith("\nPY\n")
    python = script.split("\n", maxsplit=1)[1].rsplit("\nPY", maxsplit=1)[0]
    tree = ast.parse(python)  # syntax inspection only; never compile or execute
    assert 'key = os.environ.get("SIGNING_KEY", "")' in python
    assert 'if not key:\n    raise SystemExit("SIGNING_KEY is required")' in python
    assert 'hmac.new(key.encode(), b"build-output", hashlib.sha256).hexdigest()' in python
    prints = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert len(prints) == 1
    assert len(prints[0].args) == 1
    assert isinstance(prints[0].args[0], ast.Name)
    assert prints[0].args[0].id == "tag"


def test_artifact_labels_anchor_at_exposure_and_consumption(real_corpus: Path) -> None:
    cases = {c.id: c for c in require_valid_corpus(real_corpus)}
    for case_id, evidence in (
        ("AB-ART-0001", "uses: actions/upload-artifact@"),
        ("AB-ART-0002", "tar xzf tool.tar.gz"),
    ):
        finding = cases[case_id].expected[0]
        assert finding.weakness_class is W.ARTIFACT_INTEGRITY
        assert finding.line == 15
        assert finding.evidence == evidence


def test_checkout_detection_does_not_match_the_upload_sink(real_corpus: Path) -> None:
    case = next(c for c in require_valid_corpus(real_corpus) if c.id == "AB-ART-0001")
    report = ScannerReport(
        tool="checkout-anchor",
        version="1",
        scope=frozenset({W.ARTIFACT_INTEGRITY}),
        cases_run=frozenset({case.id}),
        findings=(Finding(case.id, W.ARTIFACT_INTEGRITY, case.expected[0].file, 12),),
    )
    cell = score([case], report).per_class[W.ARTIFACT_INTEGRITY]
    assert (cell.tp, cell.fp, cell.fn) == (0, 1, 1)
