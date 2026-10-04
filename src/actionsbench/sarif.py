"""Convert SARIF 2.1.0 output into normalized findings.

SARIF is the common export format of several scanners, so one parser serves many tools.
Each tool still needs a rule map (its rule IDs to benchmark weakness classes); that map
is the part of an adapter that needs human judgement and is added per tool.

Nothing is dropped silently: rule IDs without a mapping and results without a usable
location are returned so the caller can surface them.

The parser follows the SARIF 2.1.0 structure (runs[].results[].locations[].physicalLocation).
It has been checked against real zizmor 1.30.1 output (see tests/test_sarif.py); other tools
still have to be confirmed one at a time. Scan an isolated copy of the case so that paths
are case-relative (docs/methodology.md, section 1).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from actionsbench.models import Finding
from actionsbench.taxonomy import WeaknessClass


@dataclass(slots=True)
class SarifParseResult:
    findings: list[Finding] = field(default_factory=list)
    unmapped_rule_ids: set[str] = field(default_factory=set)
    locationless: list[str] = field(default_factory=list)


def _relative_uri(uri: str, case_root: Path) -> str:
    parsed = urlparse(uri)
    path = Path(unquote(parsed.path)) if parsed.scheme == "file" else Path(unquote(uri))
    if path.is_absolute():
        try:
            return path.resolve().relative_to(case_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _rule_id(result: Mapping[str, Any]) -> str | None:
    rule_id = result.get("ruleId")
    if isinstance(rule_id, str):
        return rule_id
    rule = result.get("rule")
    if isinstance(rule, Mapping) and isinstance(rule.get("id"), str):
        return str(rule["id"])
    return None


def parse_sarif(
    document: Mapping[str, Any],
    *,
    case_id: str,
    case_root: Path,
    rule_map: Mapping[str, WeaknessClass],
) -> SarifParseResult:
    parsed = SarifParseResult()
    for run in document.get("runs", []):
        for result in run.get("results", []):
            rule_id = _rule_id(result) or "(no rule id)"
            weakness_class = rule_map.get(rule_id)
            if weakness_class is None:
                parsed.unmapped_rule_ids.add(rule_id)
                continue

            physical = None
            for location in result.get("locations", []):
                physical = location.get("physicalLocation")
                if physical:
                    break
            uri = (physical or {}).get("artifactLocation", {}).get("uri")
            line = (physical or {}).get("region", {}).get("startLine")
            if not isinstance(uri, str) or not isinstance(line, int):
                parsed.locationless.append(rule_id)
                continue

            parsed.findings.append(
                Finding(
                    case_id=case_id,
                    weakness_class=weakness_class,
                    file=_relative_uri(uri, case_root),
                    line=line,
                    rule_id=rule_id,
                )
            )
    return parsed
