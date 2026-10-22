from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from actionsbench.adapters import get_adapter
from actionsbench.adapters.base import ScannerOutput, ScannerOutputError
from actionsbench.adapters.poutine import (
    CONFIG_FILE,
    ENV_VAR,
    PINNED_VERSION,
    RULE_MAP,
    SCOPE,
    PoutineAdapter,
)
from actionsbench.taxonomy import WeaknessClass as W

# Trimmed from real 1.1.6 output on the isolated AB-INJ-0005 workflow.
REAL_SHAPE: dict[str, Any] = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {"driver": {"name": "poutine", "semanticVersion": "1.1.6"}},
            "results": [
                {
                    "ruleId": "injection",
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": ".github/workflows/commit-author.yml"},
                                "region": {"startLine": 13, "endLine": 13},
                            }
                        }
                    ],
                }
            ],
        }
    ],
}


def parse(document: dict[str, Any]) -> ScannerOutput:
    return PoutineAdapter().parse(json.dumps(document), case_id="AB-INJ-0005", scan_dir=Path("."))


def test_real_sarif_shape_and_semantic_version() -> None:
    output = parse(REAL_SHAPE)
    assert output.reported_version == PINNED_VERSION
    assert [(f.file, f.line, f.rule_id) for f in output.findings] == [
        (".github/workflows/commit-author.yml", 13, "injection")
    ]


def test_command_and_explicit_configuration(tmp_path: Path) -> None:
    adapter = PoutineAdapter(launcher="custom-poutine")
    adapter.prepare(tmp_path)
    assert (tmp_path / CONFIG_FILE).read_text() == "{}\n"
    assert adapter.command(tmp_path) == [
        "custom-poutine",
        "analyze_local",
        ".",
        "--format",
        "sarif",
        "--config",
        str(tmp_path / CONFIG_FILE),
        "--disable-version-check",
    ]
    assert adapter.configuration == "analysis=local; config=empty; version-check=off"
    assert adapter.label == f"poutine-{PINNED_VERSION}-local"
    assert adapter.ok_exit_codes == {0}
    assert adapter.probe_version() is None


def test_prepare_leaves_case_scanner_config_untouched(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    supplied = github / "poutine.yml"
    supplied.write_text("skip:\n- rule: injection\n")
    PoutineAdapter().prepare(tmp_path)
    assert supplied.read_text() == "skip:\n- rule: injection\n"
    assert "--config" in PoutineAdapter().command(tmp_path)


def test_scope_is_only_the_reviewed_classes() -> None:
    assert (
        SCOPE
        == frozenset(RULE_MAP.values())
        == {
            W.INJECTION,
            W.SECRETS_EXPOSURE,
            W.PRIVILEGED_TRIGGER,
        }
    )


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("injection", W.INJECTION),
        ("job_all_secrets", W.SECRETS_EXPOSURE),
        ("untrusted_checkout_exec", W.PRIVILEGED_TRIGGER),
    ],
)
def test_reviewed_rules(rule: str, expected: W) -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"][0]["ruleId"] = rule
    assert parse(document).findings[0].weakness_class == expected


@pytest.mark.parametrize(
    "rule",
    [
        "pr_runs_on_self_hosted",
        "github_action_from_unverified_creator_used",
        "if_always_true",
        "unverified_script_exec",
        "known_vulnerability_in_build_component",
    ],
)
def test_unreviewed_rules_are_surfaced_not_scored(rule: str) -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"][0]["ruleId"] = rule
    output = parse(document)
    assert output.findings == []
    assert output.unmapped_rule_ids == {rule}


def test_empty_results_are_a_successful_clean_run() -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"] = []
    assert parse(document).findings == []


def test_version_drift_is_preserved_for_the_runner_to_reject() -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["tool"]["driver"]["semanticVersion"] = "9.9.9"
    assert parse(document).reported_version == "9.9.9"


def test_missing_location_is_surfaced() -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"][0]["locations"] = []
    output = parse(document)
    assert output.findings == []
    assert output.locationless == ["injection"]


@pytest.mark.parametrize("line", [0, -1, True])
def test_invalid_numeric_locations_are_rejected(line: int) -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] = (
        line
    )
    with pytest.raises(ScannerOutputError, match="positive integer"):
        parse(document)


@pytest.mark.parametrize("stdout", ["not json", "{}", "[]", '{"version":"2.1.0","runs":[]}'])
def test_malformed_documents_fail(stdout: str) -> None:
    with pytest.raises(ScannerOutputError):
        PoutineAdapter().parse(stdout, case_id="AB-INJ-0005", scan_dir=Path("."))


@pytest.mark.parametrize("part", ["semanticVersion", "name"])
def test_missing_driver_identity_fails(part: str) -> None:
    document = deepcopy(REAL_SHAPE)
    del document["runs"][0]["tool"]["driver"][part]
    with pytest.raises(ScannerOutputError):
        parse(document)


@pytest.mark.parametrize(
    "results", [None, {}, [None], [{"ruleId": "injection", "locations": [None]}]]
)
def test_malformed_results_fail(results: Any) -> None:
    document = deepcopy(REAL_SHAPE)
    document["runs"][0]["results"] = results
    with pytest.raises(ScannerOutputError):
        parse(document)


def test_launcher_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert PoutineAdapter().command(tmp_path)[0] == "poutine"
    local = tmp_path / ".tools" / f"poutine-{PINNED_VERSION}" / "poutine"
    local.parent.mkdir(parents=True)
    local.touch()
    assert PoutineAdapter().command(tmp_path)[0] == str(local)
    monkeypatch.setenv(ENV_VAR, "./custom/poutine")
    assert PoutineAdapter().command(tmp_path)[0] == str(tmp_path / "custom" / "poutine")


def test_registry_and_options() -> None:
    assert isinstance(get_adapter("poutine"), PoutineAdapter)
    with pytest.raises(ValueError, match="unknown option"):
        get_adapter("poutine", {"persona": "regular"})


def test_installer_pin_matches_adapter() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "install-poutine.sh"
    assert f'DEFAULT_VERSION="{PINNED_VERSION}"' in script.read_text()
