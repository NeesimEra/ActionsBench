"""Runs the real, pinned zizmor over the seed corpus. Opt in with: pytest -m integration

Needs `uvx` and network access to download the pinned release. It is excluded from CI on
purpose: CI should not depend on a download, and a tool-side change should not fail unrelated
pull requests. Run it when changing the adapter, the rule map, or the seed corpus.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from actionsbench.adapters.zizmor import ZizmorAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass

pytestmark = pytest.mark.integration


@pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx is not installed")
def test_zizmor_on_the_seed_corpus(real_corpus: Path, tmp_path: Path) -> None:
    cases = require_valid_corpus(real_corpus)
    result = run_scanner(ZizmorAdapter(), cases, tmp_path)

    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "1.30.1"

    injection = score(cases, result.report).per_class[WeaknessClass.INJECTION]
    # Observed informally on 2026-10-04: all seven injection labels matched at exactly the
    # labeled line, and both negatives were clean. This pins that observation so a change in
    # the adapter, the rule map or the labels is noticed.
    assert (injection.tp, injection.fp, injection.fn) == (7, 0, 0)
    # zizmor also raises a rule that has no reviewed mapping; it must be surfaced, not hidden.
    assert "zizmor/self-repository" in result.unmapped_rules
