# ADR 0003: Per-class scoring with declared scope and explicit `cases_run`

**Status:** Accepted (2026-10-04). The line-matching tolerance is deliberately left open.

## Context

Scanners differ in what they claim to cover (actionlint is mainly a correctness linter),
they can crash or be skipped on individual cases, and the published numbers will be read
by people choosing tools. Three failure modes have to be designed out: judging a tool on
things it never claimed to do, crediting a tool for cases it never ran, and producing a
single number that reads as a leaderboard.

## Decision

- **Declared scope.** Each findings file lists the classes the tool claims to cover.
  Expected findings outside scope are `uncovered`, and findings outside scope are
  `out_of_scope_findings`. Neither is a false negative or false positive.
- **Explicit `cases_run`.** Cases a tool did not run are excluded and reported as
  `not_run`. A findings file that reports on a case outside `cases_run`, or lists an
  unknown case, is rejected with an error. Not run is never treated as clean.
- **One-to-one matching.** A finding satisfies at most one expected finding. Duplicate
  reports cannot inflate recall.
- **Match key:** weakness class, file, and line within `line_tolerance`.
- **Undefined metrics are `null`.** Precision, recall and F1 are not reported as 0 or 1 when
  their denominator is zero.
- **No overall score.** Results are per class only.
- **Tool-neutral input.** `actionsbench score` reads a normalized findings file
  (`findings.schema.json`), so any scanner can be scored without an adapter. Per-tool
  adapters and SARIF rule maps are added separately, one tool at a time, after the tool's
  real output has been checked.

## Open

`line_tolerance` defaults to 0 as a placeholder. Whether the right rule is a fixed
tolerance, or "within the same step", is a decision for the M0 spike, once real scanner
output shows how tools anchor their findings.

## Consequences

- A tool is only criticized for what it claims to do. The cost is that the scope
  declaration becomes part of the result and must be sourced and stated when published.
- Results are harder to summarize in one line. That is intended.
- Strict validation of the findings file means an adapter bug that mislabels cases fails
  loudly instead of quietly producing a flattering score.

## Alternatives considered

- **Score every tool on every class:** simple, but penalizes tools for out-of-scope
  behavior and distorts the comparison.
- **A single F1 across classes:** convenient, but invites ranking and hides which classes
  drive the result.
- **Treat missing cases as clean:** wrongly rewards crashes and skipped runs.
