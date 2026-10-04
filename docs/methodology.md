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

### 5.1 Configuration is part of the result

A tool's settings can change its verdict, so every result records them. The findings file has an
optional `configuration` string, adapters fill it in, `run` and `score` print it, and the result
directory name includes it. Results from different configurations are different results; they are
never merged or averaged. A findings file with no configuration is accepted and shown as "not
recorded".

Each adapter's **baseline** is the tool's default configuration made explicit, because that is how
the tool is normally run. Any other configuration is run on purpose (`--config KEY=VALUE`) and
reported next to the baseline, never in place of it.

Observed with zizmor 1.30.1 on the 25-case corpus (2026-10-04, online audits off):

| Persona | Injection (TP / FP / FN) | `write-all` (AB-PRM-0001) | Other effects |
|---|---|---|---|
| regular (baseline) | 7 / 0 / 0 | not reported (suppressed) | none on clean cases |
| pedantic | 7 / 0 / 0 | reported at the labeled line | adds `anonymous-definition` and `concurrency-limits` to every case, including clean ones |
| auditor | 7 / 0 / 0 | reported at the labeled line | same additions as pedantic |

The persona does not change the injection result here. It changes whether an excessive-permission
label is detected at all, and how noisy clean cases look. A score for that class would therefore
need its configuration stated beside it.

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

- Labels are only as good as their review. Until a case is `agreed`, treat it as a claim.
- The line-tolerance rule and the exact scope declarations are unresolved until the spike.
- **A tool's configuration changes its verdict.** It is now recorded with every result (section
  5.1), but the choice of baseline configuration is still a judgement. For zizmor the baseline is the
  default `regular` persona, made explicit; `pedantic` and `auditor` are run and reported separately.
- The ten classes were checked against the source study (2026-10-04): there are exactly ten, with
  the definitions used here. The study defines them by grouping scanner rules, so in practice
  they are broader than their prose, and the study's rule mapping lives in a repository that
  declares no license; this project reads it but does not copy it, and every mapping in an
  adapter is reviewed independently.
- zizmor is currently scored on the **injection** class only. Only `zizmor/template-injection`
  has a reviewed mapping, even though zizmor claims wider coverage, so scoring it on other
  classes would count missing mappings as missed detections. Its scope grows as rules are
  reviewed one at a time. Its online audits are disabled for determinism, so audits that need
  GitHub's API do not run.
- actionlint is scored on the **injection** class only, through one check: an `expression`
  result whose message says a value "is potentially untrusted". actionlint is mainly a
  correctness linter, so this is a narrow slice of what it does, and its other results are
  reported as unmapped. It needs a project marker (an empty `.git` directory) in the isolated
  copy, and its external linters (shellcheck, pyflakes) are disabled so results do not depend on
  the machine.
- First head-to-head on the 9 seed cases (injection class, one run each): zizmor matched all 7
  labels; actionlint matched 4 exactly, missed the `github.ref_name` case (AB-INJ-0004) and the
  composite-action case (AB-INJ-0007), and reported the multi-line `github-script` case
  (AB-INJ-0006) at the `script:` key (line 15) where the label and zizmor use the interpolation
  line (16). The seeds were chosen from weaknesses in a third tool, so this is a pipeline check
  and an early signal, not a ranking. Per-class numbers, never a single score, are the output.
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
