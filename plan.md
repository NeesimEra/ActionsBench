# Plan

**Status:** Draft v1. Not yet approved. Once approved, this file is not edited; changes go
in a new version and progress goes in `status.md` (append-only).

**Goal:** go from the scaffold to a go/no-go decision on ActionsBench with real evidence, via
the M0 spike defined in [docs/PRD.md](docs/PRD.md) (section 8).

`[HUMAN_GATE]` marks a point where work stops until a person explicitly approves in chat.

---

## Phase 0: Scaffold (done)

Delivered and verified (details in `status.md`):

- Packaging, tooling and CI (lint, format, types, tests, corpus validation).
- JSON Schemas for cases and for the scanner findings contract.
- Corpus loader and validator, scorer, SARIF parser, CLI (`validate`, `stats`, `score`).
- A 9-case seed corpus (7 positive, 2 negative), all `proposed`.
- Docs: methodology, three ADRs, contributing guide, security policy, templates.

## Phase 1: M0 spike (about 1 week)

Aim: find out whether scanners disagree with careful labels enough to be worth publishing.

1. **Scanner runner.** Add a helper that copies a case's `.github/` into an isolated temporary
   directory, runs a scanner there, and stores the raw output under `results/` (gitignored).
   Isolation is required: in place, zizmor reports paths prefixed with `corpus/cases/<id>/`.
2. **Pin and install scanners.** zizmor, actionlint and poutine, with versions recorded. zizmor
   1.30.1 already runs via `uvx`; the other two need their install route checked.
3. **One adapter per tool, one at a time.** Inspect each tool's real output on the seed cases
   before writing its rule map. Rule-to-class mappings are judgement calls (for example
   zizmor's `self-repository` note). Review each map; do not mass-generate them.
4. **Grow the corpus to about 50 cases across the 10 classes, not just injection.** The seed
   set is easy for zizmor: informally, it flagged all 7 injection labels at exactly the
   labeled line and was clean on both negatives (zizmor 1.30.1, offline). The seeds were
   derived from weaknesses in the author's own scanner, so they say little about zizmor.
   Every new case needs a rationale and a reference.
5. **Second reviewer** on a sample of 20 cases. Needs a named person; see PRD open question 2.
6. **Decide the line-tolerance rule** from real scanner output (ADR 0003, open item).
7. **Disagreement report**, then the go/no-go below.

Optional, only if approved: an adapter for the author's own challenge scanner as a baseline.
It lives in a private IEEE challenge repository whose reuse terms are unknown (PRD open
question 6), and its patcher has known bugs, so only its detector would be used.

### [HUMAN_GATE] A: spike go/no-go

Review the disagreement report against the PRD kill criteria:

- scanners agree with labels on nearly everything (no story),
- labeling too ambiguous to reach reviewer agreement,
- an equivalent labeled workflow benchmark exists.

## Phase 2: v0.1 (about 3 to 4 weeks, only after gate A)

150 to 200 cases (target to revisit after the spike), full harness, report generation,
contributor guide, and a first maintainer review round.

### [HUMAN_GATE] B: license and publication

Before the repository is made public: choose licenses for code and for corpus data, set the
private vulnerability-reporting channel in `SECURITY.md`, and confirm the repository is
ready for public view. The repository stays **private** until this gate is approved.

### [HUMAN_GATE] C: maintainer outreach

Share results privately with scanner maintainers before publishing anything that names a
tool's weaknesses.

### [HUMAN_GATE] D: real-repository material

Approval is required before any case derived from a real repository is added. Public
advisories only, with attribution and a license check.

## Out of scope for this plan

Autofix-quality track, other CI systems, a static results site, and any hosted service
(see PRD non-goals).

## Risks to watch

- Seed labels S1 to S3 and AB-INJ-0007 are reasoned, not independently sourced.
- The taxonomy still has to be checked against the paper (PRD open question 7).
- Another group may publish a labeled benchmark first; re-check prior art at each gate.
