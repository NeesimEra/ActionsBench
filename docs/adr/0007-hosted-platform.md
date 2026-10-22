# ADR 0007: the hosted platform is in scope, behind execution and disclosure guardrails

**Status:** Accepted (2026-10-22, owner decision) — supersedes the hosted-platform and
platform-engineering parts of the 2026-10-06 deferral (status.md) and the v0.1 non-goal in
the PRD.

## Context

The PRD (v0.1) marked "a hosted service, API or web frontend" out of scope, and on
2026-10-06 the owner deferred a submission platform ("submit a scanner, run it on our
servers, public leaderboard") with three recorded reasons:

1. Labels were not independently reviewed, so a leaderboard would present unreviewed
   numbers as results.
2. Running submitted scanners needs sandboxing, abuse handling and authentication: a large
   attack surface for a security benchmark, plus hosting and dispute handling.
3. The bottleneck was label review and corpus coverage, not a platform.

With 0.2.0 released (44 labels `ai-reviewed`, corpus versioned immutably, three scanner
adapters, wet-ware constraints understood) the owner now waives the deferral and accepts
the hosting and maintenance load. This ADR records what the platform is allowed to do, so
that accepting it does not silently reverse the study's evidence rules.

## Decision

Build a hosted web platform in this repository under `platform/`, split into two components
(owner direction, 2026-10-22: the UI is a Next.js application on the stable release line —
Next.js has no formal LTS program, so "LTS stable" is taken as the current stable major line
(Next.js 16.x) pinned to a patch version, running on a Node.js LTS runtime):

- **`platform/api` — Python JSON API (FastAPI).** The only component that touches the corpus
  and the scorer. It loads cases with the harness's own loader, validates findings documents
  against `findings.schema.json`, and scores them with the harness's `score()`. It serves
  no templates and executes no corpus content.
- **`platform/web` — Next.js UI (TypeScript, App Router).** Renders the pages by fetching
  from the API. Data pages are server components; the UI is presentational and holds no
  scoring or corpus logic of its own.

The platform progresses through milestones:

- **P0 (now):** read-only platform — corpus browser, per-case and per-class pages, results
  pages rendered from findings files that ship with the repository. No accounts, no
  uploads, no scanner execution. The evidence rules of ADR 0003/methodology apply as-is.
- **P1:** GitHub OAuth sign-in for scanner maintainers; project (tool) registration; the
  result files stay externally reproducible.
- **P2:** findings-file submission: a maintainer uploads a findings document the harness
  can validate against `findings.schema.json` for the declared tool/version; the platform
  stores it append-only with the submitter identity, the corpus version and the harness
  configuration it was produced with. This mirrors the pull-request route; nothing loses
  reproducibility by switching to a platform path.
- **P3:** hosted scanner runs: submissions that want server-side execution are dispatched
  to ephemeral runners with no network access and resource caps; the server itself never
  executes scanner code; raw outputs and the exact harness revision are archived with each
  run. If P3 cannot be made safe and reproducible, the platform stays at P2 without
  blocking anything else.
- **P4:** the public board: per-class scores with evidence, linkable from results to
  case pages. There is deliberately **no single "best scanner" ranking** and **no overall
  score** (PRD §5.6 and scoring.py): results are per class only.

Guardrails, none of which are negotiable inside the platform:

- **Never execute corpus content.** Case workflows are data — displayed or archived, never
  run by the platform. Only the established harness dry-run path ever runs scanners, and
  only for tools with reviewed rule mappings.
- **Label-review status is always visible.** Every score is shown with the status of the
  labels it was judged against (`ai-reviewed` by separate agent sessions; no independent
  human review yet; `agreed` is reserved for that). No result is presented as a validated
  ground-truth result while labels are not `agreed`.
- **Results are append-only and reproducible.** Platform-side results must record tool
  version, configuration, corpus version (`added_in`-dated corpus + changelog) and harness
  version; delete/rewrite paths are excluded. A stored run must be reproducible from the
  recorded inputs.
- **The static-path fallback stays true.** Findings remain validly reportable as versioned
  static files (PRD §5.4), so the platform can never become the only way in.

## Consequences

- `platform/api` is a standalone uv project (its own `uv.lock` and dev tooling) and
  `platform/web` a standalone npm project (its own `package-lock.json`), so the harness
  package and its release flow stay unchanged. CI gains platform jobs for both.
- The UI framework is Next.js 16 App Router with TypeScript. There is no second source of
  truth in the frontend: it renders what the API returns; if a page would need a score or
  a case the API does not provide, the API grows the endpoint (Python side) instead.
- The 2026-10-06 "revisit when" conditions are overtaken by this ADR; the owner explicitly
  accepts the security and maintenance load. P3 (execution) is bounded by the invariant
  above: if its isolation cannot be met, the platform halts at P2 by design.
- The static corpus explorer suggested by the deferral record is subsumed by P0 rather
  than built separately.
