"""Run a scanner over the corpus and produce a findings file for `actionsbench score`.

Rules the runner enforces (docs/methodology.md, sections 1 and 6):

* Each case is scanned from an isolated copy of its `.github/` directory in a fresh temporary
  directory. The label (`case.yaml`) never reaches the scanner, and tools that resolve paths
  against an enclosing git repository cannot see this one.
* A case only counts as run if the scanner exited with an accepted code and its output parsed.
  Timeouts, crashes and unparseable output exclude the case from `cases_run`, and the reason is
  recorded. A failed case is never treated as "ran and found nothing".
* Every finding's path must resolve to a file inside the isolated copy. A path that does not
  means the scanner reported something other than case-relative paths, which would silently turn
  into false positives and false negatives, so the case is failed instead.
* Rule IDs without a reviewed mapping are collected and reported, not dropped.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from actionsbench.adapters.base import (
    ScannerAdapter,
    ScannerNotFoundError,
    ScannerOutputError,
    ScannerVersionError,
)
from actionsbench.models import Case, Finding, ScannerReport


@dataclass(slots=True)
class RunResult:
    report: ScannerReport
    failures: dict[str, str] = field(default_factory=dict)
    # rule id -> case ids where the tool reported it without a reviewed mapping
    unmapped_rules: dict[str, list[str]] = field(default_factory=dict)
    # (case id, rule id) for results that had no usable file and line
    locationless: list[tuple[str, str]] = field(default_factory=list)
    raw_dir: Path | None = None


def materialize_case(case: Case, parent: Path) -> Path:
    """Copy only the case's `.github/` directory into `parent/<case id>` and return that path."""
    scan_dir = parent / case.id
    scan_dir.mkdir(parents=True)
    shutil.copytree(case.root / ".github", scan_dir / ".github", symlinks=True)
    return scan_dir


def findings_document(report: ScannerReport) -> dict[str, Any]:
    """Serialize a report to the shape of findings.schema.json."""
    findings: list[dict[str, Any]] = []
    for f in report.findings:
        item: dict[str, Any] = {
            "case_id": f.case_id,
            "weakness_class": f.weakness_class.value,
            "file": f.file,
            "line": f.line,
        }
        if f.rule_id is not None:
            item["rule_id"] = f.rule_id
        findings.append(item)
    document: dict[str, Any] = {"tool": report.tool, "version": report.version}
    if report.configuration is not None:
        document["configuration"] = report.configuration
    document["scope"] = sorted(c.value for c in report.scope)
    document["cases_run"] = sorted(report.cases_run)
    document["findings"] = findings
    return document


def _unresolved_paths(findings: Sequence[Finding], scan_dir: Path) -> list[str]:
    root = scan_dir.resolve()
    bad: list[str] = []
    for finding in findings:
        target = (root / finding.file).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            bad.append(finding.file)
    return bad


def run_scanner(
    adapter: ScannerAdapter,
    cases: Sequence[Case],
    out_dir: Path,
    *,
    timeout: float = 120.0,
) -> RunResult:
    raw_dir = out_dir / adapter.label / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = RunResult(
        report=ScannerReport(
            tool=adapter.name,
            version=adapter.expected_version or "unknown",
            scope=adapter.scope,
            cases_run=frozenset(),
            findings=(),
            configuration=adapter.configuration,
        ),
        raw_dir=raw_dir,
    )
    cases_run: set[str] = set()
    findings: list[Finding] = []

    # Tools that do not print their version in their output are asked once, up front. A tool
    # that is not the pinned version would make every result misleading, so this fails the run.
    seen_version = adapter.probe_version()
    if seen_version and adapter.expected_version and seen_version != adapter.expected_version:
        raise ScannerVersionError(
            f"{adapter.name} reports version {seen_version}, but the adapter is pinned to "
            f"{adapter.expected_version}"
        )

    with tempfile.TemporaryDirectory(prefix="actionsbench-") as tmp:
        for case in sorted(cases, key=lambda c: c.id):
            scan_dir = materialize_case(case, Path(tmp))
            adapter.prepare(scan_dir)
            command = adapter.command(scan_dir)
            try:
                # No shell is involved: the command is a list built by a trusted adapter.
                completed = subprocess.run(  # noqa: S603
                    command,
                    cwd=scan_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
            except FileNotFoundError as exc:
                raise ScannerNotFoundError(f"cannot start '{command[0]}': {exc}") from exc
            except subprocess.TimeoutExpired:
                result.failures[case.id] = f"timed out after {timeout:g}s"
                continue

            if completed.returncode not in adapter.ok_exit_codes:
                tail = completed.stderr.strip().splitlines()[-1:] or ["(no stderr)"]
                result.failures[case.id] = f"exit code {completed.returncode}: {tail[0]}"
                continue

            (raw_dir / f"{case.id}.{adapter.raw_suffix}").write_text(completed.stdout, "utf-8")
            try:
                output = adapter.parse(completed.stdout, case_id=case.id, scan_dir=scan_dir)
            except ScannerOutputError as exc:
                result.failures[case.id] = f"unparseable output: {exc}"
                continue

            reported = output.reported_version
            if adapter.expected_version and reported and reported != adapter.expected_version:
                result.failures[case.id] = (
                    f"tool reported version {reported}, adapter is pinned to "
                    f"{adapter.expected_version}"
                )
                continue
            if reported:
                if seen_version is not None and reported != seen_version:
                    result.failures[case.id] = (
                        f"tool version changed during the run ({seen_version} then {reported})"
                    )
                    continue
                seen_version = reported

            bad_paths = _unresolved_paths(output.findings, scan_dir)
            if bad_paths:
                result.failures[case.id] = (
                    "finding path does not resolve inside the isolated copy: "
                    + ", ".join(sorted(set(bad_paths)))
                )
                continue

            cases_run.add(case.id)
            findings.extend(output.findings)
            for rule_id in output.unmapped_rule_ids:
                result.unmapped_rules.setdefault(rule_id, []).append(case.id)
            result.locationless.extend((case.id, rule) for rule in output.locationless)

    result.report = ScannerReport(
        tool=adapter.name,
        version=seen_version or adapter.expected_version or "unknown",
        scope=adapter.scope,
        cases_run=frozenset(cases_run),
        findings=tuple(findings),
        configuration=adapter.configuration,
    )
    return result
