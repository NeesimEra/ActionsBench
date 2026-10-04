"""Command-line entry point: `actionsbench validate | stats | score`.

Running scanners is intentionally not a command yet. Per-tool adapters are an M0 task
(plan.md) and are added only once each tool's real output has been checked.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from actionsbench import __version__
from actionsbench.corpus import (
    CorpusError,
    load_corpus,
    require_valid_corpus,
    validate_json,
)
from actionsbench.models import Finding, ScannerReport
from actionsbench.report import to_json, to_text
from actionsbench.scoring import ScoringInputError, score
from actionsbench.taxonomy import WeaknessClass

DEFAULT_CORPUS = Path("corpus/cases")


def _report_from_json(data: dict[str, Any]) -> ScannerReport:
    """Build a report from data already validated against findings.schema.json."""
    return ScannerReport(
        tool=data["tool"],
        version=data["version"],
        scope=frozenset(WeaknessClass(c) for c in data["scope"]),
        cases_run=frozenset(data["cases_run"]),
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
    cases, problems = load_corpus(args.corpus)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} problem(s) found; {len(cases)} case(s) valid.", file=sys.stderr)
        return 1
    print(f"OK: {len(cases)} case(s) valid.")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    try:
        cases = require_valid_corpus(args.corpus)
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
        cases = require_valid_corpus(args.corpus)
        result = score(cases, _report_from_json(data), line_tolerance=args.tolerance)
    except CorpusError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    except ScoringInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(to_json(result), indent=2) if args.format == "json" else to_text(result))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="actionsbench", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"actionsbench {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate every case in the corpus")
    validate.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    validate.set_defaults(func=_cmd_validate)

    stats = sub.add_parser("stats", help="count cases per weakness class")
    stats.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    stats.set_defaults(func=_cmd_stats)

    scoring = sub.add_parser("score", help="score a normalized findings file against the corpus")
    scoring.add_argument("findings", type=Path, help="JSON file matching findings.schema.json")
    scoring.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    scoring.add_argument(
        "--tolerance", type=int, default=0, help="allowed line distance (default 0)"
    )
    scoring.add_argument("--format", choices=["text", "json"], default="text")
    scoring.set_defaults(func=_cmd_score)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code: int = args.func(args)
    return code
