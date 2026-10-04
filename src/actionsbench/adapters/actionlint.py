"""Adapter for actionlint (https://github.com/rhysd/actionlint).

Checked against actionlint 1.7.12 on 2026-10-04, installed with scripts/install-actionlint.sh.
Observed behaviour this adapter depends on:

* It only treats a directory as a project if it is a git repository root, and exits with code 3
  ("no project was found") otherwise. `prepare` adds an empty `.git` directory to the isolated
  copy, which is enough. The copy is still its own root, so reported paths are case-relative.
* `-format '{{json .}}'` prints a JSON array (`[]` when clean) of objects with `message`,
  `filepath`, `line`, `column`, `kind` and `snippet`. Exit code 0 means no findings, 1 means
  findings, 3 means a fatal error. The tool does not print its version in this output, so the
  version is probed once with `-version`.
* `-shellcheck=` and `-pyflakes=` disable the external linters. They are picked up from PATH by
  default, which would make results depend on the machine.

actionlint is mainly a correctness linter. Only its untrusted-input check is mapped here: an
`expression` result whose message says the value "is potentially untrusted" is an injection
finding. Every other result is reported as unmapped, not guessed at. Scope is therefore the
injection class only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from actionsbench.adapters.base import ScannerNotFoundError, ScannerOutput, ScannerOutputError
from actionsbench.models import Finding
from actionsbench.taxonomy import WeaknessClass

PINNED_VERSION = "1.7.12"
ENV_VAR = "ACTIONSBENCH_ACTIONLINT"

UNTRUSTED_RULE_ID = "actionlint/expression:untrusted-input"
SCOPE: frozenset[WeaknessClass] = frozenset({WeaknessClass.INJECTION})

# Exact wording as of 1.7.12; the version pin protects against it changing silently.
_UNTRUSTED_MESSAGE = re.compile(r'^"[^"]+" is potentially untrusted\.')


def _default_launcher() -> str:
    from_env = os.environ.get(ENV_VAR)
    if from_env:
        return from_env
    installed = Path.cwd() / ".tools" / f"actionlint-{PINNED_VERSION}" / "actionlint"
    if installed.is_file():
        return str(installed)
    return "actionlint"


def classify(kind: str, message: str) -> tuple[str, WeaknessClass | None]:
    """Return (rule id, benchmark class or None) for one actionlint result."""
    if kind == "expression" and _UNTRUSTED_MESSAGE.match(message):
        return UNTRUSTED_RULE_ID, WeaknessClass.INJECTION
    return f"actionlint/{kind}", None


class ActionlintAdapter:
    name = "actionlint"
    expected_version: str | None = PINNED_VERSION
    scope = SCOPE
    ok_exit_codes = frozenset({0, 1})
    raw_suffix = "json"

    def __init__(self, launcher: str | None = None) -> None:
        self._launcher = launcher or _default_launcher()

    @property
    def label(self) -> str:
        return f"{self.name}-{PINNED_VERSION}"

    def probe_version(self) -> str | None:
        try:
            completed = subprocess.run(  # noqa: S603 - fixed argument list, no shell
                [self._launcher, "-version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ScannerNotFoundError(
                f"cannot start '{self._launcher}': {exc}. "
                "Run scripts/install-actionlint.sh or set ACTIONSBENCH_ACTIONLINT."
            ) from exc
        lines = completed.stdout.strip().splitlines()
        return lines[0].strip() if lines else None

    def prepare(self, scan_dir: Path) -> None:
        (scan_dir / ".git").mkdir(exist_ok=True)

    def command(self, scan_dir: Path) -> list[str]:
        # No path argument: the tool finds the project from the working directory, which the
        # runner sets to the isolated copy.
        return [self._launcher, "-format", "{{json .}}", "-shellcheck=", "-pyflakes="]

    def parse(self, stdout: str, *, case_id: str, scan_dir: Path) -> ScannerOutput:
        try:
            results = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ScannerOutputError(f"not valid actionlint JSON: {exc}") from exc
        if results is None:
            results = []
        if not isinstance(results, list):
            raise ScannerOutputError("actionlint JSON is not an array")

        output = ScannerOutput()
        for item in results:
            self._add_result(output, item, case_id)
        return output

    @staticmethod
    def _add_result(output: ScannerOutput, item: Any, case_id: str) -> None:
        if not isinstance(item, dict):
            raise ScannerOutputError("actionlint result is not an object")
        kind = str(item.get("kind", ""))
        message = str(item.get("message", ""))
        rule_id, weakness_class = classify(kind, message)
        if weakness_class is None:
            output.unmapped_rule_ids.add(rule_id)
            return
        filepath, line = item.get("filepath"), item.get("line")
        if not isinstance(filepath, str) or not isinstance(line, int):
            output.locationless.append(rule_id)
            return
        output.findings.append(
            Finding(
                case_id=case_id,
                weakness_class=weakness_class,
                file=Path(filepath).as_posix(),
                line=line,
                rule_id=rule_id,
            )
        )
