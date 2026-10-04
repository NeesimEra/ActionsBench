# Rule mappings

How each scanner's findings are mapped to benchmark classes, and why. This is the review record
behind `RULE_MAP` in `adapters/zizmor.py` and `KIND_MAP` in `adapters/actionlint.py`.

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

Reviewed on 2026-10-04. Reviewer: the corpus author (single reviewer; see "Limits").

---

## zizmor 1.30.1 (online audits off)

Documentation read: <https://docs.zizmor.sh/audits/>.

### Mapped

| Rule | Class | Why | Exercised by | Study agrees |
|---|---|---|---|---|
| `template-injection` | injection | Flags template expansions of attacker-controllable contexts in code. | AB-INJ-0001 to 0007 | yes |
| `unpinned-uses` | unpinned-dependency | Flags actions not pinned to a commit hash. | AB-PIN-0001, 0002 | yes |
| `excessive-permissions` | excessive-permission | Flags over-scoped or missing permission declarations. **Persona-dependent:** at `regular` it does not report `permissions: write-all`; at `pedantic` and `auditor` it does. | AB-PRM-0001 | yes |
| `dangerous-triggers` | privileged-trigger | Flags `pull_request_target`, `workflow_run` and `issue_comment`, which run in the target repository's context. It flags the trigger itself, while the class definition is the *combination* with untrusted data (see AB-TRG-0001 notes). | AB-TRG-0001 | yes |
| `secrets-inherit` | secrets-exposure | Flags `secrets: inherit`, which violates least authority. | AB-SEC-0001 | yes |
| `artipacked` | artifact-integrity | Flags persisted checkout credentials that can leak through artifacts. **Debatable:** the class's prose is about unvalidated artifacts; the mapping, like the corpus label, follows the source study. | AB-ART-0001 | yes |

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

---

## actionlint 1.7.12

Documentation read: <https://github.com/rhysd/actionlint/blob/main/docs/checks.md>.

### Mapped

| Check | Class | Why | Exercised by | Study agrees |
|---|---|---|---|---|
| `expression`, message "… is potentially untrusted" | injection | The message itself says to avoid the value in inline scripts and pass it through an environment variable. Only this message pattern, not the whole `expression` kind. | AB-INJ-0001 to 0007 | yes |
| `if-cond` | control-flow | Documented as detecting constant conditions that always evaluate to true. | AB-CTL-0001 | yes |
| `runner-label` | runner-compatibility | Flags runner labels that are not valid, a construct that cannot be reliably resolved. | AB-RUN-0001 | yes |

### Deliberately not mapped

| Check | Reason |
|---|---|
| `permissions` | **Disagrees with the study**, which files it under excessive-permission. The documentation says this check validates scope names and values ("write is invalid for permission for all the scopes"). That is validity, not excess, so it does not detect an over-broad token. |
| `credentials` | Semantically secrets-exposure (hardcoded container credentials), but no corpus case exercises it yet. |
| `deprecated-commands` | The study files it under injection; its documentation was not read here. |
| `syntax-check`, `shellcheck`, `pyflakes`, `matrix`, `glob`, `events`, `job-needs`, `id`, `env-var`, `workflow-call`, `action`, other `expression` results | Mostly validity checks. The study files most of them under runner-compatibility, but mapping them would claim the whole class on the strength of one construct. See "Limits". `shellcheck` and `pyflakes` are also disabled for determinism. |

### Scope

injection, control-flow, runner-compatibility. Everything else is uncovered.

---

## Limits

- **Class-level scope can overstate coverage.** Some mappings cover only part of a broad class:
  runner-compatibility is far wider than actionlint's single `runner-label` check. When the corpus
  gains cases for other constructs in a mapped class, the mapping has to be revisited, or the tool
  will be charged with misses it was never designed to catch.
- **One reviewer.** These mappings are one person's judgement. They should be challenged like any
  label, through the issue templates.
- **Mappings are tied to the pinned versions.** A new tool version can rename, merge or re-word
  rules; the adapters pin versions and the untrusted-input pattern is an exact message match.
- **Anchoring is separate from mapping.** A tool can detect the right weakness and report it a line
  away from the label. That is a matching question (ADR 0003), not a mapping question.
