"""Adapter for zizmor (https://github.com/zizmorcore/zizmor).

Checked against zizmor 1.30.1 on 2026-10-04: SARIF 2.1.0 output, rule IDs prefixed with
`zizmor/`, case-relative paths when the scan target is an isolated copy outside any git
repository, and exit code 0 even when findings exist.

Online audits are disabled so a run is deterministic and needs no network or token. That means
audits that depend on GitHub's API (for example known-vulnerable actions or impostor-commit
checks) do not run; results must say so.

Mapping policy: only rules whose meaning has been reviewed against a benchmark class are mapped.
Everything else is reported as unmapped by the runner instead of being guessed. Scope is
limited to the classes that have a reviewed mapping, even though zizmor claims wider coverage.
Extend RULE_MAP and SCOPE together, one reviewed rule at a time.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from actionsbench.adapters.base import ScannerOutput, ScannerOutputError
from actionsbench.sarif import parse_sarif
from actionsbench.taxonomy import WeaknessClass

PINNED_VERSION = "1.30.1"

RULE_MAP: dict[str, WeaknessClass] = {
    "zizmor/template-injection": WeaknessClass.INJECTION,
}

SCOPE: frozenset[WeaknessClass] = frozenset(RULE_MAP.values())


class ZizmorAdapter:
    name = "zizmor"
    expected_version: str | None = PINNED_VERSION
    scope = SCOPE
    ok_exit_codes = frozenset({0})
    raw_suffix = "sarif"

    def __init__(self, launcher: Sequence[str] | None = None) -> None:
        # uvx runs the pinned release without installing it into the project environment.
        self._launcher = list(launcher or ["uvx", "--from", f"zizmor=={PINNED_VERSION}", "zizmor"])

    @property
    def label(self) -> str:
        return f"{self.name}-{PINNED_VERSION}"

    def command(self, scan_dir: Path) -> list[str]:
        return [*self._launcher, "--format", "sarif", "--no-online-audits", str(scan_dir)]

    def parse(self, stdout: str, *, case_id: str, scan_dir: Path) -> ScannerOutput:
        try:
            document = json.loads(stdout)
            runs = document["runs"]
            version = runs[0]["tool"]["driver"].get("version") if runs else None
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ScannerOutputError(f"not valid zizmor SARIF: {exc}") from exc

        parsed = parse_sarif(document, case_id=case_id, case_root=scan_dir, rule_map=RULE_MAP)
        return ScannerOutput(
            findings=parsed.findings,
            unmapped_rule_ids=parsed.unmapped_rule_ids,
            locationless=parsed.locationless,
            reported_version=version,
        )
