"""Adapter for zizmor (https://github.com/zizmorcore/zizmor).

Checked against zizmor 1.30.1 on 2026-10-04: SARIF 2.1.0 output, rule IDs prefixed with
`zizmor/`, case-relative paths when the scan target is an isolated copy outside any git
repository, and exit code 0 even when findings exist.

Online audits are disabled so a run is deterministic and needs no network or token. That means
audits that depend on GitHub's API (for example known-vulnerable actions or impostor-commit
checks) do not run; results must say so.

Mapping policy (the review record is docs/rule-mappings.md): a rule is mapped only if its
documentation has been read, its benchmark class is unambiguous or the choice is recorded, and a
corpus case exercises it. A rule is never mapped just because it fired on a labeled case.
Everything else is reported as unmapped by the runner instead of being guessed. Scope is the
mapped classes that the tool can actually detect under this configuration: known-vulnerable
components are excluded because zizmor needs online mode for them and this adapter runs offline.
Extend RULE_MAP and docs/rule-mappings.md together, one reviewed rule at a time.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from actionsbench.adapters.base import ScannerOutput, ScannerOutputError
from actionsbench.sarif import parse_sarif
from actionsbench.taxonomy import WeaknessClass

PINNED_VERSION = "1.30.1"

# zizmor suppresses findings by persona. Observed on 2026-10-04: `permissions: write-all` is
# suppressed at "regular" (the default) and reported at "pedantic" and "auditor". The persona is
# therefore always passed explicitly and recorded in every result.
PERSONAS = ("regular", "pedantic", "auditor")
DEFAULT_PERSONA = "regular"

RULE_MAP: dict[str, WeaknessClass] = {
    "zizmor/template-injection": WeaknessClass.INJECTION,
    "zizmor/unpinned-uses": WeaknessClass.UNPINNED_DEPENDENCY,
    "zizmor/excessive-permissions": WeaknessClass.EXCESSIVE_PERMISSION,
    "zizmor/dangerous-triggers": WeaknessClass.PRIVILEGED_TRIGGER,
    "zizmor/secrets-inherit": WeaknessClass.SECRETS_EXPOSURE,
    "zizmor/hardcoded-container-credentials": WeaknessClass.SECRETS_EXPOSURE,
    "zizmor/overprovisioned-secrets": WeaknessClass.SECRETS_EXPOSURE,
    # Debatable: the class's prose is about unvalidated artifacts, but persisted checkout
    # credentials are filed here by the source study, and the corpus label follows it.
    "zizmor/artipacked": WeaknessClass.ARTIFACT_INTEGRITY,
}

SCOPE: frozenset[WeaknessClass] = frozenset(RULE_MAP.values())


class ZizmorAdapter:
    name = "zizmor"
    expected_version: str | None = PINNED_VERSION
    scope = SCOPE
    ok_exit_codes = frozenset({0})
    raw_suffix = "sarif"

    def __init__(
        self, launcher: Sequence[str] | None = None, persona: str = DEFAULT_PERSONA
    ) -> None:
        if persona not in PERSONAS:
            raise ValueError(f"unknown zizmor persona '{persona}' (known: {', '.join(PERSONAS)})")
        self._persona = persona
        # uvx runs the pinned release without installing it into the project environment.
        self._launcher = list(launcher or ["uvx", "--from", f"zizmor=={PINNED_VERSION}", "zizmor"])

    @classmethod
    def from_options(cls, options: Mapping[str, str]) -> ZizmorAdapter:
        remaining = dict(options)
        persona = remaining.pop("persona", DEFAULT_PERSONA)
        if remaining:
            raise ValueError(
                f"unknown option(s) for zizmor: {', '.join(sorted(remaining))} (accepted: persona)"
            )
        return cls(persona=persona)

    @property
    def label(self) -> str:
        return f"{self.name}-{PINNED_VERSION}-{self._persona}"

    @property
    def configuration(self) -> str | None:
        return f"persona={self._persona}; online-audits=off"

    def probe_version(self) -> str | None:
        return None  # zizmor reports its version inside every SARIF document

    def prepare(self, scan_dir: Path) -> None:
        return None  # zizmor needs nothing beyond the copied .github directory

    def command(self, scan_dir: Path) -> list[str]:
        return [
            *self._launcher,
            f"--persona={self._persona}",
            "--format",
            "sarif",
            "--no-online-audits",
            str(scan_dir),
        ]

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
