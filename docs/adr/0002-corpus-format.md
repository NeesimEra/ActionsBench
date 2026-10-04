# ADR 0002: Cases are fake repositories with a schema-validated `case.yaml`

**Status:** Accepted (2026-10-04)

## Context

Scanners take a repository path or a set of workflow files. Labels must stay attached to
the files they describe, survive edits, and be reviewable by people who do not write Python.
The corpus will be contributed to through pull requests, so the validator will run on
untrusted input in CI.

## Decision

- **One directory per case**, named by the case ID (`AB-<CLASS>-NNNN`). The directory is a
  fake repository root: workflow and action files sit under `.github/` exactly where a
  scanner expects them, so a scanner can be run on the directory unchanged.
- **Labels in `case.yaml`**, beside the files and outside `.github/`, so scanners never see
  them.
- **The schema is the contract.** `case.schema.json` and `findings.schema.json` ship with the
  package and are the specification for contributors and for scanners written in any
  language. Semantic rules the schema cannot express live in `corpus.py`.
- **Evidence-anchored labels.** Each expected finding has a line number and an `evidence`
  substring that must appear on that line, so edits cannot silently move a label.
- **ID encodes the primary class.** The prefix (`INJ`, `PIN`, `NEG`, ...) must match the
  first expected finding's class, or `NEG` for negatives. The ID must equal the directory
  name, which also makes IDs unique without a separate check.
- **Status lifecycle:** `proposed` (one reviewer), `agreed` (an independent reviewer),
  `disputed`. `agreed` requires a reviewer different from the author. This extends the PRD,
  which listed only agreed and disputed.
- **Path safety.** A label's `file` must be relative and resolve inside the case directory.
- **Validation reports every problem**, not only the first, so a contributor sees the full
  list in one CI run.
- **Versioning by git and `added_in`.** Releases are immutable git tags, and `added_in`
  records the version that introduced a case. Cases are amended or disputed, not silently
  rewritten.

## Consequences

- Contributors can add a case without touching Python.
- Scanners can be evaluated on the real file layout, including multi-file cases such as
  composite actions and reusable workflows.
- The corpus directory contains deliberately vulnerable workflows. They are inert because
  GitHub only runs workflows at the repository root's `.github/workflows/`, but tools that
  scan the whole repository (including our own CI scanners) will see them. Tooling that
  scans this repository must exclude `corpus/`.
- Scanners must be run on an isolated copy of a case's `.github/` directory, not on the
  case directory in place. Verified with zizmor 1.30.1: in place (inside this git
  repository) it reports paths prefixed with `corpus/cases/<id>/`, which would never match
  a label. The copy also guarantees the label file is never visible to a scanner.
- Line anchors make labels fragile to reformatting. The `evidence` check turns that
  fragility into a clear validation error instead of a silent mislabel.

## Alternatives considered

- **A single labels file (CSV or JSON) pointing at workflow files:** easier to bulk-edit,
  but labels drift away from files and per-case rationale becomes awkward.
- **Labels as comments inside the workflow:** keeps them next to the code but changes the
  file a scanner reads, which would contaminate the test.
