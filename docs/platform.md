# Platform spec

What the hosted platform does and does not do. The scope and guardrails were accepted in
[ADR 0007](adr/0007-hosted-platform.md). This page is the working checklist; each milestone
lands as its own pull request with tests.

## Invariants (every milestone)

1. **Corpus content is data.** Case workflows and payloads may be displayed and archived;
   they are never executed by the platform. Only a scanner adapter that the harness has
   already reviewed runs scanners, through the harness entry points.
2. **Label provenance travels with scores.** Every rendered score carries the label
   statuses behind it (`ai-reviewed` via separate agent sessions; `agreed` remains reserved
   for independent human review). When labels below `agreed` are used, pages say so.
3. **No aggregate champion.** Per-class only: TP/FP/FN, precision, recall, F1 and coverage
   per class. No overall score is computed or displayed anywhere.
4. **Reproducibility first.** A stored result records tool, tool version, configuration,
   corpus version, harness version and the findings document itself; results are appended,
   never rewritten or deleted.
5. **Artifact boundaries.** External submissions (P2+) are validated before storage;
   unrun cases are excluded and stated as such, matching `findings.schema.json`'s meaning
   of `cases_run`.
6. **One source of truth.** Only the Python API reads the corpus and scores findings.
   The Next.js UI never reimplements loading, validation or scoring; it renders what the
   API returns.

## Milestones

- **P0 (this PR): read-only platform.** `platform/api` — a FastAPI JSON API that loads the
  corpus with the harness loader, serves case/fixture data, validates findings documents
  against the schema and scores them with the harness scorer. `platform/web` — a Next.js
  16 (App Router, TypeScript) UI that renders the corpus browser (all cases, per case, per
  class), fixture file views as text, and results pages from API data. Nothing here
  uploads or executes anything.
- **P1: sign-in and projects.** GitHub OAuth. A signed-in maintainer can register a tool
  (name, repository, adapters applicable). No changes to scores.
- **P2: findings submission.** An authorized project submits findings documents (web UI
  upload over an API or a PR; whichever comes first is fine). Each submission is validated,
  scored server-side using the same `score()` call the CLI uses and stored append-only
  with submitter identity. Disputes re-open review rather than rewrite history.
- **P3: sandboxed hosted runs.** A maintainer triggers a real scanner run in an ephemeral
  environment: no network, resource caps, harness-pinned adapters, archived raw output and
  exact run inputs. The server process never executes the scanner itself; the runner does.
- **P4: public results board.** Per-class comparison across submitted tools, each score
  linking to per-case evidence. Deliberately not a ranked leaderboard.

## Running P0 locally

```sh
# API (terminal 1)
uv sync --project platform/api
uv run --project platform/api pytest          # platform API tests
uv run --project platform/api actionsbench-platform-api

# Web (terminal 2), Node.js LTS + npm
npm ci --prefix platform/web
npm run dev --prefix platform/web             # serves at http://localhost:3000
```

The web app proxies `/api/*` to the API (default `http://127.0.0.1:8000`, override with
`API_BASE`), so the browser stays same-origin. The API CLI's `--corpus` and `--results`
overrides mirror the harness CLI: from a clone the API defaults to the repository's
`corpus/cases`; a `--results` directory may hold findings documents that fail validation,
which are reported as problems while valid entries still render.

Note: run the API from the repository root (as above) unless you pass `--corpus`;
`default_corpus()` resolves `corpus/cases` relative to the process working directory.

## Stack pins (P0, as built)

- Next.js `16.4.2` (current stable 16.x line; the owner's "LTS stable" direction, see
  ADR 0007), React 19.3, TypeScript 5.x, Node 22 LTS in CI.
- Python 3.11/3.13 via uv (the platform/api tooling config mirrors the root's).
