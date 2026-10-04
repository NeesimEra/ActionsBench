# Methodology

How cases are labeled and how scanners are scored. This document describes the rules the
code in `src/actionsbench/` implements. Where a rule is a placeholder awaiting the M0 spike,
it says so.

## 1. What a case is

A case is a directory under `corpus/cases/` that acts as a fake repository root:

```
corpus/cases/AB-INJ-0001/
├── case.yaml                     # label and metadata
└── .github/
    └── workflows/format-wrapping.yml
```

Scanners are never run on the case directory in place. The harness copies the case's
`.github/` directory into a fresh, isolated directory and scans that copy. This matters
for two reasons: the label (`case.yaml`) never reaches a scanner, and tools that resolve
paths against the enclosing git repository report case-relative paths instead of paths
prefixed with `corpus/cases/<id>/` (observed with zizmor 1.30.1: in place it reported
`corpus/cases/AB-INJ-0007/.github/...`, on an isolated copy it reported `.github/...`).
`case.yaml` is validated against
[case.schema.json](../src/actionsbench/schemas/case.schema.json) plus the semantic checks
in `corpus.py`.

## 2. Labeling rules

**Anchor at the sink.** An expected finding points at the line where untrusted data reaches
the interpreter, such as the `run:` line or the `script:` line, not at the line where the
data enters. When the source is elsewhere (for example a caller's `with:` input), the
case's `notes` says where.

**One purpose per case.** A case labels one weakness, or is a clean negative. To keep it
that way, every `uses:` is pinned to a full commit SHA and the workflow sets `permissions:`,
unless the case is about exactly that. Otherwise unrelated weaknesses (an unpinned action,
missing permissions) would appear and a scanner reporting them would look wrong.

**Evidence on the line.** Each expected finding carries an `evidence` substring that must
appear on the labeled line. The validator enforces it, so editing a file cannot silently
move a label.

**Negatives are first-class.** A negative case is a workflow that looks risky but is safe
(for example an untrusted value passed through an environment variable). Without negatives
precision cannot be measured.

**Provenance.** `synthetic-minimal` is the default. `derived-from-advisory` is allowed only
for fixed, public advisories, with attribution and a license check. Live vulnerabilities in
real repositories are never included.

**Benign payloads.** No working exploit code and no real secrets.

## 3. Review and status

| Status | Meaning |
|---|---|
| `proposed` | One person has labeled it. The label is a claim, not yet independently checked. |
| `agreed` | An independent reviewer, different from the author, checked the label. |
| `disputed` | A challenge could not be resolved. The case stays, marked, with the argument recorded. |

Every case carries a written `rationale` and at least one `reference`. If a label was
reasoned from first principles and no independent source exists, the rationale says so.

## 4. Matching a finding to a label

A scanner finding is normalized to: case ID, weakness class, file, line, and optionally the
tool's rule ID. A finding matches an expected finding when:

- the weakness class is equal,
- the file is equal, and
- the lines are within `line_tolerance`.

`line_tolerance` defaults to 0. That default is a placeholder; the right value (or a
step-level rule) is a decision for the M0 spike.

Matching is **one-to-one**: a finding can satisfy at most one expected finding. A scanner
that reports the same line twice gets one true positive and one false positive, so
duplicates cannot inflate recall.

## 5. Scope

Scanners do not all claim to cover all weakness classes. For example, actionlint is mainly
a correctness linter. Judging every tool on every class would be unfair and would mislead.

Each report therefore declares a `scope`, the classes the tool claims to cover:

- Inside scope: matched findings are true positives, unmatched findings are false
  positives, unmatched expected findings are false negatives.
- Outside scope: expected findings are counted as `uncovered` and reported as a coverage
  gap. Findings are counted as `out_of_scope_findings`. Neither is a false negative or a
  false positive.

The scope is declared by whoever produces the report. Published results should state where
each scope came from (the tool's documentation, or the tool's authors).

## 6. Not run is not clean

A report lists `cases_run`, the cases the tool was actually run on. Cases outside that list
are excluded from scoring and listed as `not_run`. A tool that crashed on a case, or was
never run on it, is never credited with a clean result. A report that contains findings for
a case it did not run is rejected as inconsistent.

## 7. Metrics

Per weakness class: true positives, false positives, false negatives, precision, recall, F1,
plus the coverage counts above. Precision, recall and F1 are undefined (`null`) when their
denominator is zero. They are never reported as 0 or 1 by default.

There is **no overall score**. Results are per class so the output cannot be read as a
leaderboard, and so a tool's strengths and gaps stay visible.

## 8. Versioning and immutability

The corpus is released in immutable versions. A new version adds or amends cases; it never
silently rewrites old ones. `added_in` records which version introduced a case. Published
results state the corpus version and the scanner versions they used, so a result can always
be reproduced and compared.

## 9. Known limitations

- The taxonomy is the study's 10 classes as summarized in the PRD. It has not yet been
  verified against the paper (PRD, open question 7).
- Labels are only as good as their review. Until a case is `agreed`, treat it as a claim.
- The line-tolerance rule and the exact scope declarations are unresolved until the spike.
- zizmor is currently scored on the **injection** class only. Only `zizmor/template-injection`
  has a reviewed mapping, even though zizmor claims wider coverage, so scoring it on other
  classes would count missing mappings as missed detections. Its scope grows as rules are
  reviewed one at a time. Its online audits are disabled for determinism, so audits that need
  GitHub's API do not run.
- On the 9-case seed corpus zizmor matched every injection label (7 of 7) with no false
  positives. That says the seed set is easy for it, not that it is strong everywhere; the seeds
  were chosen from weaknesses in a different tool.
- The SARIF parser has been checked against real zizmor 1.30.1 output only (rule IDs are
  prefixed, for example `zizmor/template-injection`, and paths are case-relative on an
  isolated copy). Other tools still have to be checked one at a time.
- Scanners report findings outside the labeled weakness, for example zizmor's
  `self-repository` note on a composite-action call. Whether such a rule maps to a
  benchmark class, or is deliberately left unmapped, is a per-tool judgement made when an
  adapter is written. Unmapped rules are surfaced, never dropped silently.
