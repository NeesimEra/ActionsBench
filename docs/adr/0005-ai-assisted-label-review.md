# ADR 0005: Record agent evidence review separately from human agreement

**Status:** Accepted (2026-10-22, explicit owner approval)

## Context

The owner requested parallel agent review of proposed labels and selected a new
`ai-reviewed` status rather than redefining `agreed`. Separate agent sessions can challenge
evidence and discover errors, but do not supply independent human judgment. The first four
sessions found workflow-reachability defects and unresolved rationale/classification issues.

## Decision

- Extend ADR 0002's lifecycle with `ai-reviewed`; reserve `agreed` for an independent human.
- Use a separate review session, not the case-writing conversation, and disclose its AI nature.
- Require a nonblank `ai:` reviewer identity different from the author and a `review_record`
  pointing to a dated record of scope, sources, case dispositions and limitations.
- Promote only supported cases without unresolved concerns in that scope. Challenged or
  uncertain cases stay `proposed` pending resolution and targeted re-review. This is not a
  final adjudication of `disputed` status.
- Reset materially edited cases to `proposed` until reviewed again. Never adjust workflows,
  classes or anchors merely to make a scanner's results look better.
- No change to scoring inclusion, matching, immutable release tags, or human-review gates.

## Consequences

- Consumers can distinguish author-only, agent-reviewed and human-agreed labels.
- Older schema validators reject the new status/metadata. This is an unreleased schema
  extension, to ship in a future release, not an amendment of 0.1.1's archive.
- The validator checks identity/record shape, not whether a reviewer is truly human or an
  evidence record is correct. Reported identities and evidence remain auditable claims.
- Shared model/provider bias remains possible. No label is represented as human-agreed and
  no agent review satisfies the PRD's independent-review target or justifies a leaderboard.
