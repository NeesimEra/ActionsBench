# ADR 0004: `dev` is the integration branch and every pull request targets it

**Status:** Accepted (2026-10-04)

## Context

The owner asked for a `dev` branch with all pull requests referencing it. GitHub has no
repository setting that forces a pull request's base branch, so the rule has to be built
from the default branch plus an enforced check. The project also publishes immutable corpus
releases (`v*` tags), which need a stable branch to tag.

## Decision

- **`dev`** is the default branch and the only target for pull requests. Work branches from
  `dev` and is **squash-merged** into it, so `dev` stays linear and each commit is a
  Conventional Commit taken from the pull request title.
- **`main`** is the released state. It changes only through a **release pull request from
  `dev`**, merged with a **merge commit** by a maintainer. Release tags (`v*`) are created on
  `main` and are immutable.
- **Enforcement:** the required check `PR target` (`.github/workflows/branch-flow.yml`) fails
  any pull request whose base is not `dev`, except `dev` into `main` from this repository. It
  re-runs when a base branch is edited. Because the check is required by the rulesets on both
  branches, it cannot be bypassed by retargeting.
- **Rulesets** (no bypass actors):
  - `dev`: pull request required, squash only, linear history, up-to-date branch, CI and
    `PR target` required, no force-push, no deletion.
  - `main`: pull request required, merge commits only, CI and `PR target` required, no
    force-push, no deletion. The up-to-date requirement is off (see Consequences).
- **Dependabot** targets `dev` explicitly.

## Why `dev` is the default branch

It is the only way to make `dev` the default base in GitHub's pull request UI, in `gh pr
create`, and for Dependabot security updates. A contributor cannot target `main` by accident.

## Consequences

- Visitors land on `dev`, which may be ahead of the latest release. The README states that
  `main` and the tags are the released state.
- **Merge commits into `main` mean `dev` and `main` share ancestry** instead of diverging.
  Squash-merging release pull requests would make `dev` and `main` carry different commits for
  the same content, and the next release pull request would conflict. The cost is that `main`
  is not strictly linear: each release adds one merge commit.
- After a release merge, `main` is one commit ahead of `dev` (the merge commit). That is why
  `main`'s ruleset does not require the head branch to be up to date; requiring it would force
  a back-merge of `main` into `dev` after every release.
- The enforcement check is a convention backed by a required status. A repository admin can
  still change the rulesets, which is deliberate.

## Alternatives considered

- **Trunk-based development on `main`.** Simpler, but the owner asked for a `dev` branch, and
  a separate released branch suits immutable corpus releases.
- **Squash everywhere, including release pull requests.** Linear on both branches, but `dev`
  and `main` diverge and every release needs conflict handling or a back-merge.
- **Rebase-merge release pull requests.** Linear, but it rewrites commit SHAs on `main`, so
  the same commits exist twice and release history becomes hard to read.
- **Keep `main` as the default branch and rely on the check alone.** The check would still
  reject wrong-base pull requests, but every pull request would start with the wrong base and
  Dependabot would target `main`.
