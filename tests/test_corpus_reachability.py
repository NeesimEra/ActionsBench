"""Static regressions for two audited execution-path defects; never run the fixtures."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

import yaml

from actionsbench.corpus import require_valid_corpus
from actionsbench.runner import materialize_case

CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"


def workflow(root: Path, name: str) -> dict[str, Any]:
    document: dict[str, Any] = yaml.safe_load(
        (root / ".github" / "workflows" / name).read_text(encoding="utf-8")
    )
    return document


def test_composite_caller_provisions_the_local_action_before_using_it(real_corpus: Path) -> None:
    root = real_corpus / "AB-INJ-0007"
    steps = workflow(root, "caller.yml")["jobs"]["greet"]["steps"]
    checkout, call = steps
    assert checkout["uses"] == CHECKOUT
    assert checkout["with"]["persist-credentials"] is False
    assert "if" not in checkout
    assert "path" not in checkout["with"]
    assert "sparse-checkout" not in checkout["with"]
    assert call["with"]["title"] == "${{ github.event.pull_request.title }}"
    action_path = root / call["uses"] / "action.yml"
    assert action_path.is_file()
    action = yaml.safe_load(action_path.read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    assert action["runs"]["steps"][0]["run"] == "echo ${{ inputs.title }}"


def test_privileged_checkout_explicitly_opts_out_of_the_pinned_fork_guard(
    real_corpus: Path,
) -> None:
    document = workflow(real_corpus / "AB-TRG-0001", "pwn-request.yml")
    checkout, build = document["jobs"]["build"]["steps"]
    assert checkout["uses"] == CHECKOUT
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha }}"
    assert checkout["with"]["allow-unsafe-pr-checkout"] is True
    assert checkout["with"]["persist-credentials"] is False
    assert "if" not in checkout
    assert "if" not in build
    assert document["permissions"] == {"contents": "read"}


def test_privileged_build_target_exists_in_the_isolated_case(
    real_corpus: Path, tmp_path: Path
) -> None:
    case = next(c for c in require_valid_corpus(real_corpus) if c.id == "AB-TRG-0001")
    scan_dir = materialize_case(case, tmp_path)
    build = workflow(scan_dir, "pwn-request.yml")["jobs"]["build"]["steps"][-1]
    command = shlex.split(build["run"])
    assert command == ["make", "-f", ".github/build.mk", "build"]
    recipe = scan_dir / command[2]
    assert recipe.read_bytes() == (case.root / command[2]).read_bytes()
    assert 'build:\n\t@echo "building the checked-out revision"' in recipe.read_text()
