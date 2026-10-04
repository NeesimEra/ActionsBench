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
