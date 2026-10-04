from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from actionsbench.adapters import get_adapter
from actionsbench.adapters.actionlint import (
    ENV_VAR,
    PINNED_VERSION,
    SCOPE,
    UNTRUSTED_RULE_ID,
    ActionlintAdapter,
    classify,
)
from actionsbench.adapters.base import ScannerNotFoundError, ScannerOutput, ScannerOutputError
from actionsbench.taxonomy import WeaknessClass

REPO_ROOT = Path(__file__).resolve().parents[1]

# Trimmed from actionlint 1.7.12 output (`-format '{{json .}}'`) on isolated copies of
# AB-INJ-0001, observed 2026-10-04.
UNTRUSTED = {
    "message": (
        '"github.event.pull_request.title" is potentially untrusted. avoid using it directly in '
        "inline scripts. instead, pass it through an environment variable. see "
        "https://docs.github.com/en/actions/reference/security/secure-use"
        "#good-practices-for-mitigating-script-injection-attacks for more details"
    ),
    "filepath": ".github/workflows/format-wrapping.yml",
    "line": 13,
    "column": 46,
    "kind": "expression",
    "snippet": "        run: echo ${{ format('Title is {0}', github.event.pull_request.title) }}\n",
    "end_column": 77,
}


def parse(results: object, tmp_path: Path) -> ScannerOutput:
    return ActionlintAdapter(launcher="actionlint").parse(
        json.dumps(results), case_id="AB-INJ-0001", scan_dir=tmp_path
    )


def test_untrusted_input_is_mapped_to_injection(tmp_path: Path) -> None:
    output = parse([UNTRUSTED], tmp_path)
    assert [(f.weakness_class, f.file, f.line, f.rule_id) for f in output.findings] == [
        (
            WeaknessClass.INJECTION,
            ".github/workflows/format-wrapping.yml",
            13,
            UNTRUSTED_RULE_ID,
        )
    ]
    assert output.unmapped_rule_ids == set()


def test_other_expression_results_are_not_guessed_at(tmp_path: Path) -> None:
    other = {**UNTRUSTED, "message": 'property "foo" is not defined in object type {}'}
    output = parse([other], tmp_path)
    assert output.findings == []
    assert output.unmapped_rule_ids == {"actionlint/expression"}


def test_other_kinds_are_surfaced_as_unmapped(tmp_path: Path) -> None:
    shell = {**UNTRUSTED, "kind": "shellcheck", "message": "SC2086: quote this"}
    output = parse([shell, UNTRUSTED], tmp_path)
    assert len(output.findings) == 1
    assert output.unmapped_rule_ids == {"actionlint/shellcheck"}


def test_message_wording_must_match_exactly_to_count_as_injection() -> None:
    assert classify("expression", '"x" is potentially untrusted. avoid it')[1] is not None
    assert classify("expression", 'something "x" is potentially untrusted.')[1] is None
    assert classify("syntax-check", '"x" is potentially untrusted. avoid it')[1] is None


def test_result_without_a_line_is_reported_as_locationless(tmp_path: Path) -> None:
    broken = {k: v for k, v in UNTRUSTED.items() if k != "line"}
    output = parse([broken], tmp_path)
    assert output.findings == []
    assert output.locationless == [UNTRUSTED_RULE_ID]


@pytest.mark.parametrize("stdout", ["[]", "null"])
def test_clean_run_has_no_findings(stdout: str, tmp_path: Path) -> None:
    output = ActionlintAdapter(launcher="x").parse(stdout, case_id="AB-NEG-0001", scan_dir=tmp_path)
    assert output.findings == []
    assert output.reported_version is None  # the version comes from probe_version instead


@pytest.mark.parametrize("stdout", ["not json", "{}", '"text"', "[1]"])
def test_unreadable_output_raises(stdout: str, tmp_path: Path) -> None:
    with pytest.raises(ScannerOutputError):
        ActionlintAdapter(launcher="x").parse(stdout, case_id="AB-INJ-0001", scan_dir=tmp_path)


def test_command_is_deterministic(tmp_path: Path) -> None:
    command = ActionlintAdapter(launcher="actionlint").command(tmp_path)
    assert command == ["actionlint", "-format", "{{json .}}", "-shellcheck=", "-pyflakes="]


def test_prepare_adds_the_project_marker_to_the_copy_only(tmp_path: Path) -> None:
    ActionlintAdapter(launcher="x").prepare(tmp_path)
    assert (tmp_path / ".git").is_dir()
    ActionlintAdapter(launcher="x").prepare(tmp_path)  # idempotent


def test_exit_code_3_is_not_an_accepted_outcome() -> None:
    assert ActionlintAdapter(launcher="x").ok_exit_codes == frozenset({0, 1})


def test_scope_is_injection_only() -> None:
    assert frozenset({WeaknessClass.INJECTION}) == SCOPE
    assert ActionlintAdapter(launcher="x").scope == SCOPE


def test_launcher_resolution_prefers_the_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "/somewhere/actionlint")
    assert ActionlintAdapter().command(Path("."))[0] == "/somewhere/actionlint"


def test_launcher_resolution_finds_the_installed_copy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    binary = tmp_path / ".tools" / f"actionlint-{PINNED_VERSION}" / "actionlint"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n")
    monkeypatch.chdir(tmp_path)
    assert ActionlintAdapter().command(Path("."))[0] == str(binary)


def test_launcher_falls_back_to_path_lookup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    assert ActionlintAdapter().command(Path("."))[0] == "actionlint"


def test_probe_version_reads_the_first_line(tmp_path: Path) -> None:
    fake = tmp_path / "actionlint"
    fake.write_text("#!/bin/sh\nprintf '1.7.12\\ninstalled by downloading from release page\\n'\n")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    assert ActionlintAdapter(launcher=str(fake)).probe_version() == "1.7.12"


def test_probe_version_reports_a_missing_binary_with_a_hint() -> None:
    with pytest.raises(ScannerNotFoundError, match=r"install-actionlint\.sh"):
        ActionlintAdapter(launcher="no-such-actionlint-binary-xyz").probe_version()


def test_installer_script_pins_the_same_version_as_the_adapter() -> None:
    script = (REPO_ROOT / "scripts" / "install-actionlint.sh").read_text(encoding="utf-8")
    assert f'DEFAULT_VERSION="{PINNED_VERSION}"' in script


def test_label_and_registry() -> None:
    assert ActionlintAdapter(launcher="x").label == f"actionlint-{PINNED_VERSION}"
    assert isinstance(get_adapter("actionlint"), ActionlintAdapter)
