"""Real pinned poutine, opt-in with pytest -m integration after install-poutine.sh.

Counts describe the current matching policy, not a tool ranking. Two detections have
cross-region anchors; see docs/rule-mappings.md. Labels must not be moved to fit them.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from actionsbench.adapters.poutine import PINNED_VERSION, PoutineAdapter
from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import run_scanner
from actionsbench.scoring import score
from actionsbench.taxonomy import WeaknessClass as W

pytestmark = pytest.mark.integration


def test_poutine_on_the_corpus(
    real_corpus: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(real_corpus.parents[1])
    adapter = PoutineAdapter()
    if shutil.which(adapter.command(tmp_path)[0]) is None:
        pytest.skip("poutine is not installed; run sh scripts/install-poutine.sh")
    cases = require_valid_corpus(real_corpus)
    result = run_scanner(adapter, cases, tmp_path)
    assert result.failures == {}
    assert result.report.cases_run == {c.id for c in cases}
    assert result.report.version == PINNED_VERSION
    assert result.report.configuration == adapter.configuration
    assert result.locationless == []

    scored = score(cases, result.report)
    cells = {cls: (s.tp, s.fp, s.fn) for cls, s in scored.per_class.items() if s.in_scope}
    assert cells == {
        W.INJECTION: (5, 0, 5),
        W.SECRETS_EXPOSURE: (0, 1, 3),
        W.PRIVILEGED_TRIGGER: (0, 1, 1),
    }
    anchors = {f.rule_id: (f.case_id, f.line) for f in result.report.findings}
    assert anchors["job_all_secrets"] == ("AB-SEC-0003", 9)
    assert anchors["untrusted_checkout_exec"] == ("AB-TRG-0001", 19)
    assert result.unmapped_rules == {
        "github_action_from_unverified_creator_used": ["AB-KVC-0002", "AB-NEG-0016"],
        "pr_runs_on_self_hosted": ["AB-RUN-0002"],
    }
