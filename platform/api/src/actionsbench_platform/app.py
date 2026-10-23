"""The P0 platform API: corpus and per-class results, read-only (ADR 0007).

Security posture of this milestone, enforceable by reading this file:

* No command execution, no scanners, no corpus code is ever run anywhere in the package.
* Case files are served as text via `data.PlatformData.file_text`, which refuses paths
  that escape the case directory.
* Findings documents are rejected unless `findings.schema.json` accepts them, and results
  are per-class numbers only — the platform never computes or displays an overall score.

This API is JSON-only; rendering lives in the Next.js app under `platform/web`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import uvicorn
from actionsbench import __version__
from actionsbench.models import Case
from actionsbench.scoring import ScoreResult, ScoringInputError
from actionsbench.taxonomy import WeaknessClass
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from .data import (
    MAX_FILE_BYTES,
    FindingsDocumentError,
    PlatformData,
    ReloadError,
    read_findings,
    score_findings,
)

RESULTS_DIR_DEFAULT = Path("results")


def record_link(data: PlatformData, case: Case) -> str | None:
    """API-relative link to the case's dated review record, when the file exists.

    The stored `review_record` value is like `docs/ai-label-audit-2026-10-22.md#injection`;
    the `#anchor` stays in the link (the API serves the path without it) but the existence
    check ignores it.
    """
    record = case.review_record
    if record is None:
        return None
    relative = record.removeprefix("docs/")
    if (data.repo_docs / relative.partition("#")[0]).is_file():
        return "records/" + relative
    return None


def create_app(data: PlatformData, results_dir: Path | None = None) -> FastAPI:
    results = results_dir if results_dir is not None else RESULTS_DIR_DEFAULT
    app = FastAPI(title="ActionsBench platform", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(ReloadError)
    @app.exception_handler(FindingsDocumentError)
    def refuse(_: Any, exc: ReloadError | FindingsDocumentError) -> PlainTextResponse:
        return PlainTextResponse(str(exc), status_code=404)

    @app.get("/api/summary")
    def summary() -> dict[str, Any]:
        _by_class, by_status = data.counts()
        return {
            "case_count": len(data.cases),
            "class_rows": [
                {"value": cls.value, "positives": positives, "negatives": negatives}
                for cls, positives, negatives in data.class_listing()
            ],
            "status_totals": dict(by_status),
            "provenance": label_status(data),
        }

    @app.get("/api/cases")
    def case_list() -> dict[str, Any]:
        listing = []
        for case in data.cases.values():
            listing.append(
                {
                    "id": case.id,
                    "title": case.title,
                    "is_negative": case.is_negative,
                    "classes": data.classes_of(case),
                    "status": case.status.value,
                    "added_in": case.added_in,
                }
            )
        return {"cases": listing}

    @app.get("/api/cases/{case_id}")
    def case_detail(case_id: str) -> dict[str, Any]:
        case = data.case(case_id)
        if case is None:
            raise ReloadError(f"no case {case_id}")
        return {
            "id": case.id,
            "title": case.title,
            "is_negative": case.is_negative,
            "status": case.status.value,
            "added_in": case.added_in,
            "provenance": case.provenance.value,
            "author": case.author,
            "reviewer": case.reviewer,
            "rationale": case.rationale,
            "notes": case.notes,
            "references": list(case.references),
            "expected": [
                {
                    "weakness_class": e.weakness_class.value,
                    "file": e.file,
                    "line": e.line,
                    "evidence": e.evidence,
                }
                for e in case.expected
            ],
            "files": [path.relative_to(case.root).as_posix() for path in data.case_files(case)],
            "review_record_link": record_link(data, case),
        }

    @app.get("/api/cases/{case_id}/files/{relative:path}")
    def case_file(case_id: str, relative: str) -> PlainTextResponse:
        case = data.case(case_id)
        if case is None:
            raise ReloadError(f"no case {case_id}")
        return PlainTextResponse(
            data.file_text(case, relative), media_type="text/plain; charset=utf-8"
        )

    def class_or_refuse(cls: str) -> WeaknessClass:
        try:
            value = WeaknessClass(cls)
        except ValueError:
            raise ReloadError(f"no such weakness class: {cls}") from None
        if not data.cases_in_class(value):
            raise ReloadError(f"no cases label the class {value.value}")
        return value

    @app.get("/api/classes/{cls}")
    def class_page(cls: str) -> dict[str, Any]:
        # Taken as a raw str and validated here: an enum path parameter would answer an
        # unknown class with a 422 validation error, and an unknown resource must be 404.
        value = class_or_refuse(cls)
        return {
            "value": value.value,
            "cases": [
                {
                    "id": case.id,
                    "title": case.title,
                    "is_negative": case.is_negative,
                    "status": case.status.value,
                }
                for case in data.cases_in_class(value)
            ],
        }

    @app.get("/api/results")
    def results_page() -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        problems: list[str] = []
        if results.is_dir():
            for path in sorted(results.rglob("findings.json")):
                report, errors = read_findings(path)
                if report is None:
                    problems.extend(errors)
                    continue
                try:
                    scored = score_findings(data.cases, report)
                except ScoringInputError as exc:
                    # One doc inconsistent with the corpus must not abort the whole page.
                    problems.append(f"{path.name}: {exc}")
                    continue
                entries.append(
                    {
                        "tool": report.tool,
                        "version": report.version,
                        "path": path.as_posix(),
                        "scope": ", ".join(sorted(c.value for c in report.scope)) or "(none)",
                        "configuration": report.configuration or "(not recorded)",
                        # ADR 0003: every result states the rule that produced it.
                        "matching": scored.matching,
                        "cases_scored": scored.cases_scored,
                        "case_count": len(data.cases),
                        "not_run": scored.not_run,
                        "rows": rows(scored),
                    }
                )
        else:
            problems.append(
                f"No results directory at {results} (run a scanner, or pass --results)."
            )
        # ADR 0007 reproducibility guardrail: scores name the corpus and harness versions.
        return {
            "provenance": label_status(data),
            "harness_version": __version__,
            "corpus_version": data.corpus_version,
            "problems": problems,
            "entries": entries,
        }

    @app.get("/api/records/{relative:path}")
    def record(relative: str) -> PlainTextResponse:
        """The dated review records, reachable from the links the corpus stores."""
        root = data.repo_docs.resolve()
        path = (root / relative).resolve()
        if (
            path.suffix not in {".md", ".txt"}
            or not path.is_relative_to(root)
            or not path.is_file()
        ):
            raise HTTPException(status_code=404, detail="no such record")
        # Same byte cap as case files: a record is read into memory, never streamed.
        if path.stat().st_size > MAX_FILE_BYTES:
            raise HTTPException(status_code=404, detail="record too large to show")
        return PlainTextResponse(path.read_text(encoding="utf-8", errors="replace"))

    return app


def rows(scored: ScoreResult) -> list[dict[str, Any]]:
    """One row per taxonomized class, in-scope and out-of-scope.

    Out-of-scope classes keep their counts (methodology §5: findings outside a declared
    scope are reported, never dropped silently); the UI renders them marked as such. The
    platform never aggregates the rows into a class-neutral claim.
    """
    return [
        {
            "cls": cls.value,
            "in_scope": cell.in_scope,
            "tp": cell.tp,
            "fp": cell.fp,
            "fn": cell.fn,
            "precision": pct(cell.precision),
            "recall": pct(cell.recall),
            "f1": pct(cell.f1),
            "uncovered": cell.uncovered,
            "out_of_scope_findings": cell.out_of_scope_findings,
        }
        for cls, cell in sorted(scored.per_class.items())
    ]


def pct(value: float | None) -> str:
    return f"{value * 100:.0f}%" if value is not None else "—"


def label_status(data: PlatformData) -> str:
    """One sentence about the labels behind every score, per the ADR 0007 guardrail."""
    statuses = {c.status.value for c in data.cases.values()}
    if any(status in ("agreed", "disputed") for status in statuses):
        return "Label statuses on this corpus: " + ", ".join(sorted(statuses)) + "."
    return (
        "Every label was reviewed by separate AI agent sessions (ai-reviewed); no label has "
        "independent human agreement, and results are per class only."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="actionsbench-platform-api",
        description="Serve the ActionsBench platform JSON API (ADR 0007, milestone P0).",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--corpus", type=Path, default=None, help="cases directory (default: like the CLI)"
    )
    parser.add_argument("--results", type=Path, default=None, help="results directory")
    args = parser.parse_args()
    resources = create_app(PlatformData.load(args.corpus), args.results)
    uvicorn.run(resources, host=args.host, port=args.port)


__all__ = [
    "RESULTS_DIR_DEFAULT",
    "Case",
    "create_app",
    "label_status",
    "main",
    "pct",
    "read_findings",
    "record_link",
    "rows",
    "score_findings",
]
