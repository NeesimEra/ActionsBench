from __future__ import annotations

from pathlib import Path
from typing import Any

from actionsbench.sarif import parse_sarif
from actionsbench.taxonomy import WeaknessClass

RULES = {"template-injection": WeaknessClass.INJECTION}
ROOT = Path("/fake/case-root")


def doc(*results: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "x"}}, "results": list(results)}],
    }


def result(
    rule: str = "template-injection", uri: str = ".github/workflows/a.yml", line: int = 7
) -> dict[str, Any]:
    return {
        "ruleId": rule,
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": uri},
                    "region": {"startLine": line},
                }
            }
        ],
    }


def parse(document: dict[str, Any]) -> Any:
    return parse_sarif(document, case_id="AB-INJ-0001", case_root=ROOT, rule_map=RULES)


def test_maps_rule_file_and_line() -> None:
    parsed = parse(doc(result()))
    assert len(parsed.findings) == 1
    finding = parsed.findings[0]
    assert finding.weakness_class is WeaknessClass.INJECTION
    assert finding.file == ".github/workflows/a.yml"
    assert finding.line == 7
    assert finding.case_id == "AB-INJ-0001"
    assert finding.rule_id == "template-injection"


def test_absolute_file_uri_is_made_relative_to_the_case_root() -> None:
    parsed = parse(doc(result(uri="file:///fake/case-root/.github/workflows/a.yml")))
    assert parsed.findings[0].file == ".github/workflows/a.yml"


def test_percent_encoded_uri_is_decoded() -> None:
    parsed = parse(doc(result(uri=".github/workflows/my%20file.yml")))
    assert parsed.findings[0].file == ".github/workflows/my file.yml"


def test_uri_outside_the_case_root_is_kept_so_it_cannot_match_silently() -> None:
    parsed = parse(doc(result(uri="file:///elsewhere/a.yml")))
    assert parsed.findings[0].file == "/elsewhere/a.yml"


def test_rule_id_can_come_from_rule_object() -> None:
    item = result()
    del item["ruleId"]
    item["rule"] = {"id": "template-injection"}
    assert len(parse(doc(item)).findings) == 1


def test_unmapped_rules_are_reported_not_dropped_silently() -> None:
    parsed = parse(doc(result(rule="some-other-rule"), result()))
    assert len(parsed.findings) == 1
    assert parsed.unmapped_rule_ids == {"some-other-rule"}


def test_results_without_a_location_are_reported() -> None:
    parsed = parse(doc({"ruleId": "template-injection", "locations": []}))
    assert parsed.findings == []
    assert parsed.locationless == ["template-injection"]


def test_empty_document() -> None:
    parsed = parse({"version": "2.1.0", "runs": []})
    assert parsed.findings == []
    assert parsed.unmapped_rule_ids == set()


def test_real_zizmor_output_shape() -> None:
    """Trimmed from zizmor 1.30.1 output on an isolated copy of AB-INJ-0007."""
    document = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "zizmor", "version": "1.30.1"}},
                "results": [
                    {
                        "ruleId": "zizmor/template-injection",
                        "level": "error",
                        "message": {"text": "code injection via template expansion"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": ".github/actions/greet/action.yml"},
                                    "region": {"startLine": 10, "endLine": 10, "startColumn": 19},
                                }
                            }
                        ],
                    },
                    {
                        "ruleId": "zizmor/self-repository",
                        "level": "note",
                        "message": {"text": "use GitHub's dedicated self-repository syntax"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": ".github/workflows/caller.yml"},
                                    "region": {"startLine": 13, "endLine": 13},
                                }
                            }
                        ],
                    },
                ],
            }
        ],
    }
    parsed = parse_sarif(
        document,
        case_id="AB-INJ-0007",
        case_root=ROOT,
        rule_map={"zizmor/template-injection": WeaknessClass.INJECTION},
    )
    assert [(f.file, f.line) for f in parsed.findings] == [(".github/actions/greet/action.yml", 10)]
    assert parsed.unmapped_rule_ids == {"zizmor/self-repository"}
