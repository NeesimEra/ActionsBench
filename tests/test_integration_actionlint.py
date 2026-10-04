"""Runs the real, pinned actionlint over the corpus. Opt in with: pytest -m integration

Needs the pinned binary: run scripts/install-actionlint.sh first. Excluded from CI because it
needs a download. The numbers are observations (2026-10-04, 44 hand-built cases, one reviewer).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from actionsbench.adapters.actionlint import ActionlintAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import ScoreResult, score
from actionsbench.taxonomy import WeaknessClass as W

pytestmark = pytest.mark.integration


def cell(scored: ScoreResult, cls: W) -> tuple[int, int, int]:
    c = scored.per_class[cls]
    return (c.tp, c.fp, c.fn)


def test_actionlint_on_the_corpus(
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
    assert result.report.configuration == "external-linters=disabled"

    region = score(cases, result.report)
    # Misses: github.ref_name (AB-INJ-0004) and the composite-action sink (AB-INJ-0007).
    assert cell(region, W.INJECTION) == (8, 0, 2)
    assert cell(region, W.CONTROL_FLOW) == (1, 0, 0)
    assert cell(region, W.RUNNER_COMPATIBILITY) == (2, 0, 0)
    # The only secrets check is the hardcoded-credentials one, so the other two secrets cases
    # (secrets: inherit, toJSON(secrets)) count as misses: the class-level scope limitation.
    assert cell(region, W.SECRETS_EXPOSURE) == (1, 0, 2)

    # Exact line: actionlint reports a multi-line script at the `script:` / `run:` key, above the
    # labeled interpolation line (one line for github-script, two for the long run block).
    strict = score(cases, result.report, matching="line")
    assert cell(strict, W.INJECTION) == (6, 2, 4)

    # One line of tolerance is not enough for the long run block; two lines happens to equal the
    # region rule here, but a longer block would need a bigger number (ADR 0003).
    one_line = score(cases, result.report, matching="line", line_tolerance=1)
    assert cell(one_line, W.INJECTION) == (7, 1, 3)
    two_lines = score(cases, result.report, matching="line", line_tolerance=2)
    assert cell(two_lines, W.INJECTION) == cell(region, W.INJECTION)
