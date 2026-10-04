"""Load and validate the labeled corpus.

A case is a directory that doubles as a fake repository root: workflow and action files
live under `.github/` exactly as a scanner expects to find them, and the label metadata
sits beside them in `case.yaml`. Validation has two layers:

1. The JSON Schema in `schemas/case.schema.json` (shape, enums, patterns).
2. Semantic rules the schema cannot express (the file really exists, the labeled line
   really contains the evidence, the ID matches the directory and the primary class, ...).

Validation reports every problem it finds instead of stopping at the first one, so a
contributor sees the whole list in one CI run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from actionsbench.models import Case, ExpectedFinding, Provenance, Status
from actionsbench.taxonomy import CLASS_CODES, NEGATIVE_CODE, WeaknessClass

CASE_FILE = "case.yaml"


@dataclass(frozen=True, slots=True)
class Problem:
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


class CorpusError(Exception):
    def __init__(self, problems: list[Problem]) -> None:
        super().__init__(f"{len(problems)} corpus problem(s)")
        self.problems = problems


@cache
def load_schema(name: str) -> dict[str, Any]:
    """Load a bundled JSON Schema by file name (for example `case.schema.json`)."""
    text = files("actionsbench").joinpath("schemas", name).read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(text)
    return schema


def validate_json(instance: object, schema_name: str, location: str) -> list[Problem]:
    validator = Draft202012Validator(load_schema(schema_name))
    problems: list[Problem] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(part) for part in error.absolute_path) or "(root)"
        problems.append(Problem(location, f"{path}: {error.message}"))
    return problems


def _primary_code(expected: list[dict[str, Any]], is_negative: bool) -> str | None:
    if is_negative:
        return NEGATIVE_CODE
    if not expected:
        return None
    return CLASS_CODES[WeaknessClass(expected[0]["weakness_class"])]


def _check_expected_file(case_dir: Path, item: dict[str, Any], location: str) -> list[Problem]:
    rel = str(item["file"])
    root = case_dir.resolve()
    target = (root / rel).resolve()
    # Contributors submit case files through pull requests and CI runs this validator,
    # so a label must never be able to point outside its own case directory.
    if Path(rel).is_absolute() or not target.is_relative_to(root):
        return [Problem(location, f"expected file '{rel}' escapes the case directory")]
    if not target.is_file():
        return [Problem(location, f"expected file '{rel}' does not exist")]
    lines = target.read_text(encoding="utf-8").splitlines()
    line_no = int(item["line"])
    if line_no > len(lines):
        return [
            Problem(location, f"{rel}:{line_no} is past the end of the file ({len(lines)} lines)")
        ]
    if str(item["evidence"]) not in lines[line_no - 1]:
        return [
            Problem(location, f"{rel}:{line_no} does not contain evidence {item['evidence']!r}")
        ]
    return []


def _check_semantics(case_dir: Path, raw: dict[str, Any]) -> list[Problem]:
    location = f"{case_dir.name}/{CASE_FILE}"
    problems: list[Problem] = []
    case_id = str(raw["id"])
    expected: list[dict[str, Any]] = raw["expected"]
    is_negative = bool(raw["is_negative"])

    if case_id != case_dir.name:
        problems.append(Problem(location, f"id '{case_id}' does not match directory name"))

    if is_negative and expected:
        problems.append(Problem(location, "a negative case must not list expected findings"))
    if not is_negative and not expected:
        problems.append(Problem(location, "a positive case needs at least one expected finding"))

    code = _primary_code(expected, is_negative)
    if code is not None and case_id.split("-")[1] != code:
        problems.append(
            Problem(
                location, f"id prefix must be '{code}' (the case's primary class), got '{case_id}'"
            )
        )

    if raw["status"] == Status.AGREED and (
        raw["reviewer"] is None or raw["reviewer"] == raw["author"]
    ):
        problems.append(
            Problem(location, "status 'agreed' needs a reviewer different from the author")
        )

    if not (case_dir / ".github").is_dir():
        problems.append(Problem(location, "case has no .github/ directory to scan"))

    for item in expected:
        problems.extend(_check_expected_file(case_dir, item, location))
    return problems


def _build_case(case_dir: Path, raw: dict[str, Any]) -> Case:
    return Case(
        id=raw["id"],
        root=case_dir,
        title=raw["title"],
        is_negative=raw["is_negative"],
        expected=tuple(
            ExpectedFinding(
                weakness_class=WeaknessClass(item["weakness_class"]),
                file=item["file"],
                line=item["line"],
                evidence=item["evidence"],
            )
            for item in raw["expected"]
        ),
        rationale=raw["rationale"],
        references=tuple(raw["references"]),
        provenance=Provenance(raw["provenance"]),
        status=Status(raw["status"]),
        author=raw["author"],
        reviewer=raw["reviewer"],
        added_in=raw["added_in"],
        notes=raw.get("notes"),
    )


def load_case(case_dir: Path) -> tuple[Case | None, list[Problem]]:
    """Load one case directory. Returns (case, problems); case is None if any problem exists."""
    location = f"{case_dir.name}/{CASE_FILE}"
    path = case_dir / CASE_FILE
    if not path.is_file():
        return None, [Problem(location, "missing case.yaml")]
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [Problem(location, f"invalid YAML: {exc}")]

    problems = validate_json(raw, "case.schema.json", location)
    if problems:
        return None, problems
    problems = _check_semantics(case_dir, raw)
    if problems:
        return None, problems
    return _build_case(case_dir, raw), []


def load_corpus(root: Path) -> tuple[list[Case], list[Problem]]:
    """Load every case under `root`. Cases that fail are reported, not skipped silently."""
    if not root.is_dir():
        return [], [Problem(str(root), "corpus directory does not exist")]

    # IDs are unique because load_case requires id == directory name and directory names
    # are unique, so no separate duplicate check is needed.
    cases: list[Case] = []
    problems: list[Problem] = []
    for case_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        case, case_problems = load_case(case_dir)
        problems.extend(case_problems)
        if case is not None:
            cases.append(case)
    return cases, problems


def require_valid_corpus(root: Path) -> list[Case]:
    cases, problems = load_corpus(root)
    if problems:
        raise CorpusError(problems)
    return cases
