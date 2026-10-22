# AI-assisted label audit — 2026-10-22

## Scope and limits

Four separate OpenCode general-agent sessions reviewed non-overlapping groups covering all
44 cases. They read the workflows/actions, labels, taxonomy, methodology and earlier audit,
and challenged claims against primary documentation, advisory data and action source.
They were explicitly told not to edit files, run corpus payloads, or tune labels to scanners.
No live workflows or exploits were executed. Some implementation sources track upstream
default branches; pinned action source was used for version-specific findings.

This is **AI-assisted evidence review, not independent human agreement**. Separate sessions
reduce shared conversational context, not shared-model errors or training-data bias. The
agents' exact model identifiers were not independently recorded. Their session identifiers
below are provenance, not public links or a substitute for the evidence summarized here.

The owner approved a distinct `ai-reviewed` status on 2026-10-22, preserving `agreed` for
independent human review. Initial maintainer-side triage promoted **27 cases** with supported
labels and no unresolved rationale concern; **17 remained proposed**. After the targeted
reachability fixes, artifact advisory revision, ten rationale corrections and four boundary
resolutions below, the current totals are **44 ai-reviewed, 0 proposed**. No case is human-agreed.
Supported synthetic pattern negatives do not certify fictional
callees, actual credentials, or successful production execution. Known-vulnerable-component
labels are affected-version inventory claims, not proof of a reachable exploit.

The initial audit and its promotions changed only status and review metadata, not workflows,
labels or rationales. Subsequent fixture fixes and rationale revisions are recorded below;
expected classes are preserved, but the boundary pass deliberately corrects the two artifact
sink anchors and their evidence substrings. Review must be repeated
after a material case change; it is not permanent approval of an ID.

The following four group tables preserve the **initial** dispositions. Current dispositions
for the subsequently repaired cases are in [Targeted re-review](#targeted-re-review) and
[Artifact advisory re-review](#artifact-advisory-re-review) and
[Rationale correction re-review](#rationale-correction-re-review), with final boundary
dispositions in [Boundary case re-review](#boundary-case-re-review).

## Injection

Reviewer: `ai:opencode:ses_e9cbdab14ffeq3bus49D4yfV2g` (14 cases).

| Case | Disposition | Evidence and qualification |
|---|---|---|
| AB-INJ-0001 | ai-reviewed | `format-wrapping.yml:13`: `format()` substitutes PR-title text, not shell escaping. |
| AB-INJ-0002 | ai-reviewed | `contains-and-value.yml:13`: `&&` returns the attacker-controlled branch-name operand when the guard is true. Ref restrictions still allow shell metacharacters. |
| AB-INJ-0003 | ai-reviewed | `tojson.yml:13`: JSON string serialization is not shell escaping; command substitution survives double quotes. |
| AB-INJ-0004 | proposed | `ref-name.yml:3,13`: push event requires base-repository ref/push authority. Explicitly qualify this threat model before promotion. |
| AB-INJ-0005 | proposed | `commit-author.yml:13`: injectable author metadata is supported, but the rationale's blanket “not validated” wording ignores Git's limited identity sanitization. |
| AB-INJ-0006 | ai-reviewed | `github-script.yml:16`: pinned github-script passes the supplied script to an `AsyncFunction` constructor. Interpolation is JavaScript source, not data. |
| AB-INJ-0007 | proposed — blocker | `caller.yml:11–15` never checks out the repository before invoking a local action. The sink in `actions/greet/action.yml:10` is injectable if called, but the supplied workflow does not provision that action. |
| AB-INJ-0008 | ai-reviewed | `multiline-script.yml:15`: multiline YAML does not prevent expression substitution into shell source. |
| AB-INJ-0009 | ai-reviewed | `issue-title.yml:13`: issue author controls the title; the issue event runs from the default-branch workflow. |
| AB-INJ-0010 | ai-reviewed | `review-comment.yml:13`: the event schema confirms `comment.body` is the review comment's text. |
| AB-NEG-0001 | ai-reviewed | `env-indirection.yml:13–15`: quoted environment expansion does not recursively parse title text as shell syntax. |
| AB-NEG-0002 | ai-reviewed | `boolean-contains.yml:13–14`: untrusted text affects only a Boolean condition; script text is constant. |
| AB-NEG-0011 | ai-reviewed | `multiline-safe.yml:13–18`: quoted environment expansion stays data; no secondary interpreter is present. |
| AB-NEG-0012 | proposed | `safe-contexts.yml:13`: number/hash representation is safe, but the rationale incorrectly equates this with complete absence of attacker influence. |

Primary evidence:

- [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use),
  [contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts),
  [expressions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions),
  [events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- [Runner AND operator](https://github.com/actions/runner/blob/main/src/Sdk/DTExpressions2/Expressions2/Sdk/Operators/And.cs),
  [JSON serialization](https://github.com/actions/runner/blob/main/src/Sdk/DTExpressions2/Expressions2/Sdk/Functions/ToJson.cs),
  [local action loading](https://github.com/actions/runner/blob/main/src/Runner.Worker/ActionManager.cs).
- [Pinned github-script execution](https://github.com/actions/github-script/blob/3a2844b7e9c422d3c10d287c895573f7108da1b3/src/async-function.ts).
- [Git ref syntax](https://git-scm.com/docs/git-check-ref-format),
  [commit identity](https://git-scm.com/docs/git-commit), and
  [ref-based injection threat model](https://github.com/stacklok/toolhive/security/advisories/GHSA-g976-wp3r-q8c6).
- [Review comment event schema](https://github.com/octokit/webhooks/blob/main/payload-schemas/api.github.com/pull_request_review_comment/created.schema.json).

The historical expression experiment bypasses local-action provisioning in AB-INJ-0007;
it establishes sink semantics, not end-to-end workflow reachability. Bash semantics were
not newly demonstrated; one attempted fetch of GNU Bash documentation timed out.

## Trust and secrets

Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR` (17 cases).

| Case | Disposition | Evidence and qualification |
|---|---|---|
| AB-PIN-0001 | ai-reviewed | `tag-ref.yml:13`: tag is mutable under upstream ref control. This is not an arbitrary fork contributor's authority. |
| AB-PIN-0002 | proposed | `branch-ref.yml:13`: mutable-reference label is supported; rationale's categorical “weaker even than a tag” comparison needs qualification. |
| AB-PIN-0003 | ai-reviewed | `reusable-tag.yml:10`: tag-based reusable workflow reference is mutable; no runtime behavior of the fictional callee is certified. |
| AB-PRM-0001 | ai-reviewed | `write-all.yml:5,12`: requested writes are unnecessary for constant echo. Ordinary fork PRs downgrade writes; this is an excessive-request claim, not demonstrated privileged fork access. |
| AB-PRM-0002 | ai-reviewed | `workflow-write.yml:6,13`: sole echo-only job inherits unnecessary requested write scope. Fork downgrade qualification also applies. |
| AB-SEC-0001 | proposed | `inherit.yml:10–11`: blanket forwarding is documented, but the fictional callee's claimed need for exactly one secret cannot be established. |
| AB-SEC-0002 | ai-reviewed | `hardcoded-credentials.yml:15`: literal-password pattern; the disclosed synthetic value is not a verified usable credential. |
| AB-SEC-0003 | ai-reviewed | `all-secrets.yml:14–15`: entire secret context reaches a step that needs none. Fork secret restrictions limit available values, but `GITHUB_TOKEN` is included in that context. No exfiltration is demonstrated. |
| AB-TRG-0001 | proposed — blocker | `pwn-request.yml:13–18`: checkout v7.0.1 rejects the fork-head SHA in a privileged event unless unsafe checkout is explicitly enabled. That opt-in is absent. |
| AB-NEG-0003 | ai-reviewed | `pinned.yml:13–15`: real full SHA, nonpersistent credentials; no mutable action reference. Pinning is not a general safety certification. |
| AB-NEG-0004 | proposed | `read-only.yml:6,13`: constant echo needs no contents access. Read-only is a defensible default, not the claimed job-specific minimum. |
| AB-NEG-0005 | ai-reviewed | `pull-request-head.yml:3,6,13–18`: ordinary PR event, explicit read scope, no secret reference or persisted credentials. Scoped negative for privileged-trigger escalation under ordinary fork settings. |
| AB-NEG-0006 | ai-reviewed | `explicit-secret.yml:10–12`: named-secret forwarding rather than blanket inheritance. Fictional callee necessity and handling are not verified. |
| AB-NEG-0010 | ai-reviewed | `trigger-only.yml:3,6,13`: constant echo, read scope, no untrusted code/data consumption. The trigger alone is insufficient under this class definition. |
| AB-NEG-0013 | ai-reviewed | `reusable-pinned.yml:10`: full-SHA form removes floating-ref behavior. Placeholder callee/commit are disclosed, not certified executable. |
| AB-NEG-0014 | ai-reviewed | `secret-credentials.yml:15`: password comes from secrets, not a literal. No real registry login is demonstrated. |
| AB-NEG-0015 | proposed | `named-secret.yml:14–15`: even one secret is unnecessary for constant echo. Resolve the class's least-authority boundary before calling this clean. |

Primary evidence:

- [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use),
  [reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
  [permission calculation](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#how-permissions-are-calculated-for-a-workflow-job),
  [secrets context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#secrets-context).
- [Pinned checkout fork guard](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/unsafe-pr-checkout-helper.ts),
  [input handling](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/input-helper.ts),
  [shipped bundle](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/dist/index.js).
- [Security Lab pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/),
  [secure pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
  [zizmor audits](https://docs.zizmor.sh/audits/),
  [actionlint checks](https://github.com/rhysd/actionlint/blob/main/docs/checks.md),
  [study definitions](https://arxiv.org/html/2601.14455v2#S5).

## Advisories and runners

Reviewer: `ai:opencode:ses_e9cbd5d11ffeEqL0ISzKVeCn2R` (7 cases).

| Case | Disposition | Evidence and qualification |
|---|---|---|
| AB-KVC-0001 | ai-reviewed | `vulnerable-download.yml:13–15`: pin resolves to affected v4.1.2. A crafted artifact and its availability are not established; this is component inclusion only. |
| AB-KVC-0002 | ai-reviewed | `vulnerable-setup-php.yml:13–15`: pin resolves to affected 2.37.0. Fixed trusted `php-version` avoids the advisory's repository-derived input path; component inclusion only. |
| AB-NEG-0007 | proposed — uncertainty | `patched-download.yml:13–15`: v4.1.3 is outside the action advisory's structured range, but its extraction callback appears to continue writing after Promise rejection, and a related toolkit advisory has conflicting prose/ranges. No exploit was demonstrated. |
| AB-NEG-0016 | ai-reviewed | `patched-setup-php.yml:13–15`: 2.37.1 is patched for the cited advisory; source validates explicit and repository-derived version inputs. |
| AB-RUN-0001 | ai-reviewed | `retired-runner.yml:10`: ubuntu-18.04 is unavailable as a GitHub-hosted image. Private self-hosted labels are outside that assumption. |
| AB-RUN-0002 | proposed | `retired-macos.yml:10`: retirement label is supported, but notes reverse history: the August 30 deadline was postponed to December 1, not vice versa. |
| AB-NEG-0017 | ai-reviewed | `current-macos.yml:10`: macos-latest remains a supported maintained label as of this audit, not a fixed OS/hardware version. |

Primary evidence:

- [Download-artifact advisory](https://api.github.com/advisories/GHSA-cxww-7g56-2vh6),
  [4.1.2 tag](https://api.github.com/repos/actions/download-artifact/git/ref/tags/v4.1.2),
  [4.1.3 tag](https://api.github.com/repos/actions/download-artifact/git/ref/tags/v4.1.3),
  [4.1.3 extraction bundle](https://github.com/actions/download-artifact/blob/87c55149d96e628cc2ef7e6fc2aab372015aec85/dist/index.js#L2414-L2443),
  [related toolkit advisory](https://api.github.com/advisories/GHSA-6q32-hq47-5qq3).
- [Setup-php advisory](https://api.github.com/advisories/GHSA-pqwm-q9pv-ph8r),
  [2.37.0 source](https://github.com/shivammathur/setup-php/blob/accd6127cb78bee3e8082180cb391013d204ef9f/src/utils.ts),
  [2.37.1 source](https://github.com/shivammathur/setup-php/blob/7c071dfe9dc99bdf297fa79cb49ea005b9fcadbc/src/utils.ts),
  [2.37.1 release qualifications](https://github.com/shivammathur/setup-php/releases/tag/2.37.1).
- [Ubuntu retirement](https://github.com/actions/runner-images/issues/6002),
  [macOS retirement postponement](https://github.com/actions/runner-images/issues/5583#issuecomment-1219501124),
  [final retirement update](https://github.com/actions/runner-images/issues/5583#issuecomment-1426004850),
  [hosted runner inventory](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

The source-level download-artifact concern remains unverified beyond static inspection.
It is not a newly proven vulnerability and does not justify describing the case as safely
patched without qualification or publishing an exploit claim.

## Artifacts and conditions

Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5` (6 cases).

| Case | Disposition | Evidence and qualification |
|---|---|---|
| AB-ART-0001 | proposed | `artipacked.yml:13–19`: pinned checkout persistence and hidden-file upload are supported; confidentiality-versus-integrity class fit and checkout-versus-upload sink anchor remain unresolved. |
| AB-ART-0002 | proposed | `unverified-download.yml:14–15`: absent integrity check is supported. The study's example is not this literal curl pattern; distinguish illustrative download from an actual available release and justify the source/consumption anchor. |
| AB-CTL-0001 | proposed | `constant-condition.yml:13`: true does not enforce a branch restriction, but implicit `success()` remains. Correct the unconditional-execution wording; security impact of echo-only publication is a judgment. |
| AB-NEG-0008 | proposed | `no-persist.yml:13–21`: token removal is supported on normal checkout cleanup. The claim that “nothing sensitive” is uploaded is broader than established behavior. |
| AB-NEG-0009 | proposed | `real-condition.yml:13`: nonconstant comparison is supported, but GitHub comparisons ignore case. “Only main” is not an exact case-sensitive authorization guarantee. |
| AB-NEG-0018 | proposed | `verified-download.yml:14–16`: checksum failure stops extraction under the default shell. Placeholder digest proves neither authenticity nor a successful usable download; qualify the audit's confidence. |

Primary evidence:

- [Pinned checkout token storage](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/src/git-auth-helper.ts),
  [cleanup](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/src/git-source-provider.ts),
  [pinned upload search](https://github.com/actions/upload-artifact/blob/043fb46d1a93c77aae656e7c1c64a875d1fc6a0a/src/shared/search.ts).
- [OWASP integrity validation](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation),
  [study definitions](https://arxiv.org/html/2601.14455v2#S5),
  [GitHub expression comparisons/status checks](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions),
  [default shell semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell),
  [GNU checksum checking](https://www.gnu.org/software/coreutils/manual/html_node/cksum-common-options.html),
  [IANA example domains](https://www.iana.org/help/example-domains).

## Targeted re-review

The owner authorized fixing the two reachability blockers and obtaining targeted re-review.
The original reviewing sessions inspected the revised files and primary sources without
editing files or executing workflows, scripts, payloads or the make recipe. Both found
their blocker resolved and no remaining substantive blocker in static/documented scope.

| Case | Disposition | Revised evidence and reviewer |
|---|---|---|
| AB-INJ-0007 | ai-reviewed | Caller lines 12–15 now perform pinned checkout with credential persistence disabled before the local action at line 17. PR-title input is at line 19; the composite sink stays at action.yml line 10. Reviewer: `ai:opencode:ses_e9cbdab14ffeq3bus49D4yfV2g`. |
| AB-TRG-0001 | ai-reviewed | Checkout explicitly sets `allow-unsafe-pr-checkout: true` at line 16, then executes the provided benign `.github/build.mk` recipe at line 19. Trigger anchor stays at line 3. Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR`. |

Re-review sources:

- [Composite action provisioning](https://docs.github.com/en/actions/tutorials/creating-a-composite-action#creating-a-composite-action-within-the-same-repository),
  [ordinary PR events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request),
  [pinned checkout inputs](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/input-helper.ts),
  [credential cleanup](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/git-source-provider.ts).
- [Pinned guard opt-in](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/unsafe-pr-checkout-helper.ts),
  [head-SHA fetch behavior](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/ref-helper.ts),
  [privileged-event risk](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
  [low-trust cache access](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#cache-access-for-low-trust-workflow-triggers).

The privileged case retains `contents: read`, no secret reference, and nonpersistent
checkout credentials. Its rationale explicitly makes no write-token, secret-theft or
cache-write claim; default-branch cache access is read-only without an explicit write mode.
The included recipe is benign but contributor-controlled after the head checkout. Static
tests check local-action provisioning order, the guard opt-in and recipe presence in the
isolated scanner copy. All six scanner integration tests pass with unchanged TP/FP/FN
counts; poutine's execution anchor moves from line 18 to 19 due to the added input.

Limits: no live checkout/fetch, payload execution or end-to-end runner demonstration. PR
accessibility, mergeability, workflow enablement, approval settings and compatible hosted
runners are assumed. The bundled checkout distribution was not independently compared
with TypeScript source during the composite re-review. Neither verdict is human agreement.

## Artifact advisory re-review

The owner authorized investigating AB-NEG-0007's advisory/source inconsistency. The
investigation confirmed that upstream metadata remains inconsistent as of 2026-10-22:

- GHSA-cxww-7g56-2vh6 describes action versions before 4.1.3 as affected and recommends
  4.1.3 or higher. Its structured range is `>= 4.0.0, < 4.1.3`.
- GHSA-6q32-hq47-5qq3 recommends toolkit `@actions/artifact` 2.1.7 or higher in prose,
  but its structured data names 2.1.2 as patched (`>= 2.0.0, < 2.1.2` affected).
- The old action v4.1.3 bundles toolkit 2.1.3. Its shipped callback at lines 2418–2443
  rejects an invalid extraction path but then continues toward writing. This is a static
  concern, not a demonstrated exploit or an adjudication against the published advisory.

Rather than certify the ambiguous old pin, the unreleased negative now pins **v4.1.8** at
`fa0a91b85d4f404e444e00e005971372dc801d16`. The official
[tag ref](https://api.github.com/repos/actions/download-artifact/git/ref/tags/v4.1.8) resolves
to that commit, and the [release](https://github.com/actions/download-artifact/releases/tag/v4.1.8)
records an artifact-library update. At the exact commit:

- [package-lock.json](https://github.com/actions/download-artifact/blob/fa0a91b85d4f404e444e00e005971372dc801d16/package-lock.json)
  resolves `@actions/artifact` **2.1.8**, above both stated toolkit patch thresholds.
- [Shipped bundle metadata, line 130593](https://github.com/actions/download-artifact/blob/fa0a91b85d4f404e444e00e005971372dc801d16/dist/index.js#L130593)
  also identifies toolkit 2.1.8; the claim is not inferred from the lockfile alone.
- [Extraction, lines 2380–2409](https://github.com/actions/download-artifact/blob/fa0a91b85d4f404e444e00e005971372dc801d16/dist/index.js#L2380-L2409)
  calls `unzip-stream.Extract`, rather than the old custom Parse/Transform callback. The
  [upstream replacement PR](https://github.com/actions/toolkit/pull/1724) documents that
  implementation change. It is not a proof of universal path-containment safety.

The revised rationale limits the negative to affected-version inclusion under those two
advisories. It no longer calls every known-vulnerable-component report categorically wrong.
No producer supplies `build-output` in this fixture; successful artifact consumption,
artifact attacker control, and live exploitability are not asserted. Offline regression
tests lock the reviewed negative pin and preserve the affected positive pin; they do not
query upstream or execute extraction.

The original advisory-review session independently verified the revised pin, advisory
ranges, lockfile, shipped package metadata, extraction implementation and scoped rationale.
It found no unresolved concern within that static/documented scope and cleared promotion.

| Case | Disposition | Revised evidence and reviewer |
|---|---|---|
| AB-NEG-0007 | ai-reviewed | v4.1.8 bundles artifact 2.1.8, outside the named affected ranges and above both toolkit patch thresholds. Reviewer: `ai:opencode:ses_e9cbd5d11ffeEqL0ISzKVeCn2R`. |

Verification limits remain: neither live artifact retrieval nor extraction was executed;
other advisories and universal dependency safety are not certified. This is not human
agreement, and the old v4.1.3 implementation's exploitability remains unadjudicated.

## Rationale correction re-review

Ten held cases received metadata-only corrections addressing the initial audit. Their
workflow/action bytes, expected findings, sink anchors and evidence substrings are
unchanged. Targeted reviews used the original separate review sessions, not the writing
conversation. All ten received supported verdicts for the corrected scope before promotion.

Corrections checked:

- AB-INJ-0004 and AB-INJ-0005 now explicitly require a crafted ref/commit to reach a pushed
  revision in the workflow repository; arbitrary fork PR creation alone is insufficient.
  The author-name case acknowledges Git's partial identity sanitization instead of calling
  the metadata completely unvalidated.
- AB-NEG-0012 relies on integer/hash syntax, not an assertion that contributors cannot
  influence commit hashes or on absence from a scanner's untrusted-context list.
- AB-PIN-0002 labels mutable branch references without ranking them categorically below tags.
- AB-SEC-0001 identifies the cited blanket-forwarding policy, without inventing the fictional
  callee's secret requirements, use, or exfiltration. Same-organization assumptions remain.
- AB-RUN-0002 correctly orders the initial August deadline, postponement to December 1,
  and later confirmation of unsupported status; the claim is about hosted runner labels.
- AB-CTL-0001 identifies a missing branch restriction while retaining implicit `success()`;
  its echo-only recipe is not an actual unauthorized publication demonstration.
- AB-NEG-0008 bounds its claim to checkout-token removal during successful normal cleanup,
  not the absence of all sensitive repository files or infallibility of cleanup.
- AB-NEG-0009 is a negative for a constant condition, not a case-sensitive authorization
  guarantee; GitHub's case-insensitive equality is disclosed.
- AB-NEG-0018 asserts fail-closed checksum gating under the default shell, not a verified
  authentic digest, available release, or successful download. No checksum command was run.

Primary sources for these corrections include the injection/trust sources above and:

- [GitHub operators and status checks](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions),
  [shell failure behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell),
  [GNU checksum checking](https://www.gnu.org/software/coreutils/manual/html_node/cksum-common-options.html).
- [Pinned checkout cleanup](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/src/git-source-provider.ts),
  [authentication removal](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/src/git-auth-helper.ts).
- [Retirement postponement, dated 2022-08-18](https://github.com/actions/runner-images/issues/5583#issuecomment-1219501124),
  [unsupported-date confirmation, dated 2023-02-10](https://github.com/actions/runner-images/issues/5583#issuecomment-1426004850).

The class/anchor disputes for AB-ART-0001/0002 and the least-authority boundaries for
AB-NEG-0004/0015 are deliberately not settled by wording changes in this pass.

Completed targeted verdicts:

| Case | Disposition | Corrected scope and reviewer |
|---|---|---|
| AB-INJ-0004 | ai-reviewed | Push/ref-creation authority explicitly required; the related advisory concerns github.ref rather than ref_name. Reviewer: `ai:opencode:ses_e9cbdab14ffeq3bus49D4yfV2g`. |
| AB-INJ-0005 | ai-reviewed | Partial Git identity sanitization acknowledged; crafted author must survive in head_commit for the pushed event, not merely some historical commit. Reviewer: `ai:opencode:ses_e9cbdab14ffeq3bus49D4yfV2g`. |
| AB-NEG-0012 | ai-reviewed | Integer/hash representation supplies no command-injection syntax in the supplied echo step, despite possible contributor influence on hashes. Reviewer: `ai:opencode:ses_e9cbdab14ffeq3bus49D4yfV2g`. |
| AB-PIN-0002 | ai-reviewed | Mutable branch reference; no categorical ranking below tags or assertion of actual upstream compromise. Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR`. |
| AB-SEC-0001 | ai-reviewed | Static blanket-forwarding pattern under the cited audit policy; fictional callee needs, actual leakage and runtime behavior remain unverified. Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR`. |
| AB-RUN-0002 | ai-reviewed | Corrected postponement chronology and current hosted-runner incompatibility; no scheduling failure was executed. Reviewer: `ai:opencode:ses_e9cbd5d11ffeEqL0ISzKVeCn2R`. |
| AB-CTL-0001 | ai-reviewed | No branch restriction, but implicit success() remains; the echo-only step demonstrates no actual publication. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |
| AB-NEG-0008 | ai-reviewed | Checkout authentication removed before upload under successful normal cleanup; warning-only failures and unrelated sensitive files are not ruled out. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |
| AB-NEG-0009 | ai-reviewed | Nonconstant comparison, with case-insensitive equality disclosed; no real release authorization certified. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |
| AB-NEG-0018 | ai-reviewed | Fail-closed checksum gating under the documented default shell; placeholder digest authenticity and successful download remain unverified. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |

These reviews newly checked primary-source documentation, not live workflow behavior.
Merge/squash strategy can affect the author represented by head_commit; fictional callees
cannot be certified executable; hosted-runner support is a dated observation. None of the
verdicts supplies independent human agreement or broadens the negative cases' scope.
The checksum reviewer verified GNU behavior in the preceding pass but its documentation
refresh timed out during this re-review; default-shell semantics were checked again.

## Boundary case re-review

The owner explicitly chose to retain the study-compatible `artifact-integrity` class for
AB-ART-0001 while moving its anchor to the upload exposure sink. ADR 0006 records that
confidentiality-related exception, preserves the ID, and prohibits tool-specific match
bridging. The final four cases were revised and cleared by their original review sessions
after reading the new files and primary sources. No workflow, extraction or signing code
was executed during review.

| Case | Disposition | Resolution and reviewer |
|---|---|---|
| AB-ART-0001 | ai-reviewed | Explicit study-compatibility class exception; anchor moves from checkout line 13 to upload line 15. Successful-upload exposure is distinguished from usable token theft. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |
| AB-ART-0002 | ai-reviewed | Anchor moves from curl retrieval line 14 to tar consumption line 15; OWASP principle, illustrative URL and nonliteral study example are distinguished. Reviewer: `ai:opencode:ses_e9cbd3299ffe5p1Jg66UI4O0Z5`. |
| AB-NEG-0004 | ai-reviewed | Constant echo now requests permissions: {}, removing its unused read scope without claiming token absence. Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR`. |
| AB-NEG-0015 | ai-reviewed | Exactly one named key is consumed through the environment for a fixed-message HMAC; no key source/CLI interpolation or raw-key output, explicit missing-key failure, no token permissions. Reviewer: `ai:opencode:ses_e9cbd7f21ffewiQ16lnv744ZmR`. |

Primary evidence:

- [Pinned credential storage](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/src/git-auth-helper.ts#L272-L318),
  [pinned hidden-file search](https://github.com/actions/upload-artifact/blob/043fb46d1a93c77aae656e7c1c64a875d1fc6a0a/src/shared/search.ts),
  [OWASP integrity guidance](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation),
  [zizmor version-sensitive persistence warnings](https://docs.zizmor.sh/audits/#artipacked).
- [Empty permission map](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions),
  [secret availability and environment passing](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions),
  [Python HMAC interface](https://docs.python.org/3/library/hmac.html).

The artifact reviewer cleared the owner-chosen exception without declaring confidentiality
intrinsically an integrity weakness. A nonblocking warning about newer checkout findings
was narrowed: residual credential-persistence warnings need not claim workspace-artifact
leakage, so absence of that leak does not establish scanner incorrectness.

The signing reviewer verified key/message byte types, digest constructor, heredoc syntax,
environment-only key handling and tag-only output. Fork PRs ordinarily lack the key and
fail the empty-key check. Weak-key resistance and a production signing protocol are not
certified; no real signing secret was used.

Four new static tests inspect these conventions without executing corpus code. Real
scanner reruns confirm that zizmor's checkout anchor remains line 12 while the label is
now upload line 15: artifact region counts become **0/1/2**, versus historical **1/0/1**.
This is an anchor mismatch on a positive, not a false alarm on a negative. At line tolerance
3 it matches across steps; regions intentionally do not. All other mapped-class counts
are unchanged. No matcher or rule-map change was made to compensate for the anchor choice.

All 44 cases now carry scoped AI evidence review. No human agreement or live end-to-end
validation follows from that status, and future material edits still require re-review.

## Follow-up priorities

1. The two reachability blockers are resolved in the unreleased revision above. Keep the
   static-versus-live evidence distinction; scanner detection does not itself prove execution.
2. AB-NEG-0007 now avoids the ambiguous old pin and has scoped agent approval. Upstream's
   advisory/source inconsistency remains documented, not resolved through an exploit claim.
3. All four remaining boundary cases are now resolved and agent-reviewed under ADR 0006.
   Preserve the explicit class exception, corrected sinks, least-authority fixtures and
   disclosed score change when preparing the next corpus release.
4. Seek independent human review. None of these sessions supplies `agreed` status, the
   PRD's independent-review milestone, or justification for public rankings.
