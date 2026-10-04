"""Map a line of a workflow or action file to the construct it belongs to.

Scanners do not agree on which line of a construct to report. Observed on the corpus: zizmor
reports a privileged trigger at the `on:` line, a reusable-workflow call at its `uses:` line and
a step at its header, while actionlint reports a multi-line script at the `script:` key. Every one
of those is a different line of the same construct, so matching by "within N lines" is the wrong
question. The right one, and the PRD's wording, is "same step".

A *region* is the smallest of these that contains a line:

* a step: `("jobs", <job id>, "steps", <index>)`, or `("runs", "steps", <index>)` in a composite
  action;
* a job outside its steps: `("jobs", <job id>)`, which also covers a reusable-workflow call such as
  `uses:` plus `secrets:` where there are no steps;
* any other top-level key, such as `on` or `permissions`: `(<key>,)`;
* a line before the first key (comments, blank lines): `("",)`.

Boundaries come from the start positions of YAML nodes, not from indentation, so block lists whose
dash sits at the parent's indentation, comments, and blank lines are handled by the parser.

If a file cannot be parsed as a single YAML mapping, `RegionIndex.from_text` returns None and the
caller must fall back to exact line comparison. Nothing is guessed.
"""

from __future__ import annotations

import bisect
from collections.abc import Sequence
from dataclasses import dataclass

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

Region = tuple[str | int, ...]

PREAMBLE: Region = ("",)


@dataclass(frozen=True, slots=True)
class _Entry:
    name: str
    start: int  # 1-based line on which the key starts
    value: Node


def _entries(node: Node) -> list[_Entry]:
    if not isinstance(node, MappingNode):
        return []
    return [
        _Entry(str(key.value), key.start_mark.line + 1, value)
        for key, value in node.value
        if isinstance(key, ScalarNode)
    ]


def _last_at_or_before(starts: Sequence[int], line: int) -> int | None:
    index = bisect.bisect_right(starts, line) - 1
    return index if index >= 0 else None


def _step_index(container: Node, line: int, end: int | None) -> int | None:
    """Index of the step containing `line` inside a mapping that has a `steps` list, or None.

    `end` is the exclusive line at which the container itself ends (the next sibling's start).
    A line after the last step but before the next key of the same mapping, for example a
    `timeout-minutes` written below `steps`, is not part of the last step.
    """
    entries = _entries(container)
    steps = next((e for e in entries if e.name == "steps"), None)
    if steps is None or not isinstance(steps.value, SequenceNode) or not steps.value.value:
        return None

    item_starts = [item.start_mark.line + 1 for item in steps.value.value]
    limits = [e.start for e in entries if e.start > steps.start]
    if end is not None:
        limits.append(end)
    if line < item_starts[0] or (limits and line >= min(limits)):
        return None
    return _last_at_or_before(item_starts, line)


class RegionIndex:
    """The regions of one file, built once and queried by line number."""

    def __init__(self, top: list[_Entry]) -> None:
        self._top = top
        self._top_starts = [e.start for e in top]

    @classmethod
    def from_text(cls, text: str) -> RegionIndex | None:
        try:
            root = yaml.compose(text)
        except yaml.YAMLError:
            return None
        if not isinstance(root, MappingNode):
            return None
        return cls(_entries(root))

    def region(self, line: int) -> Region:
        top_index = _last_at_or_before(self._top_starts, line)
        if top_index is None:
            return PREAMBLE
        top = self._top[top_index]
        next_top = (
            self._top_starts[top_index + 1] if top_index + 1 < len(self._top_starts) else None
        )

        if top.name == "jobs":
            return self._in_jobs(top, line, next_top)
        if top.name == "runs":
            step = _step_index(top.value, line, next_top)
            return ("runs", "steps", step) if step is not None else ("runs",)
        return (top.name,)

    @staticmethod
    def _in_jobs(top: _Entry, line: int, next_top: int | None) -> Region:
        jobs = _entries(top.value)
        starts = [j.start for j in jobs]
        job_index = _last_at_or_before(starts, line)
        if job_index is None:
            return ("jobs",)
        job = jobs[job_index]
        job_end = starts[job_index + 1] if job_index + 1 < len(starts) else next_top
        step = _step_index(job.value, line, job_end)
        if step is None:
            return ("jobs", job.name)
        return ("jobs", job.name, "steps", step)
