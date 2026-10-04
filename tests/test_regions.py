from __future__ import annotations

from pathlib import Path

import pytest

from actionsbench.regions import PREAMBLE, RegionIndex

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "cases"

WORKFLOW = """\
# a leading comment
name: Example
on:
  pull_request:
  push:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: First
        run: echo one

      - name: Second
        uses: actions/checkout@v4
        with:
          persist-credentials: false
    timeout-minutes: 5
  deploy:
    uses: example/repo/.github/workflows/x.yml@v1
    secrets: inherit
"""


def index(text: str = WORKFLOW) -> RegionIndex:
    built = RegionIndex.from_text(text)
    assert built is not None
    return built


def test_comment_before_the_first_key_is_the_preamble() -> None:
    assert index().region(1) == PREAMBLE


def test_every_line_of_a_top_level_key_is_one_region() -> None:
    idx = index()
    assert idx.region(3) == idx.region(4) == idx.region(5) == ("on",)
    assert idx.region(7) == idx.region(8) == ("permissions",)


def test_different_top_level_keys_are_different_regions() -> None:
    idx = index()
    assert idx.region(4) != idx.region(8)


def test_lines_of_one_step_share_a_region_and_steps_differ() -> None:
    idx = index()
    assert idx.region(14) == idx.region(15) == ("jobs", "build", "steps", 0)
    assert idx.region(17) == idx.region(18) == idx.region(19) == idx.region(20)
    assert idx.region(17) == ("jobs", "build", "steps", 1)
    assert idx.region(15) != idx.region(18)


def test_blank_line_between_steps_belongs_to_the_previous_step() -> None:
    # A blank line has no node of its own; it is attributed to the step that precedes it.
    assert index().region(16) == ("jobs", "build", "steps", 0)


def test_job_keys_outside_the_steps_are_the_job_region() -> None:
    idx = index()
    assert idx.region(11) == ("jobs", "build")  # the job key line
    assert idx.region(12) == ("jobs", "build")  # runs-on
    assert idx.region(13) == ("jobs", "build")  # the `steps:` key line itself


def test_a_key_written_after_steps_is_not_part_of_the_last_step() -> None:
    assert index().region(21) == ("jobs", "build")  # timeout-minutes


def test_the_jobs_key_line_itself_is_the_jobs_region() -> None:
    assert index().region(10) == ("jobs",)


def test_a_job_without_steps_is_one_region() -> None:
    idx = index()
    assert idx.region(23) == idx.region(24) == ("jobs", "deploy")
    assert idx.region(23) != idx.region(12)


def test_composite_action_steps_are_regions_even_when_the_dash_is_at_the_parent_indent() -> None:
    text = (
        "name: Greet\n"  # 1
        "runs:\n"  # 2
        "  using: composite\n"  # 3
        "  steps:\n"  # 4
        "  - run: echo one\n"  # 5
        "    shell: bash\n"  # 6
        "  - run: echo two\n"  # 7
        "    shell: bash\n"  # 8
    )
    idx = index(text)
    assert idx.region(3) == ("runs",)
    assert idx.region(5) == idx.region(6) == ("runs", "steps", 0)
    assert idx.region(7) == idx.region(8) == ("runs", "steps", 1)


def test_a_line_past_the_end_of_the_file_is_the_last_region() -> None:
    assert index().region(500) == ("jobs", "deploy")


@pytest.mark.parametrize(
    "text",
    ["", "just a scalar", "- a\n- list\n", "a: [unclosed\n", "---\na: 1\n---\nb: 2\n"],
)
def test_files_that_are_not_a_single_yaml_mapping_have_no_index(text: str) -> None:
    assert RegionIndex.from_text(text) is None


def _region_pair(case: str, workflow: str, label_line: int, tool_line: int) -> bool:
    text = (CORPUS / case / ".github" / workflow).read_text(encoding="utf-8")
    idx = index(text)
    return idx.region(label_line) == idx.region(tool_line)


@pytest.mark.parametrize(
    ("case", "file", "label_line", "tool_line"),
    [
        # zizmor reports the `on:` line; the label is the trigger line under it.
        ("AB-TRG-0001", "workflows/pwn-request.yml", 3, 2),
        # zizmor reports the call's `uses:` line; the label is `secrets: inherit`.
        ("AB-SEC-0001", "workflows/inherit.yml", 11, 10),
        # zizmor reports the step header; the label is the step's `uses:` line.
        ("AB-ART-0001", "workflows/artipacked.yml", 13, 12),
        # actionlint reports the `script:` key; the label is the line inside the script.
        ("AB-INJ-0006", "workflows/github-script.yml", 16, 15),
    ],
)
def test_the_four_observed_anchoring_differences_are_all_the_same_region(
    case: str, file: str, label_line: int, tool_line: int
) -> None:
    assert _region_pair(case, file, label_line, tool_line)


@pytest.mark.parametrize(
    ("case", "file", "label_line", "other_line"),
    [
        # the checkout step versus the upload step that follows it
        ("AB-ART-0001", "workflows/artipacked.yml", 13, 15),
        # the trigger versus the permissions block
        ("AB-TRG-0001", "workflows/pwn-request.yml", 3, 6),
        # the step's `uses:` versus the job it lives in
        ("AB-PIN-0001", "workflows/tag-ref.yml", 13, 10),
    ],
)
def test_neighbouring_constructs_are_different_regions(
    case: str, file: str, label_line: int, other_line: int
) -> None:
    assert not _region_pair(case, file, label_line, other_line)
