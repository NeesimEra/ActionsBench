"""Offline pin regressions for reviewed advisory fixtures, not exploitation tests.

Primary-source verification is recorded in docs/ai-label-audit-2026-10-22.md.
These tests catch fixture drift; they do not query advisory databases or prove safety.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from actionsbench.corpus import require_valid_corpus


def download_step(root: Path, workflow: str) -> dict[str, Any]:
    document = yaml.safe_load((root / ".github" / "workflows" / workflow).read_text())
    step: dict[str, Any] = document["jobs"]["fetch"]["steps"][0]
    return step


def test_download_artifact_negative_uses_the_reaudited_release(real_corpus: Path) -> None:
    case = next(c for c in require_valid_corpus(real_corpus) if c.id == "AB-NEG-0007")
    step = download_step(case.root, "patched-download.yml")
    # v4.1.8 bundles artifact 2.1.8, above both conflicting toolkit patch thresholds.
    assert step["uses"] == "actions/download-artifact@fa0a91b85d4f404e444e00e005971372dc801d16"
    assert case.is_negative
    assert case.expected == ()
    assert "https://github.com/advisories/GHSA-cxww-7g56-2vh6" in case.references
    assert "https://github.com/advisories/GHSA-6q32-hq47-5qq3" in case.references


def test_download_artifact_pair_keeps_the_affected_positive_pin(real_corpus: Path) -> None:
    positive = download_step(real_corpus / "AB-KVC-0001", "vulnerable-download.yml")
    negative = download_step(real_corpus / "AB-NEG-0007", "patched-download.yml")
    assert positive["uses"] == "actions/download-artifact@eaceaf801fd36c7dee90939fad912460b18a1ffe"
    assert positive["with"] == negative["with"] == {"name": "build-output"}
