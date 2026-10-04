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
