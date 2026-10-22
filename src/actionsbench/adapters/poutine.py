"""poutine 1.1.6 local SARIF adapter; reviewed mappings: docs/rule-mappings.md.

Checked against isolated copies of all 44 cases on 2026-10-22. Local analysis needs
neither a git repository nor a token. Rule IDs are unprefixed, paths are case-relative,
and the version is in driver.semanticVersion (not driver.version).
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from actionsbench.adapters.base import ScannerOutput, ScannerOutputError
from actionsbench.sarif import parse_sarif
from actionsbench.taxonomy import WeaknessClass

PINNED_VERSION = "1.1.6"
ENV_VAR = "ACTIONSBENCH_POUTINE"
CONFIG_FILE = ".poutine.yml"

RULE_MAP: dict[str, WeaknessClass] = {
    "injection": WeaknessClass.INJECTION,
    "job_all_secrets": WeaknessClass.SECRETS_EXPOSURE,
    "untrusted_checkout_exec": WeaknessClass.PRIVILEGED_TRIGGER,
}
SCOPE = frozenset(RULE_MAP.values())


def _default_launcher() -> str:
    if from_env := os.environ.get(ENV_VAR):
        # Resolve explicit relative paths before the runner changes working directory.
        return str(Path(from_env).resolve()) if os.sep in from_env else from_env
    installed = Path.cwd() / ".tools" / f"poutine-{PINNED_VERSION}" / "poutine"
    return str(installed) if installed.is_file() else "poutine"


class PoutineAdapter:
    name = "poutine"
    expected_version: str | None = PINNED_VERSION
    scope = SCOPE
    ok_exit_codes = frozenset({0})  # no --fail-on-violation: findings still exit 0
    raw_suffix = "sarif"

    def __init__(self, launcher: str | None = None) -> None:
        self._launcher = launcher or _default_launcher()

    @classmethod
    def from_options(cls, options: Mapping[str, str]) -> PoutineAdapter:
        if options:
            raise ValueError(
                f"unknown option(s) for poutine: {', '.join(sorted(options))} (none accepted)"
            )
        return cls()

    @property
    def label(self) -> str:
        return f"{self.name}-{PINNED_VERSION}-local"

    @property
    def configuration(self) -> str | None:
        return "analysis=local; config=empty; version-check=off"

    def probe_version(self) -> str | None:
        return None  # every SARIF run reports semanticVersion

    def prepare(self, scan_dir: Path) -> None:
        # An explicit empty config prevents auto-discovered .github/poutine.yml from
        # suppressing findings or loading custom rules. Do not modify the corpus copy.
        (scan_dir / CONFIG_FILE).write_text("{}\n", encoding="utf-8")

    def command(self, scan_dir: Path) -> list[str]:
        return [
            self._launcher,
            "analyze_local",
            ".",
            "--format",
            "sarif",
            "--config",
            str(scan_dir / CONFIG_FILE),
            "--disable-version-check",
        ]

    def parse(self, stdout: str, *, case_id: str, scan_dir: Path) -> ScannerOutput:
        try:
            document = json.loads(stdout)
            if document["version"] != "2.1.0":
                raise ValueError("expected SARIF 2.1.0")
            runs = document["runs"]
            if not isinstance(runs, list) or len(runs) != 1:
                raise ValueError("expected one local analysis run")
            driver = runs[0]["tool"]["driver"]
            version = driver["semanticVersion"]
            if driver["name"] != "poutine" or not isinstance(version, str) or not version:
                raise ValueError("missing poutine name or semantic version")
            results = runs[0]["results"]
            if not isinstance(results, list) or any(not isinstance(r, dict) for r in results):
                raise ValueError("results must be an array of objects")
            parsed = parse_sarif(document, case_id=case_id, case_root=scan_dir, rule_map=RULE_MAP)
            if any(type(f.line) is not int or f.line < 1 for f in parsed.findings):
                raise ValueError("finding line must be a positive integer")
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise ScannerOutputError(f"not valid poutine SARIF: {exc}") from exc
        return ScannerOutput(
            findings=parsed.findings,
            unmapped_rule_ids=parsed.unmapped_rule_ids,
            locationless=parsed.locationless,
            reported_version=version,
        )
