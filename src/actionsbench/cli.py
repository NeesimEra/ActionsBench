"""Command-line entry point: `actionsbench validate | stats | run | score`.

`run` executes a scanner that has a reviewed adapter and writes a findings file; `score` judges
any findings file. Adapters are added one at a time, after each tool's real output has been
checked (docs/adr/0003-scanner-scope-and-scoring.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import Any

from actionsbench import __version__
from actionsbench.adapters import ADAPTERS, get_adapter
from actionsbench.adapters.base import ScannerNotFoundError, ScannerVersionError
from actionsbench.corpus import (
    CorpusError,
    load_corpus,
    require_valid_corpus,
    validate_json,
)
from actionsbench.models import Finding, ScannerReport
from actionsbench.report import to_json, to_text
from actionsbench.runner import findings_document, run_scanner
from actionsbench.scoring import ScoringInputError, score
from actionsbench.taxonomy import WeaknessClass

LOCAL_CORPUS = Path("corpus/cases")


def _packaged_corpus() -> Path:
    # The wheel ships the corpus as package data (see pyproject.toml). Installed normally this is a
    # real directory; a zipped install is not supported.
    return Path(str(files("actionsbench"))) / "_corpus" / "cases"


def default_corpus(*, local: Path = LOCAL_CORPUS, packaged: Path | None = None) -> Path:
    """Where to read the corpus when --corpus is not given.

    A `corpus/cases` directory in the working directory wins, so a clone of the repository uses its
    own, possibly edited, corpus. Otherwise the copy bundled in the installed package is used.
    If neither exists the local path is returned, so the error names the path a user expects.
    """
    bundled = packaged if packaged is not None else _packaged_corpus()
    if local.is_dir():
        return local
    if bundled.is_dir():
        return bundled
    return local


def _corpus(args: argparse.Namespace) -> Path:
    corpus: Path | None = args.corpus
    return corpus if corpus is not None else default_corpus()


def _report_from_json(data: dict[str, Any]) -> ScannerReport:
    """Build a report from data already validated against findings.schema.json."""
    return ScannerReport(
        tool=data["tool"],
        version=data["version"],
        scope=frozenset(WeaknessClass(c) for c in data["scope"]),
        cases_run=frozenset(data["cases_run"]),
        configuration=data.get("configuration"),
        findings=tuple(
            Finding(
                case_id=f["case_id"],
                weakness_class=WeaknessClass(f["weakness_class"]),
                file=f["file"],
                line=f["line"],
                rule_id=f.get("rule_id"),
            )
            for f in data["findings"]
        ),
    )


def _cmd_validate(args: argparse.Namespace) -> int:
    cases, problems = load_corpus(_corpus(args))
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} problem(s) found; {len(cases)} case(s) valid.", file=sys.stderr)
        return 1
    print(f"OK: {len(cases)} case(s) valid.")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    try:
        cases = require_valid_corpus(_corpus(args))
    except CorpusError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    by_class: Counter[str] = Counter()
    for case in cases:
        if case.is_negative:
            by_class["(negative)"] += 1
        for cls in {e.weakness_class for e in case.expected}:
            by_class[cls.value] += 1
    print(f"{len(cases)} case(s)")
    for name, count in sorted(by_class.items()):
        print(f"  {name:<28}{count:>4}")
    print(
        "status: "
        + ", ".join(f"{k}={v}" for k, v in sorted(Counter(c.status.value for c in cases).items()))
    )
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    if args.match == "region" and args.tolerance is not None:
        print("error: --tolerance only applies with --match line", file=sys.stderr)
        return 1
    try:
        data = json.loads(args.findings.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read findings file: {exc}", file=sys.stderr)
        return 1
    problems = validate_json(data, "findings.schema.json", str(args.findings))
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    try:
        cases = require_valid_corpus(_corpus(args))
        result = score(
            cases,
            _report_from_json(data),
            matching=args.match,
            line_tolerance=args.tolerance or 0,
        )
    except CorpusError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    except ScoringInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(to_json(result), indent=2) if args.format == "json" else to_text(result))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        cases = require_valid_corpus(_corpus(args))
    except CorpusError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    if args.cases:
        wanted = set(args.cases)
        unknown = sorted(wanted - {c.id for c in cases})
        if unknown:
            print(f"error: unknown case ids: {', '.join(unknown)}", file=sys.stderr)
            return 1
        cases = [c for c in cases if c.id in wanted]

    options: dict[str, str] = {}
    for item in args.config:
        key, sep, value = item.partition("=")
        if not sep or not key or not value:
            print(f"error: --config expects KEY=VALUE, got '{item}'", file=sys.stderr)
            return 1
        options[key] = value
    try:
        adapter = get_adapter(args.tool, options)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        result = run_scanner(adapter, cases, args.out, timeout=args.timeout)
    except (ScannerNotFoundError, ScannerVersionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    findings_path = args.out / adapter.label / "findings.json"
    findings_path.write_text(
        json.dumps(findings_document(result.report), indent=2) + "\n", encoding="utf-8"
    )
    report = result.report
    scope = ", ".join(sorted(c.value for c in report.scope))
    print(f"{report.tool} {report.version}: ran {len(report.cases_run)} of {len(cases)} case(s)")
    print(f"configuration: {report.configuration or 'not recorded'}")
    print(f"scope (classes with a reviewed rule mapping): {scope}")
    print(f"findings: {findings_path}")
    print(f"raw output: {result.raw_dir}")
    if result.unmapped_rules:
        print("rules reported but not mapped to a class (excluded from scoring, not hidden):")
        for rule, case_ids in sorted(result.unmapped_rules.items()):
            print(f"  {rule}: {len(case_ids)} case(s)")
    if result.locationless:
        print(f"results without a usable file and line: {len(result.locationless)}")
    for case_id, reason in sorted(result.failures.items()):
        print(f"FAILED {case_id}: {reason}", file=sys.stderr)
    if result.failures:
        print(
            f"{len(result.failures)} case(s) did not run and are excluded from scoring.",
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="actionsbench", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"actionsbench {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate every case in the corpus")
    validate.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="corpus directory (default: ./corpus/cases, else the bundled corpus)",
    )
    validate.set_defaults(func=_cmd_validate)

    stats = sub.add_parser("stats", help="count cases per weakness class")
    stats.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="corpus directory (default: ./corpus/cases, else the bundled corpus)",
    )
    stats.set_defaults(func=_cmd_stats)

    run = sub.add_parser(
        "run", help="run a scanner on isolated copies of the cases and write a findings file"
    )
    run.add_argument("--tool", required=True, choices=sorted(ADAPTERS))
    run.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="corpus directory (default: ./corpus/cases, else the bundled corpus)",
    )
    run.add_argument("--out", type=Path, default=Path("results"))
    run.add_argument("--cases", nargs="+", metavar="ID", help="only run these case ids")
    run.add_argument(
        "--config",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="tool setting, repeatable (zizmor: persona=regular|pedantic|auditor)",
    )
    run.add_argument("--timeout", type=float, default=120.0, help="seconds per case")
    run.set_defaults(func=_cmd_run)

    scoring = sub.add_parser("score", help="score a normalized findings file against the corpus")
    scoring.add_argument("findings", type=Path, help="JSON file matching findings.schema.json")
    scoring.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="corpus directory (default: ./corpus/cases, else the bundled corpus)",
    )
    scoring.add_argument(
        "--match",
        choices=["region", "line"],
        default="region",
        help="region (default): same step, job or top-level key; line: exact line, see --tolerance",
    )
    scoring.add_argument(
        "--tolerance",
        type=int,
        default=None,
        help="allowed line distance; only valid with --match line (default 0)",
    )
    scoring.add_argument("--format", choices=["text", "json"], default="text")
    scoring.set_defaults(func=_cmd_score)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code: int = args.func(args)
    return code
