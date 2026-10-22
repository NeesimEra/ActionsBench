# Rule mappings

How each scanner's findings are mapped to benchmark classes, and why. This is the review record
behind `RULE_MAP` in `adapters/zizmor.py` and `adapters/poutine.py`, and `KIND_MAP` in
`adapters/actionlint.py`.

**Policy.** A rule is mapped only if:

1. its documentation has been read,
2. its benchmark class is unambiguous, or the choice is recorded here, and
3. a corpus case exercises that class for the tool.

A rule is never mapped because it happened to fire on a labeled case; that would tune the map to
the labels. Everything unmapped is still reported by `actionsbench run` and never dropped.

**Independence.** The source study publishes its own rule-to-class mapping in a repository that
declares no license. It was read for orientation and is not copied. Where this project agrees or
disagrees with it, that is noted below.

**Scope.** A tool's scope is the set of mapped classes the tool can actually detect in the
configuration it was run in. A class outside scope is reported as *uncovered*, never as *missed*.

zizmor and actionlint reviewed on 2026-10-04; poutine on 2026-10-22. These are maintainer-side
mapping reviews, not independent label reviews (see "Limits").

---

## zizmor 1.30.1 (online audits off)

Documentation read: <https://docs.zizmor.sh/audits/>.

### Mapped

| Rule | Class | Why | Exercised by | Study agrees |
|---|---|---|---|---|
| `template-injection` | injection | Flags template expansions of attacker-controllable contexts in code. | AB-INJ-0001 to 0007 | yes |
| `unpinned-uses` | unpinned-dependency | Flags actions not pinned to a commit hash. It also reports a reusable workflow referenced by a tag (AB-PIN-0003), which its documentation does not explicitly promise. | AB-PIN-0001, 0002, 0003 | yes |
| `excessive-permissions` | excessive-permission | Flags over-scoped or missing permission declarations. **Persona-dependent:** at `regular` it reports neither `permissions: write-all` nor a workflow-level `contents: write`; at `pedantic` and `auditor` it reports both. | AB-PRM-0001, 0002 | yes |
| `dangerous-triggers` | privileged-trigger | Flags `pull_request_target`, `workflow_run` and `issue_comment`, which run in the target repository's context. It flags the trigger itself, while the class definition is the *combination* with untrusted data (see AB-TRG-0001 notes). | AB-TRG-0001 | yes |
| `secrets-inherit` | secrets-exposure | Flags `secrets: inherit`, which violates least authority. | AB-SEC-0001 | yes |
| `hardcoded-container-credentials` | secrets-exposure | Flags a literal password in container or service credentials (documentation example: `password: hackme`). | AB-SEC-0002 | yes |
| `overprovisioned-secrets` | secrets-exposure | Flags expanding the whole secrets context, as in `toJSON(secrets)`, where a named secret would do. | AB-SEC-0003 | yes |
| `artipacked` | artifact-integrity | Flags persisted checkout credentials. ADR 0006 explicitly retains the study's confidentiality-related class exception. The case is now anchored at upload, so a checkout-anchored detection is a cross-step mismatch, not a false alarm on a clean workflow. | AB-ART-0001 | yes |

### Deliberately not mapped

| Rule | Reason |
|---|---|
| `known-vulnerable-actions` | The class is clear (known-vulnerable-component) but the audit needs online mode, which the adapter disables for determinism. The class is therefore out of scope for zizmor in this configuration. Revisit if an online configuration is added. |
| `obfuscation` | Fires on AB-CTL-0001 (`if: ${{ true }}`), but its documentation describes obfuscated `uses:` clauses and expressions, not unsound conditions. Mapping it to control-flow would tune the map to my own label. The study files it under runner-compatibility, which does not fit either. |
| `unsound-condition` | Control-flow in spirit, but its documentation was only skimmed and no case exercises it. |
| `github-env`, `bot-conditions`, `cache-poisoning` | Classes are plausible but no corpus case exercises them yet. |
| `impostor-commit`, `ref-confusion` | Online mode only. |
| `self-repository`, `anonymous-definition`, `concurrency-limits` | Style and hygiene findings with no benchmark class. The last two appear on every case at `pedantic` and `auditor`. |

### Scope

injection, unpinned-dependency, excessive-permission, privileged-trigger, secrets-exposure,
artifact-integrity. Out of scope: known-vulnerable-component (needs online mode), control-flow and
runner-compatibility (no reviewed rule), hardening-gap (no cases).

### Revised artifact anchor (2026-10-22)

The owner chose to retain the study-compatible artifact-integrity exception for credential
confidentiality, but anchor AB-ART-0001 at its actual upload sink (line 15). Zizmor 1.30.1
reports checkout at line 12, a different step. With region matching its artifact class now
scores **0 TP / 1 FP / 2 FN** at all three personas, rather than the historical **1/0/1**.
One FP/FN pair is this anchor mismatch; the other FN is unverified archive consumption,
which no mapped rule targets. This is not evidence of a false alarm on a negative workflow.
At line tolerance 3 the checkout finding matches across steps; region matching deliberately
does not. The mapping and matching algorithm are unchanged; do not compare these counts to
released corpus counts without stating the corpus revision.

---

## actionlint 1.7.12

Documentation read: <https://github.com/rhysd/actionlint/blob/main/docs/checks.md>.

### Mapped

| Check | Class | Why | Exercised by | Study agrees |
|---|---|---|---|---|
| `expression`, message "… is potentially untrusted" | injection | The message itself says to avoid the value in inline scripts and pass it through an environment variable. Only this message pattern, not the whole `expression` kind. | AB-INJ-0001 to 0007 | yes |
| `if-cond` | control-flow | Documented as detecting constant conditions that always evaluate to true. | AB-CTL-0001 | yes |
| `runner-label` | runner-compatibility | Flags runner labels that are not valid, a construct that cannot be reliably resolved. | AB-RUN-0001, 0002 | yes |
| `credentials` | secrets-exposure | Flags a literal password in container or service credentials ("password ... should be specified via secrets"). | AB-SEC-0002 | yes |

### Deliberately not mapped

| Check | Reason |
|---|---|
| `permissions` | **Disagrees with the study**, which files it under excessive-permission. The documentation says this check validates scope names and values ("write is invalid for permission for all the scopes"). That is validity, not excess, so it does not detect an over-broad token. |
| `deprecated-commands` | The study files it under injection; its documentation was not read here. |
| `syntax-check`, `shellcheck`, `pyflakes`, `matrix`, `glob`, `events`, `job-needs`, `id`, `env-var`, `workflow-call`, `action`, other `expression` results | Mostly validity checks. The study files most of them under runner-compatibility, but mapping them would claim the whole class on the strength of one construct. See "Limits". `shellcheck` and `pyflakes` are also disabled for determinism. |

### Scope

injection, control-flow, runner-compatibility, secrets-exposure. Everything else is uncovered.

---

## poutine 1.1.6 (local analysis)

Primary sources read at the pinned tag, not the moving default branch:
[README](https://github.com/boostsecurityio/poutine/blob/v1.1.6/README.md),
[rule documentation](https://github.com/boostsecurityio/poutine/tree/v1.1.6/docs/content/en/rules),
[rule source](https://github.com/boostsecurityio/poutine/tree/v1.1.6/opa/rego/rules),
[local analysis](https://github.com/boostsecurityio/poutine/blob/v1.1.6/analyze/analyze.go), and
[SARIF formatter](https://github.com/boostsecurityio/poutine/blob/v1.1.6/formatters/sarif/sarif.go).

All 44 cases were scanned in isolated copies before implementing the adapter. Exit code is 0
with or without findings (no `--fail-on-violation`). Rule IDs have no prefix, paths are
case-relative, and the driver reports `semanticVersion`, not `version`. No git setup or token
is needed. An explicit empty config prevents auto-discovery of `.github/poutine.yml` from
changing the run; `--disable-version-check` disables the upstream update check and telemetry.
Local analysis uses a static reputation client and bundled rule data, not a remote scan.

### Mapped

| Rule | Class | Why | Exercised by |
|---|---|---|---|
| `injection` | injection | Documents attacker-controlled expression interpolation into bash or JavaScript, recommending environment variables instead. | AB-INJ-0005, 0006, 0008, 0009, 0010 |
| `job_all_secrets` | secrets-exposure | Documents exposing the entire secrets object through `toJSON(secrets)` or dynamic keys. | AB-SEC-0003 |
| `untrusted_checkout_exec` | privileged-trigger | Detects executing untrusted checked-out code under privileged events, rather than flagging the trigger alone. | AB-TRG-0001 |

### Deliberately not mapped

| Rule | Reason |
|---|---|
| `github_action_from_unverified_creator_used` | Creator verification is not proof of a vulnerable component. It fires on both the vulnerable and patched setup-php cases; neither finding establishes the labeled advisory. |
| `pr_runs_on_self_hosted` | Documents exposure of self-hosted runners to pull requests, not retired hosted runner compatibility. Its finding on AB-RUN-0002 does not justify mapping it to that label. |
| `unpinnable_action` | Concerns mutable transitive components of known unpinnable actions, not a general check for mutable `uses:` references. No exercising case for this rule here. |
| `if_always_true` | Documents extra characters around expressions. AB-CTL-0001 instead uses a literal true condition and does not exercise that documented pattern. |
| `unverified_script_exec` | Potential artifact-integrity mapping, but no current case exercises the detected script-execution pattern. AB-ART-0002 downloads and extracts an archive, rather than executing a fetched script. |
| `known_vulnerability_in_build_component` | Its pinned rule checks semantic-version references against bundled advisories. The corpus pins vulnerable components by commit SHA; this rule does not exercise those cases. |
| `default_permissions_on_risky_events`, other rules | No exercising case and reviewed mapping for this configuration. Unmapped findings remain visible. |

### Scope and matching limitations

Scope is injection, secrets-exposure and privileged-trigger. Everything else is uncovered.

With the unchanged default region rule, the observed TP/FP/FN counts are injection **5/0/5**,
secrets-exposure **0/1/3**, privileged-trigger **0/1/1**. These are pipeline observations over
proposed labels, not a ranking. Two detections are mismatches because of cross-region anchors:

- `job_all_secrets` points at the job header (AB-SEC-0003 line 9), while the label points at the
  step's `toJSON(secrets)` expression (line 14).
- `untrusted_checkout_exec` points at the build command (AB-TRG-0001 line 19 in the revised
  fixture, originally line 18), while the label points
  at the privileged trigger (line 3).

Each costs one FP and one FN under current matching, despite flagging the declared pattern.
No mapped-class findings occurred on negative cases. Do not interpret these two FPs as false
alarms on clean workflows. The third tool supplies evidence to revisit matching (ADR 0003);
this adapter does not broaden regions, move anchors, or change labels to improve its score.

The later [agent label audit](ai-label-audit-2026-10-22.md) found AB-TRG-0001's pinned
checkout blocked the intended fork checkout, and AB-INJ-0007 lacked local-action provisioning.
Both were repaired and cleared by targeted static agent re-review; they are now `ai-reviewed`.
The observed scanner counts above remain unchanged and are not live execution evidence.

---

## Limits

- **Class-level scope can overstate coverage, and now visibly does.** Some mappings cover only part
  of a broad class: runner-compatibility is far wider than actionlint's single `runner-label` check,
  and actionlint's only secrets check is the hardcoded-credentials one, so the `secrets: inherit` and
  `toJSON(secrets)` cases count as misses for it (zizmor's artifact-integrity coverage, `artipacked`
  alone, likewise charges it with the unverified-download case). When the corpus
  gains cases for other constructs in a mapped class, the mapping has to be revisited, or the tool
  will be charged with misses it was never designed to catch.
- **One reviewer.** These mappings are one person's judgement. They should be challenged like any
  label, through the issue templates.
- **Mappings are tied to the pinned versions.** A new tool version can rename, merge or re-word
  rules; the adapters pin versions and the untrusted-input pattern is an exact message match.
- **Anchoring is separate from mapping.** A tool can detect the right weakness and report it a line
  away from the label. That is a matching question (ADR 0003), not a mapping question.
