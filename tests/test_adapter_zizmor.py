from __future__ import annotations

import json
from pathlib import Path

import pytest

from actionsbench.adapters import ADAPTERS, get_adapter
from actionsbench.adapters.base import ScannerOutputError
from actionsbench.adapters.zizmor import PINNED_VERSION, RULE_MAP, SCOPE, ZizmorAdapter
from actionsbench.taxonomy import WeaknessClass

# Trimmed from zizmor 1.30.1 output on an isolated copy of AB-INJ-0007.
REAL_SHAPE = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {"driver": {"name": "zizmor", "version": "1.30.1"}},
            "results": [
                {
                    "ruleId": "zizmor/template-injection",
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": ".github/actions/greet/action.yml"},
                                "region": {"startLine": 10},
                            }
                        }
                    ],
                },
                {
                    "ruleId": "zizmor/self-repository",
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": ".github/workflows/caller.yml"},
                                "region": {"startLine": 13},
                            }
                        }
                    ],
                },
            ],
        }
    ],
}


def test_command_pins_the_version_and_disables_online_audits(tmp_path: Path) -> None:
    command = ZizmorAdapter().command(tmp_path)
    assert f"zizmor=={PINNED_VERSION}" in command
    assert command[-3:] == ["sarif", "--no-online-audits", str(tmp_path)]
    assert "--format" in command


def test_launcher_can_be_overridden_for_a_local_install(tmp_path: Path) -> None:
    assert ZizmorAdapter(launcher=["zizmor"]).command(tmp_path)[0] == "zizmor"


def test_label_names_tool_version_and_persona() -> None:
    assert ZizmorAdapter().label == f"zizmor-{PINNED_VERSION}-regular"
    assert ZizmorAdapter(persona="auditor").label == f"zizmor-{PINNED_VERSION}-auditor"


def test_persona_is_always_passed_explicitly(tmp_path: Path) -> None:
    # Never rely on zizmor's own default: the persona changes its verdict and must be recorded.
    assert "--persona=regular" in ZizmorAdapter().command(tmp_path)
    assert "--persona=pedantic" in ZizmorAdapter(persona="pedantic").command(tmp_path)


def test_configuration_states_every_setting_that_changes_the_verdict() -> None:
    assert ZizmorAdapter().configuration == "persona=regular; online-audits=off"
    assert ZizmorAdapter(persona="auditor").configuration == "persona=auditor; online-audits=off"


def test_unknown_persona_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown zizmor persona"):
        ZizmorAdapter(persona="paranoid")


def test_options_are_validated() -> None:
    assert ZizmorAdapter.from_options({"persona": "pedantic"}).label.endswith("-pedantic")
    assert ZizmorAdapter.from_options({}).label.endswith("-regular")
    with pytest.raises(ValueError, match="unknown option"):
        ZizmorAdapter.from_options({"personas": "regular"})


def test_scope_is_exactly_the_classes_with_a_reviewed_mapping() -> None:
    assert SCOPE == frozenset(RULE_MAP.values()) == frozenset({WeaknessClass.INJECTION})
    assert ZizmorAdapter().scope == SCOPE


def test_every_mapped_rule_id_uses_zizmors_prefix() -> None:
    assert all(rule.startswith("zizmor/") for rule in RULE_MAP)


def test_parse_maps_reviewed_rules_and_surfaces_the_rest(tmp_path: Path) -> None:
    output = ZizmorAdapter().parse(json.dumps(REAL_SHAPE), case_id="AB-INJ-0007", scan_dir=tmp_path)
    assert [(f.file, f.line) for f in output.findings] == [(".github/actions/greet/action.yml", 10)]
    assert output.unmapped_rule_ids == {"zizmor/self-repository"}
    assert output.reported_version == "1.30.1"


@pytest.mark.parametrize("stdout", ["not json", "{}", '{"runs": 5}', "[]"])
def test_unreadable_output_raises_scanner_output_error(stdout: str, tmp_path: Path) -> None:
    with pytest.raises(ScannerOutputError):
        ZizmorAdapter().parse(stdout, case_id="AB-INJ-0001", scan_dir=tmp_path)


def test_run_with_no_results_is_valid() -> None:
    empty = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "zizmor"}}, "results": []}]}
    output = ZizmorAdapter().parse(json.dumps(empty), case_id="AB-NEG-0001", scan_dir=Path("."))
    assert output.findings == []
    assert output.reported_version is None


def test_registry() -> None:
    assert set(ADAPTERS) == {"actionlint", "zizmor"}
    assert isinstance(get_adapter("zizmor"), ZizmorAdapter)
    assert get_adapter("zizmor", {"persona": "auditor"}).label.endswith("-auditor")
    with pytest.raises(ValueError, match="unknown scanner"):
        get_adapter("nope")
