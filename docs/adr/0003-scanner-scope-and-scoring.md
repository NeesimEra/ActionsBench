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

## Matching rule (decided 2026-10-04)

A finding matches a label when class and file are equal and both lines are in the same *region* of
the file: the same step, the same job outside its steps, or the same top-level key
(`src/actionsbench/regions.py`, methodology section 4). Exact-line matching with an optional
tolerance remains available for a strict comparison (`score --match line --tolerance N`). If the
labeled file cannot be parsed as a single YAML mapping, matching falls back to exact line equality.
Every result states the rule that produced it.

**Why.** Scanners anchor one construct at different lines, so the line is a tool convention and the
construct is what matters. Evidence, in the order it arrived:

- For a multi-line `github-script` step, zizmor reports the interpolation line (16, matching the
  label) and actionlint reports the `script:` key (15).
- After the mapping review (25 cases, nine classes) every anchoring difference between a tool and a
  label was exactly one line, across four cases and two tools: zizmor reports privileged-trigger at
  the `on:` line (label: the trigger line), secrets-exposure at the `uses:` line of the reusable
  workflow call (label: `secrets: inherit`) and artifact-integrity at the step header (label: the
  `uses:` line), and actionlint reports the `github-script` case at the `script:` key.
- Under exact-line matching each costs one false positive and one false negative. Under region
  matching all four match, and on this corpus the results equal a one-line tolerance exactly
  (pinned by the integration tests).

A fixed tolerance would pass these four but is the wrong shape: it depends on a magic number, and
it cannot cope with a multi-line `run: |` block where the interpolation sits several lines below the
`run:` key. A region needs no number, and it is the PRD's own wording ("same step").

**What it costs.**

- A region is coarser than a line. A tool that reports the wrong line inside a long step still
  matches, so region matching cannot distinguish a precise report from a loose one. Strict
  line-level results stay one flag away.
- Outside steps, a whole job is one region, so two different keys of the same job match each other
  (a label on `runs-on` is matched by a finding on `permissions` of that job).
- A step with several labeled problems of one class needs one expected finding per problem;
  matching stays one-to-one, so a tool reporting several lines of one problem gets one true positive
  and the rest are false positives.
- The evidence base is thin: two tools and four anchoring cases. Revisit when a third adapter
  (poutine) is added, and whenever a tool is found to anchor in a different construct from the label.

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
