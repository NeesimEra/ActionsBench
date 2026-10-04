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

**Evidence so far (2026-10-04):** tools do anchor differently. For a multi-line `github-script`
step, zizmor reports the interpolation line (16, matching the label) and actionlint reports the
`script:` key (15). At tolerance 0 that is one miss and one false positive for actionlint; at
tolerance 1 it matches. Two tools are not enough to choose a rule, and the labels are not
changed to suit a tool; the decision waits for more adapters and more multi-line cases.

**Update after the mapping review (25 cases, nine classes):** the pattern held and widened. Every
anchoring difference between a tool and a label is exactly one line, across four cases and two
tools: zizmor reports privileged-trigger at the `on:` line (label: the trigger line), secrets-
exposure at the `uses:` line of the reusable-workflow call (label: `secrets: inherit`) and
artifact-integrity at the step header (label: the `uses:` line), and actionlint reports the
multi-line `github-script` case at the `script:` key. At tolerance 0 each costs one false
positive and one false negative; at tolerance 1 all of them match and nothing else changes. A
fixed tolerance is crude: it would not cope with a multi-line `run: |` block, where the right
rule is probably "same step" (the PRD's wording). Two tools and one-line differences are still
thin evidence, so the default stays at 0 and results are shown at both tolerances until a
step-level rule is designed.

## Consequences

- A tool is only criticized for what it claims to do. The cost is that the scope
  declaration becomes part of the result and must be sourced and stated when published.
- Results are harder to summarize in one line. That is intended.
- Strict validation of the findings file means an adapter bug that mislabels cases fails
  loudly instead of quietly producing a flattering score.
- In practice a tool's scope is the intersection of the classes it claims to cover and the
  classes that have a reviewed rule mapping. Declaring a wider scope than the mappings support
  would turn a missing mapping into a false negative.
- The runner (`actionsbench run`) enforces "not run is not clean": a case that crashes, times
  out, or produces unparseable output is excluded from `cases_run` and reported as failed.

- Tool configuration is part of the result (methodology 5.1). The findings contract has an optional
  `configuration` string, adapters pass every verdict-changing setting explicitly instead of relying
  on a tool's own default, and result directories are named after it. This was prompted by
  zizmor's personas: the same label is detected or not depending on the persona.

## Alternatives considered

- **Score every tool on every class:** simple, but penalizes tools for out-of-scope
  behavior and distorts the comparison.
- **A single F1 across classes:** convenient, but invites ranking and hides which classes
  drive the result.
- **Treat missing cases as clean:** wrongly rewards crashes and skipped runs.
