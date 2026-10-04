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
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx is not installed"),
]


@pytest.mark.parametrize("persona", PERSONAS)
def test_zizmor_on_the_corpus(persona: str, real_corpus: Path, tmp_path: Path) -> None:
    cases = require_valid_corpus(real_corpus)
    result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path)

    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "1.30.1"
    assert result.report.configuration == f"persona={persona}; online-audits=off"

    # Observed 2026-10-04: all seven injection labels matched at exactly the labeled line and the
    # clean cases produced no injection finding, under every persona. This pins that observation
    # so a change in the adapter, the rule map, the labels or zizmor itself is noticed.
    injection = score(cases, result.report).per_class[WeaknessClass.INJECTION]
    assert (injection.tp, injection.fp, injection.fn) == (7, 0, 0)

    # Rules without a reviewed mapping must be surfaced, not hidden.
    assert "zizmor/self-repository" in result.unmapped_rules


def test_persona_changes_whether_write_all_is_reported(real_corpus: Path, tmp_path: Path) -> None:
    """Configuration is part of the result: the same label gets a different verdict."""
    cases = [c for c in require_valid_corpus(real_corpus) if c.id == "AB-PRM-0001"]
    seen = {}
    for persona in PERSONAS:
        result = run_scanner(ZizmorAdapter(persona=persona), cases, tmp_path / persona)
        seen[persona] = "zizmor/excessive-permissions" in result.unmapped_rules
    assert seen == {"regular": False, "pedantic": True, "auditor": True}
