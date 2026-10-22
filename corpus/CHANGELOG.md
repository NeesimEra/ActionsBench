# Corpus changelog

Corpus versions are immutable once released. A new version adds or amends cases; it never
silently rewrites old ones. Each case records the version that introduced it in `added_in`.

## Unreleased

- Added `ai-reviewed`, distinct from independent human `agreed`, with agent reviewer identity
  and a required `review_record`. This extends the case schema; older validators will reject it.
- Four agent sessions audited all 44 cases on 2026-10-22. Promoted 27 supported cases;
  initially held 17 pending factual, rationale or classification concerns. See
  [the audit record](../docs/ai-label-audit-2026-10-22.md).
- Repaired AB-INJ-0007's missing local-action checkout and AB-TRG-0001's blocked fork-head
  checkout. The latter explicitly opts into unsafe checkout and provides a benign build
  recipe. Targeted agent re-review cleared both. Expected classes, sink anchors and
  evidence substrings are unchanged.
- Replaced AB-NEG-0007's ambiguous v4.1.3 pin with v4.1.8, bundling artifact 2.1.8 above
  both conflicting toolkit advisory patch thresholds. Narrowed the negative to the two
  cited advisories and obtained targeted agent approval; no claim is made that the old pin
  is newly proven vulnerable.
- Corrected factual rationale scope for AB-INJ-0004/0005, AB-NEG-0012, AB-PIN-0002,
  AB-SEC-0001, AB-RUN-0002, AB-CTL-0001 and AB-NEG-0008/0009/0018. Targeted agents cleared
  all ten without changing workflows, expected findings, anchors or evidence.
- Resolved the final four boundary cases under ADR 0006: retain the explicit artipacked
  class exception but anchor at upload, anchor unverified archive consumption at tar,
  remove the echo-only negative's unused read permission, and give its named-secret peer
  an actual benign HMAC use. Targeted reviewers cleared all four. All 44 cases are now
  `ai-reviewed`, none human-agreed. Zizmor artifact counts change from 1/0/1 to 0/1/2
  because its checkout anchor no longer matches the upload sink; this is disclosed, not
  compensated for with tool-specific matching.
- No release tag, DOI archive, or published 0.1.1 corpus was changed.

## 0.1.1 (2026-10-06)

The corpus is unchanged from 0.1.0: the same 44 cases with the same labels. This release changes how it is
packaged. The wheel now bundles the corpus and both licenses, so a `pip install` is usable on its own, and the
CLI falls back to the bundled corpus when there is no `corpus/cases` in the working directory. The version of
0.1.0's wheel did not contain the corpus.

## 0.1.0 (2026-10-04)

Seed set of 44 cases (26 positive, 18 negative), all `proposed`.

Injection (first batch):

- AB-INJ-0001: untrusted value wrapped in `format()`
- AB-INJ-0002: `contains(...) && untrusted value`
- AB-INJ-0003: untrusted value passed through `toJSON()`
- AB-INJ-0004: branch name (`github.ref_name`)
- AB-INJ-0005: commit author name (`head_commit.author.name`)
- AB-INJ-0006: untrusted value in an `actions/github-script` script
- AB-INJ-0007: composite action sink with a tainted input and shallow indentation
- AB-NEG-0001: untrusted value passed through an environment variable
- AB-NEG-0002: `contains()` used as a boolean condition only

Other classes (second batch, each positive has a clean twin):

- AB-PIN-0001, AB-PIN-0002: action referenced by a tag, by a branch
- AB-PRM-0001: `permissions: write-all`
- AB-TRG-0001: `pull_request_target` checking out and building the pull request head
- AB-SEC-0001: `secrets: inherit` to a reusable workflow
- AB-KVC-0001: action pinned inside a published advisory's vulnerable range
- AB-RUN-0001: retired `ubuntu-18.04` runner image
- AB-CTL-0001: constant `if` condition
- AB-ART-0001: checkout credentials uploaded in an artifact
- AB-NEG-0003 to 0009: clean twins for the above

Third batch (harder variants and more than one positive per class, each with a clean twin):

- AB-INJ-0008: untrusted value on a deep line of a multi-line script
- AB-INJ-0009, AB-INJ-0010: issue title, review comment body
- AB-PIN-0003: reusable workflow referenced by a tag
- AB-PRM-0002: workflow-level `contents: write`
- AB-SEC-0002: hardcoded container registry password
- AB-SEC-0003: `toJSON(secrets)` in a step's environment
- AB-KVC-0002: `shivammathur/setup-php` 2.37.0, inside GHSA-pqwm-q9pv-ph8r's vulnerable range
- AB-RUN-0002: retired `macos-10.15` runner image
- AB-ART-0002: archive downloaded and unpacked without an integrity check
- AB-NEG-0010 to 0018: clean twins and probes (a `pull_request_target` trigger with nothing untrusted,
  a multi-line script via the environment, safe contexts, a pinned reusable workflow, credentials
  from secrets, one named secret, patched setup-php, `macos-latest`, a verified download)

Before this release an evidence audit checked the facts behind every label (docs/evidence-audit.md). It
corrected AB-ART-0001 and AB-NEG-0008, whose first draft pinned a checkout version where the described
weakness does not exist (they now pin 4.2.2), and it demonstrated the injection cases with GitHub's own
expression engine. No label has been independently reviewed: every case is still `proposed`.
