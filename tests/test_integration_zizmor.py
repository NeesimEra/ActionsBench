"""Runs the real, pinned zizmor over the corpus. Opt in with: pytest -m integration

Needs `uvx` and network access to download the pinned release. It is excluded from CI on
purpose: CI should not depend on a download, and a tool-side change should not fail unrelated
pull requests. Run it when changing the adapter, the rule map, or the corpus.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from actionsbench.adapters.zizmor import PERSONAS, ZizmorAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import ScoreResult, score
from actionsbench.taxonomy import WeaknessClass

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx is not installed"),
]


def _cells(scored: ScoreResult) -> dict[WeaknessClass, tuple[int, int, int]]:
    return {cls: (c.tp, c.fp, c.fn) for cls, c in scored.per_class.items() if c.in_scope}


@pytest.mark.parametrize("persona", PERSONAS)
def test_zizmor_on_the_corpus(persona: str, real_corpus: Path, tmp_path: Path) -> None:
    cases = require_valid_corpus(real_corpus)
    result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path)

    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "1.30.1"
    assert result.report.configuration == f"persona={persona}; online-audits=off"

    # Observed 2026-10-04 (hand-built labels, one reviewer; see docs/rule-mappings.md). Cells are
    # (TP, FP, FN). No tool-reported finding landed on a clean case, under any persona.
    #
    # With region matching (the default) every labeled weakness in scope is found, except
    # `write-all` at the default persona, which zizmor suppresses.
    expected_region = {
        WeaknessClass.INJECTION: (7, 0, 0),
        WeaknessClass.UNPINNED_DEPENDENCY: (2, 0, 0),
        WeaknessClass.EXCESSIVE_PERMISSION: (0, 0, 1) if persona == "regular" else (1, 0, 0),
        WeaknessClass.PRIVILEGED_TRIGGER: (1, 0, 0),
        WeaknessClass.SECRETS_EXPOSURE: (1, 0, 0),
        WeaknessClass.ARTIFACT_INTEGRITY: (1, 0, 0),
    }
    assert _cells(score(cases, result.report)) == expected_region
    # On this corpus region matching and a one-line tolerance agree exactly; that agreement is the
    # evidence the region rule rests on (ADR 0003).
    one_line = score(cases, result.report, matching="line", line_tolerance=1)
    assert _cells(one_line) == expected_region

    # Strictly (exact line), three classes are detected one line away from the label: zizmor
    # reports the `on:` line, the `uses:` line of the reusable-workflow call and the step header.
    # Each costs one false positive and one false negative. This pins that anchoring evidence
    # for the open matching-rule decision (ADR 0003).
    expected_strict = {
        **expected_region,
        WeaknessClass.PRIVILEGED_TRIGGER: (0, 1, 1),
        WeaknessClass.SECRETS_EXPOSURE: (0, 1, 1),
        WeaknessClass.ARTIFACT_INTEGRITY: (0, 1, 1),
    }
    assert _cells(score(cases, result.report, matching="line")) == expected_strict

    # Rules without a reviewed mapping must be surfaced, not hidden.
    assert "zizmor/self-repository" in result.unmapped_rules


def test_persona_changes_whether_write_all_is_reported(real_corpus: Path, tmp_path: Path) -> None:
    """Configuration is part of the result: the same label gets a different verdict."""
    cases = [c for c in require_valid_corpus(real_corpus) if c.id == "AB-PRM-0001"]
    seen = {}
    for persona in PERSONAS:
        result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path / persona)
        seen[persona] = any(
            f.weakness_class is WeaknessClass.EXCESSIVE_PERMISSION for f in result.report.findings
        )
    assert seen == {"regular": False, "pedantic": True, "auditor": True}
