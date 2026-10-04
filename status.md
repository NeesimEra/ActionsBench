# Status log

Append-only. Newest entries at the bottom. Each entry says what was done, what was verified
and how, what was decided, and what is still open.

---

## 2026-10-04: Scaffold

**Done**

- Project scaffold: `pyproject.toml` (hatchling, uv), `src/actionsbench/` (taxonomy, models,
  corpus loader and validator, scorer, SARIF parser, report, CLI), two JSON Schemas shipped
  as package data.
- Seed corpus: 9 cases (AB-INJ-0001 to 0007, AB-NEG-0001 and 0002), all `proposed`.
- Docs: PRD (moved from the abandoned MobileX folder), methodology, ADRs 0001 to 0003,
  CONTRIBUTING, SECURITY, corpus README and changelog, issue and PR templates.
- CI workflow with every action pinned to a verified full commit SHA.

**Verified (by running it)**

- 57 tests pass on Python 3.12 (uv default) and on 3.11 (the declared minimum).
- `ruff check`, `ruff format --check` and `mypy --strict` are clean.
- `actionsbench validate` accepts all 9 seed cases. Negative tests prove the validator
  rejects: an id that does not match its directory, negatives with findings, positives
  without findings, bad line numbers, evidence missing from the labeled line, paths that
  escape the case directory, `agreed` without an independent reviewer, unknown classes,
  non-URL references, and unknown fields.
- A built wheel contains both schemas and runs from a clean virtual environment.
- `uv sync --locked` succeeds, so CI's install step matches the committed lockfile.
- zizmor 1.30.1 (offline mode, so network-dependent audits did not run) reports no findings
  on our own CI workflow.
- zizmor on the seed corpus: flagged all 7 injection cases at exactly the labeled line and
  nothing on the 2 negatives. It also raised a separate `self-repository` note on
  AB-INJ-0007. Informal, one tool, offline mode; not a result.
- Real finding about running scanners: in place inside a git repository, zizmor reports
  paths prefixed with `corpus/cases/<id>/`; on an isolated copy it reports `.github/...`.
  Recorded in methodology and ADR 0002; the runner must isolate cases.

**Decisions made without asking**

- Harness in Python with two runtime dependencies (ADR 0001). The user asked "why python?"
  and the answer is recorded there; reversible.
- `argparse` for the CLI, dataclasses for the model, no validation framework.
- Case status gains `proposed` (PRD updated).
- Findings input gains `cases_run`, so "not run" is never treated as clean (ADR 0003).
- No frontend and no API (PRD non-goal). A static results site may come later.
- Removed a duplicate-id check from the loader after confirming it was unreachable.
- No license file, deliberately (gate B).

**Not verified**

- The CI workflow has never run on GitHub; it was only exercised command by command locally.
- The SARIF parser has been checked against zizmor only.
- Taxonomy classes have not been checked against the paper.
- Seed labels AB-INJ-0001 to 0003 and 0007 are reasoned, not independently sourced.

**Open**

- Everything in `plan.md` Phase 1. Second reviewer unnamed. Name collisions checked only for
  repo, PyPI and npm names.

---

## 2026-10-04: Gate B approved, licenses chosen

**Decision (owner, in chat):** make the repository public. Licenses: MIT for code, CC BY 4.0
for the corpus. The owner also chose to remove their personal email address from the commit
history before publication.

**Done**

- Added `LICENSE` (MIT) and `corpus/LICENSE` (the official CC BY 4.0 legal code, fetched from
  creativecommons.org and checked for the expected header and footer). `pyproject.toml` now
  declares `license = "MIT"`.
- Replaced the "license TBD" and "private reporting channel TBD" text in README,
  CONTRIBUTING, SECURITY, PRD and the corpus README. Security reports go through GitHub's
  private vulnerability reporting.
- Commit history rewritten to the GitHub noreply address. Because GitHub can keep old
  unreachable commits fetchable by SHA, the clean history is published in a fresh repository
  and the earlier private one is renamed and archived instead of being force-pushed over.

**Still open from the plan**

- Gate C (maintainer outreach before publishing results) and gate D (real-repository
  material) are unchanged; they apply to results and new cases, not to this scaffold.
- Second reviewer, taxonomy check against the paper, everything in `plan.md` Phase 1.

---

## 2026-10-04: Published, with protections

**Done**

- Repository public at https://github.com/NeesimEra/ActionsBench (GitHub detects the MIT
  license). The earlier private repository was renamed `ActionsBench-private-archive` and
  archived; it still contains the original commits and can be deleted by an org admin.
- **Merge policy:** squash only, branch deleted after merge, no wiki, projects or discussions.
- **Actions:** only GitHub-owned actions and `astral-sh/setup-uv` are allowed; full-commit-SHA
  pinning is required; the default token is read-only; workflows cannot approve pull
  requests; first-run approval is required for all external contributors.
- **Security features:** secret scanning with push protection, Dependabot alerts and security
  updates, Dependabot version updates for `github-actions` and `uv` (7-day cooldown), and
  private vulnerability reporting (the channel named in `SECURITY.md`).
- **Ruleset `protect-main`** (no bypass actors): pull request required, squash merge only,
  conversations must be resolved, branch must be up to date, both CI checks required and
  pinned to the GitHub Actions app, linear history, no force-push, no deletion.
- **Ruleset `immutable-release-tags`** on `v*`: no update, no deletion. Corpus releases are
  tagged, so tags must not move.

**Verified (by doing it)**

- CI passed on GitHub on Python 3.11 and 3.13, under the hardened Actions policy above.
- A direct push to `main` was rejected ("Changes must be made through a pull request; 2 of 2
  required status checks are expected") and so was a force-push. Remote `main` was unchanged.
- This entry went through a pull request and the required checks, which exercises the
  protected workflow end to end.
- Commit metadata uses the GitHub noreply address on all commits, and a search of every
  reachable object found no trace of the previous address.

**Decisions and limits**

- No required approvals: with one maintainer, a pull request could never be approved by
  anyone else. A pull request and passing checks are still required. Revisit when a second
  maintainer joins; `.github/CODEOWNERS` is in place but not enforced.
- Signed commits are not required, because commit signing is not set up. Worth adding.
- CodeQL is not enabled. The corpus contains deliberately vulnerable workflows, so any
  workflow scanner run on this repository must first exclude `corpus/`.
- There is no `CODE_OF_CONDUCT.md` yet.
- The ruleset has no bypass actors, so even an admin must change the ruleset itself to push
  around it.
- Not yet observed: Dependabot's first pull requests.

---

## 2026-10-04: `dev` branch and the branch flow

**Decision (owner, in chat):** add a `dev` branch; all pull requests reference it.

**Done** (design and trade-offs in [ADR 0004](docs/adr/0004-branching-model.md))

- `dev` created and made the **default branch**. `main` is the released state and carries the
  `v*` tags.
- New workflow `branch-flow.yml` with the required check **PR target**: it fails any pull
  request whose base is not `dev`, except the `dev` to `main` release pull request from this
  repository. It re-runs when a base branch is edited.
- Rulesets, no bypass actors:
  - `protect-dev`: pull request required, squash only, linear history, up-to-date branch,
    the two CI checks and `PR target` required, no force-push, no deletion.
  - `protect-main` (now targets `refs/heads/main` explicitly instead of the default branch):
    pull request required, merge commits only, the same three checks required, no force-push,
    no deletion, up-to-date requirement off.
- Repository allows squash and merge commits; the rulesets restrict which one applies per
  branch. CI also runs on pushes to `dev`. Dependabot targets `dev`.

**Verified (by doing it)**

- A pull request into `dev` ran all three required checks and was squash-merged.
- A direct push and a force-push to `dev` were both rejected; remote `dev` was unchanged.
- A pull request targeting `main` from a branch other than `dev` failed `PR target`, showed a
  blocked merge state and could not be merged. After retargeting it to `dev`, the check
  re-ran on its own and passed. The throwaway pull request (#3) was closed unmerged.

**Limits**

- Visitors land on `dev`, which can be ahead of the latest release. The README says `main`
  and the tags are the released state.
- Each release adds one merge commit to `main`, so `main` is not strictly linear. Squashing
  release pull requests would make `dev` and `main` diverge (ADR 0004).
- The check is enforced by the rulesets, which a repository admin can still edit.

---

## 2026-10-04: Isolated scanner runner and zizmor adapter (M0, steps 1 to 3 for one tool)

**Done**

- `actionsbench run --tool zizmor`: copies each case's `.github/` into a fresh temporary
  directory, runs the pinned scanner there, stores raw SARIF under `results/` (gitignored), and
  writes a findings file for `actionsbench score`.
- Adapter contract (`adapters/base.py`) and the zizmor adapter, pinned to 1.30.1 and run with
  online audits disabled. Only `zizmor/template-injection` is mapped (to injection); scope is
  therefore the injection class only. Other rules are reported as unmapped.
- Runner rules: a case that exits unexpectedly, times out, produces unparseable output,
  reports a different tool version than the pin, or reports a path that does not resolve in
  the isolated copy is excluded from `cases_run` with the reason recorded. A missing scanner
  binary is an error, not a clean run.
- Corpus validation now rejects symbolic links in case directories, so a contributed case
  cannot point a scanner at files outside it.

**Verified (by running it)**

- 87 unit tests, ruff and mypy pass. The unit tests use a fake scanner to exercise each runner
  rule: nonzero exit, garbage output, timeout, bad path, version drift, missing binary, and that
  the scanner never sees `case.yaml` or a path inside the corpus.
- Real run (`pytest -m integration` and `actionsbench run` then `score`): all 9 seed cases ran
  with zizmor 1.30.1; injection TP 7, FP 0, FN 0; the negatives were clean; `self-repository`
  surfaced as unmapped.

**Findings**

- The seed corpus is easy for zizmor, as expected: the seeds came from weaknesses in a different
  tool. This is one tool, one class, offline mode, and tolerance 0. It is a pipeline check, not
  a result.

**Not done / next**

- Adapters for actionlint and poutine, each after inspecting real output.
- Growing the corpus to about 50 cases across all 10 classes; the second reviewer; the line
  tolerance decision.
- The integration test is opt-in and not run in CI (it needs a download).

---

## 2026-10-04: actionlint adapter (M0, step 3, second tool)

**Done**

- `scripts/install-actionlint.sh`: downloads the official release (pinned 1.7.12), verifies its
  SHA-256 from the release's checksum file, installs to `.tools/` (gitignored). A wrong
  checksum is refused. The checksum comes from the same release, so it detects a corrupted or
  altered download, not a compromised release.
- actionlint adapter, pinned to 1.7.12. Maps only the untrusted-input check (an `expression`
  result saying a value "is potentially untrusted") to injection; scope is injection only. Every
  other result is reported as unmapped. External linters are disabled for determinism.
- Adapter contract gained two small, general hooks: `prepare` (the copy needs an empty `.git`
  directory or actionlint exits 3 with "no project was found") and `probe_version` (actionlint
  does not print its version in its output). A pinned-version mismatch stops the whole run.
- `actionsbench run --tool actionlint` works end to end.

**Verified (by running it)**

- 113 unit tests, ruff and mypy pass. Opt-in integration tests (`pytest -m integration`) pass
  against the real zizmor 1.30.1 and actionlint 1.7.12.
- A first false alarm worth recording: actionlint's `{{json .}}` output looked invalid, but the
  cause was zsh's `echo` expanding `\n` inside my test harness. The raw output parses strictly.

**Findings (injection class, 9 seed cases, one run each)**

| Tool | TP | FP | FN | tolerance |
|---|---|---|---|---|
| zizmor 1.30.1 | 7 | 0 | 0 | 0 or 1 |
| actionlint 1.7.12 | 4 | 1 | 3 | 0 |
| actionlint 1.7.12 | 5 | 0 | 2 | 1 |

- actionlint missed `github.ref_name` (AB-INJ-0004) and the composite-action sink (AB-INJ-0007).
- Tools anchor multi-line blocks differently (zizmor line 16, actionlint line 15 for
  AB-INJ-0006). Recorded as evidence for the open tolerance decision; labels were not changed.
- Caveats: the seeds came from weaknesses in a third tool, actionlint is mainly a correctness
  linter, and this is injection only. It shows the pipeline works and that tools disagree; it is
  not a ranking.

**Not done / next**

- poutine adapter, after inspecting its real output.
- The corpus still needs to grow to about 50 cases across all 10 classes; with zizmor at 7 of 7
  the seed set does not separate it from anything.
- Second reviewer; tolerance decision.

---

## 2026-10-04: Corpus batch 2 (16 new cases) and the taxonomy check

**Done**

- Checked the taxonomy against the paper: exactly ten classes with the definitions in use. Closes
  PRD open question 7. The classes are defined by grouping scanner rules, so they are broader than
  their prose (for example persisted checkout credentials are filed under artifact integrity).
- Added 16 cases (9 positive, 7 negative twins) covering eight more classes: unpinned-dependency,
  excessive-permission, privileged-trigger, secrets-exposure, known-vulnerable-component,
  runner-compatibility, control-flow, artifact-integrity. With injection, the corpus now covers
  nine of the ten classes. The corpus is now 25 cases (16 positive,
  9 negative), all `proposed`.
- Every reference was read before being cited. Things I corrected by checking: the download-artifact
  advisory's vulnerable range is `>= 4.0.0, < 4.1.3` (I had assumed `< 4.1.7` from memory); a CVE ID
  could not be confirmed through GitHub's API, so only the advisory ID is cited; and
  `include-hidden-files` defaults to `false` in upload-artifact, so the artifact case sets it to true
  or there would be no weakness.
- hardening-gap has no cases yet and the reason is recorded in `corpus/README.md`.

**Verified (by running it)**

- The corpus validates (25 cases). Both adapters, scoped to injection, report no injection on any
  new case, and the seed results are unchanged (zizmor 7/0/0, actionlint 4/1/3 at tolerance 0).
- Raw reports on the new cases, before any mapping review: zizmor fired `unpinned-uses`,
  `secrets-inherit`, `dangerous-triggers` and `artipacked` where the labels expect those
  weaknesses, plus `obfuscation` on the constant condition; actionlint fired `runner-label` on the
  retired image and `if-cond` on the constant condition. Neither tool reported anything on any
  negative. zizmor reported nothing on the known-vulnerable action, as expected offline.

**Finding: tool configuration changes the verdict**

- zizmor at its default `regular` persona suppresses `permissions: write-all`; at `pedantic` or
  `auditor` it reports `excessive-permissions` at the labeled line (5) with high confidence.
  The runner records the tool version but not the configuration, so a score would silently depend
  on this choice. Next: make the configuration explicit in the adapter and add an optional
  configuration field to the findings contract so it appears in every result.

**Not done / next**

- Mapping review for the new classes, once the configuration question is settled. Candidate rules
  seen so far are listed above; none is mapped yet, so both adapters still score injection only.
- poutine adapter; a named second reviewer; the tolerance decision; about 25 more cases.

---

## 2026-10-04: Tool configuration is part of the result

**Done**

- The findings contract gains an optional `configuration` string. Adapters report it, `run` and
  `score` print it ("not recorded" when absent), and the result directory name includes it, so
  results from different configurations cannot overwrite or be mistaken for each other.
- zizmor: the persona is now always passed explicitly (`--persona=...`) instead of relying on the
  tool's default, and is selectable with `actionsbench run --tool zizmor --config persona=...`.
  Result directories are now `results/zizmor-1.30.1-<persona>/`. actionlint records its fixed
  `external-linters=disabled`. Unknown or malformed options are rejected before anything runs.
- Baseline decision: each adapter's baseline is the tool's default configuration made explicit
  (zizmor: `regular`); other configurations are run on purpose and reported beside it. I
  recommended this and it was not objected to; it is a judgement and can be revisited.

**Verified (by running it)**

- 127 unit tests, ruff and mypy pass. Five opt-in integration tests pass against the real tools:
  zizmor 1.30.1 under all three personas, a test that pins the persona effect described below, and
  actionlint 1.7.12.
- Real run of zizmor over the 25-case corpus under each persona (online audits off):

| Persona | Injection TP / FP / FN | `write-all` (AB-PRM-0001) | Other effects |
|---|---|---|---|
| regular | 7 / 0 / 0 | not reported | none on clean cases |
| pedantic | 7 / 0 / 0 | reported at line 5 | `anonymous-definition` and `concurrency-limits` on every case |
| auditor | 7 / 0 / 0 | reported at line 5 | same as pedantic |

- The persona does not change the injection result. It changes whether an excessive-permission
  label is detected at all, so a score for that class must state its configuration.

**Not done / next**

- Mapping review for the new classes (which zizmor and actionlint rules map to which benchmark
  class), now that the configuration is explicit. It must decide which persona the baseline uses
  for classes like excessive-permission, where the default misses a labeled weakness.
- poutine adapter; a named second reviewer; the line-tolerance decision; about 25 more cases.

---

## 2026-10-04: Rule mappings for the new classes and the first multi-class results

**Done**

- Reviewed and recorded rule mappings ([docs/rule-mappings.md](docs/rule-mappings.md)). Policy: map a
  rule only if its documentation was read, its class is unambiguous or the choice is recorded, and
  a corpus case exercises it; never map a rule because it fired on a labeled case.
- zizmor now judged on six classes: injection, unpinned-dependency, excessive-permission,
  privileged-trigger, secrets-exposure, artifact-integrity. actionlint on three: injection,
  control-flow (`if-cond`), runner-compatibility (`runner-label`).
- Deliberate exclusions, with reasons in the review record: zizmor's `known-vulnerable-actions`
  (online mode only, so that class is out of scope for zizmor here), `obfuscation` (fires on the
  constant-condition case but is not a control-flow rule), and actionlint's `permissions` check
  (validates names and values, not excess; this disagrees with the source study, whose own mapping
  was read for orientation but not copied because its repository declares no license).

**Verified (by running it)**

- 149 unit tests and 5 opt-in integration tests pass; ruff and mypy are clean. The integration tests
  now pin the per-class results below.
- Real runs over the 25-case corpus, baseline configurations plus zizmor's `auditor`. Cells are
  TP / FP / FN; "n/a" is out of scope for that tool (uncovered, not missed).

| Class | zizmor regular (tol 0 / tol 1) | zizmor auditor (tol 0 / tol 1) | actionlint (tol 0 / tol 1) |
|---|---|---|---|
| injection | 7/0/0 / 7/0/0 | 7/0/0 / 7/0/0 | 4/1/3 / 5/0/2 |
| unpinned-dependency | 2/0/0 / 2/0/0 | 2/0/0 / 2/0/0 | n/a |
| excessive-permission | 0/0/1 / 0/0/1 | 1/0/0 / 1/0/0 | n/a |
| privileged-trigger | 0/1/1 / 1/0/0 | 0/1/1 / 1/0/0 | n/a |
| secrets-exposure | 0/1/1 / 1/0/0 | 0/1/1 / 1/0/0 | n/a |
| artifact-integrity | 0/1/1 / 1/0/0 | 0/1/1 / 1/0/0 | n/a |
| control-flow | n/a | n/a | 1/0/0 / 1/0/0 |
| runner-compatibility | n/a | n/a | 1/0/0 / 1/0/0 |
| known-vulnerable-component, hardening-gap | n/a | n/a | n/a |

**Findings**

- No tool reported a mapped-class finding on any clean case, at either tolerance.
- Anchoring is the dominant strict-score disagreement, and every difference is exactly one line:
  zizmor reports privileged-trigger at the `on:` line, secrets-exposure at the call's `uses:` line and
  artifact-integrity at the step header, and actionlint reports the multi-line `github-script` case
  at the `script:` key. At tolerance 0 each is one false positive plus one false negative. Labels
  were not changed to suit a tool. A fixed tolerance is crude (ADR 0003 is updated); the PRD's
  "same step" rule is the likely answer and needs a design.
- The persona effect shows in one class: excessive-permission is a miss at the default persona and
  found at `auditor`.
- zizmor's `obfuscation` fires on the constant-condition case but stays unmapped, so zizmor is
  uncovered (not missed) on control-flow.

**Caveats**

- One reviewer, 25 hand-built cases, one run each, labels written before looking at tool output, and
  one positive per class for most classes, so each cell moves in whole cases. This is a pipeline
  check and an early signal, not a ranking.
- Class-level scope can overstate coverage when a mapping covers part of a broad class
  (documented as a limit).

**Next**

- Design the matching rule (step-level instead of a fixed line tolerance).
- poutine adapter; a named second reviewer; more cases per class, including harder variants, so that
  results are not decided by single cases.

---

## 2026-10-04: Matching rule decided (same region, not N lines)

**Decision.** A finding matches a label when class and file are equal and both lines are in the same
*region*: the same step, the same job outside its steps, or the same top-level key. I read "yes" to
"the matching rule or more cases?" as both and did this first because I had recommended it.
Exact-line matching with an optional tolerance stays available (`--match line [--tolerance N]`);
every result now states which rule produced it. Details and costs: ADR 0003, methodology section 4.
`plan.md` still lists the tolerance as an open step; it is a draft that was never approved, so it is
left as written and this entry is the record.

**Done**

- `regions.py` maps a line to its region using PyYAML node positions (not indentation), so a block
  list whose dash sits at the parent's indentation, comments and blank lines are handled by the
  parser. A file that is not a single YAML mapping has no index and matching falls back to exact
  line equality; nothing is guessed.
- `score` gains `matching` ("region" by default, or "line" with an optional tolerance); the CLI gains
  `--match`; `--tolerance` without `--match line` is an error; text and JSON output state the rule.
  Only the labeled file is read, and its path was validated at corpus load, so a findings file cannot
  choose what the scorer reads.

**Verified (by running it)**

- 189 unit tests and 5 opt-in integration tests pass; ruff and mypy are clean. The four real anchoring
  differences (zizmor at the `on:` line, the call's `uses:` line and the step header; actionlint at
  the `script:` key) are tested as same-region, and neighbouring constructs (the next step, the
  permissions block, the job) as different regions.
- Against the real tools, region matching gives exactly the results of a one-line tolerance on this
  corpus, and strict line results are unchanged. A hand-counted line number in one of my own tests was
  off by one and the code correctly refused the cross-step match; the tests now look lines up by text.

**Limits**

- Region matching is coarser than a line: it cannot tell a precise report from a loose one inside a
  step, and a whole job is one region outside its steps.
- The evidence is two tools and four anchoring cases. Revisit when poutine is added.

**Next**

- More cases, including harder variants and more than one positive per class, so a cell is not
  decided by a single case. poutine adapter; a named second reviewer.

---

## 2026-10-04: Corpus batch 3 (19 cases): harder variants and more than one positive per class

I read "yes" to "the matching rule or more cases?" as both; the matching rule was done first, this is
the cases.

**Done**

- 19 new cases (10 positive, 9 clean twins or probes); the corpus is now 44 (26 positive, 18
  negative), all `proposed`. Harder variants: a long multi-line script, an issue title, a review
  comment, a reusable workflow referenced by a tag, workflow-level `contents: write`, a hardcoded
  container password, `toJSON(secrets)`, a second advisory (`shivammathur/setup-php` 2.37.0), the
  retired `macos-10.15` runner, and a download with no integrity check. Probes: safe contexts (pull
  request number and commit SHA) and a `pull_request_target` trigger with nothing untrusted.
- Every source was read before being cited. Details that came from checking, not memory: the advisory's
  range and patched version were read from GitHub's API; setup-php's tags have no `v` prefix and the
  2.37.0 tag is annotated, so it was dereferenced to its commit; both commits were resolved and the
  patched one is literally "Bump version to 2.37.1".
- One idea was dropped for lack of a source: an always-true condition written as mixed `${{ }}` and
  text. actionlint's documentation does not describe it, so it is not labeled from memory.
- Mapping additions, each after its documentation was read and a case exercised it: zizmor
  `hardcoded-container-credentials` and `overprovisioned-secrets`, and actionlint `credentials`, all
  to secrets-exposure. actionlint is now judged on four classes.

**Mistakes caught (mine)**

- AB-INJ-0009 and AB-INJ-0010 were malformed workflows: an unquoted value with a colon and a space
  (`echo "New issue: ..."`) is invalid YAML. The runner did its job: zizmor refused both, they were
  reported as not run rather than clean, and actionlint reported `syntax-check`, which would have
  scored as two bogus misses. The cases are fixed, and the corpus validator now requires every YAML
  file under `.github/` to parse (with tests), so this cannot recur.
- My note on AB-ART-0002 said both tools would leave it "uncovered", but zizmor is judged on that
  class through `artipacked`, so it scores as a miss. The note now says what the scoring does.
- **My earlier claim that region matching equals a one-line tolerance was only true at 25 cases.** At
  44 it is false: actionlint reports the long `run: |` block at its `run:` key and zizmor reports the
  container credentials at the `container:` block, each two lines from the label. A one-line
  tolerance misses both (actionlint injection 7/1/3 instead of 8/0/2; zizmor secrets-exposure 2/1/1
  instead of 3/0/0); region matching gets both; a tolerance of two happens to equal region matching,
  but a longer block would need a bigger number. ADR 0003 and the methodology are corrected; this is
  the failure mode that ADR predicted, now seen with real tool output.

**Verified (by running it)**

- 195 unit tests and 5 opt-in integration tests pass against the real tools; ruff and mypy clean; all
  44 cases ran in every configuration with no failures. Results (region matching; TP / FP / FN; "n/a" is
  out of scope, i.e. uncovered, not missed):

| Class | zizmor regular | zizmor pedantic | zizmor auditor | actionlint |
|---|---|---|---|---|
| injection | 10/0/0 | 10/2/0 | 10/2/0 | 8/0/2 |
| unpinned-dependency | 3/0/0 | 3/0/0 | 3/0/0 | n/a |
| excessive-permission | 0/0/2 | 2/0/0 | 2/0/0 | n/a |
| privileged-trigger | 1/1/0 | 1/1/0 | 1/1/0 | n/a |
| secrets-exposure | 3/0/0 | 3/0/0 | 3/0/0 | 1/0/2 |
| artifact-integrity | 1/0/1 | 1/0/1 | 1/0/1 | n/a |
| control-flow | n/a | n/a | n/a | 1/0/0 |
| runner-compatibility | n/a | n/a | n/a | 2/0/0 |
| known-vulnerable-component, hardening-gap | n/a | n/a | n/a | n/a |

**Findings**

- `pedantic` and `auditor` are identical on every class.
- Configuration shows up in two places. The default persona misses both excessive-permission cases
  (`write-all` and workflow-level `contents: write`). `pedantic` and `auditor` flag the two safe
  contexts in AB-NEG-0012 (the pull request number and the commit SHA), which zizmor's own
  documentation says they do, costing two false positives on injection.
- Both personas flag the trigger-only negative AB-NEG-0010. That was labeled as a deliberate
  definitional split: zizmor flags `pull_request_target` itself, while the class definition needs
  untrusted data as well. It is a candidate for a label challenge, not a plain error.
- actionlint misses `github.ref_name` and the composite-action sink as before, finds both new
  untrusted-input cases once they were valid, and catches only the hardcoded-credentials pattern in
  secrets-exposure.
- Class-level scope shows its limit: two of actionlint's three secrets-exposure misses and zizmor's
  artifact-integrity miss are patterns no rule of that tool targets. They are honest statements of
  what each tool detects, but a per-class recall figure over-reads as "how good the tool is at the
  class". A per-pattern notion of coverage is a candidate improvement.
- Nothing in the corpus can be detected for known-vulnerable-component (zizmor needs online mode,
  actionlint has no rule) or hardening-gap (no cases). The class is in the corpus to define it, not
  because a tool covers it.

**Caveats**

- One reviewer, hand-built cases, one run each. Many classes still have only two or three positives,
  so a cell moves in whole cases. A pipeline check and an early signal, not a ranking.

**Next**

- poutine adapter (a third tool tests the matching rule and the mappings); a named second reviewer;
  decide what to do about per-pattern coverage and the hardening-gap class.

---

## 2026-10-04: Evidence audit (desk research, nobody else involved)

**What was asked.** Whether the labels can be verified by researching online, without involving a third
party. Partly yes, and this entry says exactly how far. The record is
[docs/evidence-audit.md](docs/evidence-audit.md); the experiment is `tools/verify-expressions`.

**Done**

- Checked the facts behind all 44 cases against primary sources: GitHub's secure-use and reusable-workflow
  documentation, the Security Lab article, the actions' own READMEs and source at pinned tags, the tools'
  documentation, OWASP CICD-SEC-9, and GitHub's advisories API with the commits resolved from the
  repositories. 13 case-checks are demonstrated by experiment, 35 confirmed in primary documentation,
  4 in advisory data, 2 in source code, and 4 are marked as depending on judgement.
- The experiment evaluates each injection case's expression with GitHub's own published expression engine
  (`@actions/expressions` 0.3.61, MIT, installed with scripts disabled and pinned by lockfile), substitutes
  the result into the script as GitHub documents, runs it in bash, and checks for a canary file. Every
  positive ran the payload (`format()`, `contains(...) && x`, `toJSON()`, `ref_name`, the commit author name,
  a composite input, a deep line, an issue title, a review comment). Every clean twin was inert: a boolean
  `contains()`, the pull request number, the commit SHA, and an environment variable. Git itself accepts the
  branch-name payload as valid.
- It is a regression check: it exits non-zero when a result differs from the labels. I proved that with a
  deliberately wrong expectation (my first attempt at that test used GNU-only `sed` on macOS, never changed the
  file, and "passed" for the wrong reason; the redo diffs the file first).

**Defects found and fixed**

- AB-ART-0001 and AB-NEG-0008 described a weakness that did not exist at the version they pinned. With
  `actions/checkout` 7.0.1 the job token is not in `.git/config` (changelog 6.0.0: "Persist creds to a separate
  file"; source confirms), so an artifact of the workspace would not contain it. Both now pin 4.2.2, where
  the source writes the token into `.git/config` and removes it when `persist-credentials` is false.
- AB-SEC-0001 omitted that `secrets: inherit` only works within the same organization or enterprise.
- AB-INJ-0004 cited an advisory about `github.ref`, not `github.ref_name`; the case now says so.
- Cases that were "reasoned, proposed" (AB-INJ-0001, 0002, 0003, 0007) are now demonstrated, and their
  wording says so.

**Verified (by running it)**

- 195 unit tests and 5 opt-in integration tests pass; ruff and mypy clean; all 44 cases validate. Tool results
  are unchanged by the corrections: zizmor still flags the corrected artifact case and is silent on its twin.

**What it does not establish**

- It does not make any label `agreed`. A re-read by the author, or by the assistant that wrote the cases, is
  not independent, and methodology section 3 now separates `proposed`, evidence-audited and `agreed`.
- It is not a live run: the expression engine is one of several implementations of the language, the
  substitution step is modeled from documentation, and checkout behavior was read from source, not run.
- Judgement calls remain (the cases marked J): the class for AB-ART-0001, the definitional split in
  AB-NEG-0010, whether a constant condition belongs in control-flow, the class fit of AB-ART-0002.

**Gates (owner decisions, not mine)**

- Gate A (spike go or no-go): the evidence supports a provisional go. Scanners clearly disagree with careful
  labels, and the labels' facts hold up. It is not firm until label judgement is independently reviewed.
- Gate C (share results with scanner maintainers before publishing weaknesses): not crossed. The instruction
  to avoid third parties was about verifying labels; whether it also waives maintainer outreach before an
  official release is a decision for the owner and has not been made. Per-tool results are already in this
  public repository, caveated.

**Not done / next**

- poutine adapter; decide the hardening-gap class and per-pattern coverage; put the experiment in CI if wanted.
