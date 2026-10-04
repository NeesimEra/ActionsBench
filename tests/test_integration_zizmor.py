"""Runs the real, pinned zizmor over the corpus. Opt in with: pytest -m integration

Needs `uvx` and network access to download the pinned release. It is excluded from CI on
purpose: CI should not depend on a download, and a tool-side change should not fail unrelated
pull requests. Run it when changing the adapter, the rule map, or the corpus.

The tables below are observations (2026-10-04, 44 hand-built cases, one reviewer), pinned so that
a change in the adapter, the rule map, the labels or zizmor itself is noticed. Cells are
(TP, FP, FN). Each disagreement is explained in docs/rule-mappings.md or status.md.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from actionsbench.adapters.zizmor import PERSONAS, ZizmorAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import ScoreResult, score
from actionsbench.taxonomy import WeaknessClass as W

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx is not installed"),
]


def _cells(scored: ScoreResult) -> dict[W, tuple[int, int, int]]:
    return {cls: (c.tp, c.fp, c.fn) for cls, c in scored.per_class.items() if c.in_scope}


def _expected_region(persona: str) -> dict[W, tuple[int, int, int]]:
    default = persona == "regular"
    return {
        # pedantic and auditor flag every template expansion, including the two safe contexts
        # (pull request number and commit SHA) in AB-NEG-0012: a configuration effect.
        W.INJECTION: (10, 0, 0) if default else (10, 2, 0),
        W.UNPINNED_DEPENDENCY: (3, 0, 0),
        # the default persona suppresses both workflow-level write grants
        W.EXCESSIVE_PERMISSION: (0, 0, 2) if default else (2, 0, 0),
        # AB-NEG-0010: zizmor flags the trigger itself, the class definition needs untrusted data
        W.PRIVILEGED_TRIGGER: (1, 1, 0),
        W.SECRETS_EXPOSURE: (3, 0, 0),
        # AB-ART-0002 is a miss only because the class is judged through artipacked alone
        W.ARTIFACT_INTEGRITY: (1, 0, 1),
    }


@pytest.mark.parametrize("persona", PERSONAS)
def test_zizmor_on_the_corpus(persona: str, real_corpus: Path, tmp_path: Path) -> None:
    cases = require_valid_corpus(real_corpus)
    result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path)

    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "1.30.1"
    assert result.report.configuration == f"persona={persona}; online-audits=off"

    expected = _expected_region(persona)
    assert _cells(score(cases, result.report)) == expected

    # Strictly (exact line) the anchoring differences show up: zizmor reports the `on:` line, the
    # call's `uses:` line, a step header, and for container credentials the `container:` block two
    # lines above the password.
    strict = {
        **expected,
        W.PRIVILEGED_TRIGGER: (0, 2, 1),
        W.SECRETS_EXPOSURE: (1, 2, 2),
        W.ARTIFACT_INTEGRITY: (0, 1, 2),
    }
    assert _cells(score(cases, result.report, matching="line")) == strict

    # A one-line tolerance is not enough once a report is two lines from the label (the container
    # credentials case); a tolerance of two happens to equal the region rule on this corpus, but a
    # longer block would need a bigger number. That is the argument for regions (ADR 0003).
    one_line = _cells(score(cases, result.report, matching="line", line_tolerance=1))
    assert one_line == {**expected, W.SECRETS_EXPOSURE: (2, 1, 1)}
    two_lines = score(cases, result.report, matching="line", line_tolerance=2)
    assert _cells(two_lines) == expected

    # Rules without a reviewed mapping must be surfaced, not hidden.
    assert "zizmor/self-repository" in result.unmapped_rules


def test_persona_changes_whether_write_all_is_reported(real_corpus: Path, tmp_path: Path) -> None:
    """Configuration is part of the result: the same label gets a different verdict."""
    cases = [c for c in require_valid_corpus(real_corpus) if c.id == "AB-PRM-0001"]
    seen = {}
    for persona in PERSONAS:
        result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path / persona)
        seen[persona] = any(
            f.weakness_class is W.EXCESSIVE_PERMISSION for f in result.report.findings
        )
    assert seen == {"regular": False, "pedantic": True, "auditor": True}
