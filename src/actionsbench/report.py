"""Render a ScoreResult as machine-readable JSON or a plain-text table."""

from __future__ import annotations

from typing import Any

from actionsbench.scoring import ClassScore, ScoreResult
from actionsbench.taxonomy import WeaknessClass


def _ratio(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _class_row(cls: WeaknessClass, score: ClassScore) -> dict[str, Any]:
    return {
        "class": cls.value,
        "in_scope": score.in_scope,
        "tp": score.tp,
        "fp": score.fp,
        "fn": score.fn,
        "precision": score.precision,
        "recall": score.recall,
        "f1": score.f1,
        "uncovered": score.uncovered,
        "out_of_scope_findings": score.out_of_scope_findings,
    }


def to_json(result: ScoreResult) -> dict[str, Any]:
    return {
        "tool": result.tool,
        "version": result.version,
        "line_tolerance": result.line_tolerance,
        "cases_scored": result.cases_scored,
        "not_run": result.not_run,
        "classes": [_class_row(cls, result.per_class[cls]) for cls in WeaknessClass],
        "mismatches": [
            {
                "case_id": m.case_id,
                "missed": [
                    {"weakness_class": e.weakness_class.value, "file": e.file, "line": e.line}
                    for e in m.missed
                ],
                "extra": [
                    {
                        "weakness_class": f.weakness_class.value,
                        "file": f.file,
                        "line": f.line,
                        "rule_id": f.rule_id,
                    }
                    for f in m.extra
                ],
            }
            for m in result.mismatches
        ],
    }


def to_text(result: ScoreResult) -> str:
    lines = [
        f"{result.tool} {result.version}  |  cases scored: {result.cases_scored}  |  "
        f"line tolerance: {result.line_tolerance}",
        "",
        f"{'class':<28}{'scope':<7}{'TP':>4}{'FP':>4}{'FN':>4}{'prec':>7}{'rec':>7}{'uncov':>7}",
    ]
    for cls in WeaknessClass:
        s = result.per_class[cls]
        lines.append(
            f"{cls.value:<28}{('yes' if s.in_scope else 'no'):<7}{s.tp:>4}{s.fp:>4}{s.fn:>4}"
            f"{_ratio(s.precision):>7}{_ratio(s.recall):>7}{s.uncovered:>7}"
        )
    if result.not_run:
        lines += ["", f"not run (excluded, not counted as clean): {', '.join(result.not_run)}"]
    if result.mismatches:
        lines += ["", "cases where the tool and the label disagree:"]
        for m in result.mismatches:
            lines.append(f"  {m.case_id}: {len(m.missed)} missed, {len(m.extra)} extra")
    return "\n".join(lines)
