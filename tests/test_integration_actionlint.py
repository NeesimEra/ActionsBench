"""Runs the real, pinned actionlint over the seed corpus. Opt in with: pytest -m integration

Needs the pinned binary: run scripts/install-actionlint.sh first. Excluded from CI because it
needs a download.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from actionsbench.adapters.actionlint import ActionlintAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass

pytestmark = pytest.mark.integration


def test_actionlint_on_the_seed_corpus(
    real_corpus: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(real_corpus.parents[1])  # the repository root, where .tools/ lives
    adapter = ActionlintAdapter()
    try:
        adapter.probe_version()
    except Exception as exc:  # binary not installed
        pytest.skip(f"actionlint not available: {exc}")

    cases = require_valid_corpus(real_corpus)
    result = run_scanner(adapter, cases, tmp_path)
    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == "1.7.12"

    # Observed 2026-10-04. At tolerance 0, actionlint matched AB-INJ-0001/2/3/5 exactly, missed
    # github.ref_name (AB-INJ-0004) and the composite-action sink (AB-INJ-0007), and anchored
    # the multi-line github-script case (AB-INJ-0006) at the `script:` key (line 15) while the
    # label and zizmor use the interpolation line (16).
    strict = score(cases, result.report, matching="line").per_class[WeaknessClass.INJECTION]
    assert (strict.tp, strict.fp, strict.fn) == (4, 1, 3)

    # The other two reviewed classes are each detected once and never reported on a clean case:
    # `if-cond` on the constant condition and `runner-label` on the retired runner image.
    scored = score(cases, result.report, matching="line")
    for cls in (WeaknessClass.CONTROL_FLOW, WeaknessClass.RUNNER_COMPATIBILITY):
        cell = scored.per_class[cls]
        assert (cell.tp, cell.fp, cell.fn) == (1, 0, 0)

    # Under region matching (the default) the github-script case matches: both lines are in the
    # same step. Tools anchor multi-line blocks differently; this is the evidence for ADR 0003.
    region = score(cases, result.report).per_class[WeaknessClass.INJECTION]
    assert (region.tp, region.fp, region.fn) == (5, 0, 2)
    one_line = score(cases, result.report, matching="line", line_tolerance=1)
    assert one_line.per_class[WeaknessClass.INJECTION] == region
