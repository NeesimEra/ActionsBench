# ActionsBench (working name) — Product Requirements Document

**Status:** Draft v0.1
**Date:** 2026-10-04
**Owner:** Aliu Tijani
**Product type:** Open-source benchmark and evaluation harness
**Domain:** Security of GitHub Actions workflows
**License:** MIT (code), CC BY 4.0 (corpus)

The name is a working name. On 2026-10-04 no GitHub repository, PyPI package or npm package named `actionsbench` was found. The GitHub organization handle, domain and trademark position have not been checked.

---

## 1. Summary

Several open-source scanners analyze GitHub Actions workflows for security weaknesses. They report very different results on the same files, and there is no verified, labeled dataset that says which findings are correct. As a result, nobody can measure a scanner's precision or recall, compare scanners fairly, or detect regressions against a shared standard.

ActionsBench is an open benchmark that fills that gap:

1. A **labeled corpus** of minimized workflows, each tagged with the weakness it contains, or marked clean.
2. An **evaluation harness** that runs any scanner against the corpus and reports precision, recall and coverage per weakness class.
3. **Versioned, reproducible releases** of both the corpus and the published results.

It is not a new scanner and it does not declare a single "best" tool. It publishes per-class evidence so maintainers and users can see where each tool is strong or weak.

---

## 2. Problem

### 2.1 Scanners disagree, and no one can say who is right

A 2026 study compared 9 open-source scanners (actionlint, frizbee, ggshield, pinny, poutine, scharf, scorecard, semgrep, zizmor) on 2,722 real-world workflows. Examples of the disagreement:

- Injection weakness: poutine reported 107 findings, zizmor reported 1,778.
- Artifact integrity weakness: poutine reported 125, zizmor reported 3,620.
- Unpinned dependencies: three tools differed by more than 2,000 findings.

The authors attribute this to different analysis philosophies: poutine is conservative, while zizmor increases coverage but produces more lower-confidence findings.

### 2.2 There is no ground truth

The same study states there is no verified dataset of workflows labeled with known weaknesses, so it could not compute precision, recall or false-positive rates. Its conclusion is that no scanner performs well across all weakness types, and that users should combine several.

### 2.3 Consequences

- Users stack scanners without knowing what each one covers or misses.
- Maintainers cannot measure improvement or regressions against a shared standard.
- New tools cannot be compared to existing ones. The author hit this directly: a CI scanner built for a student challenge had blind spots (for example, expressions wrapped in `format()` or `toJSON()`, and `github-script` sinks) that nothing could quantify against incumbents.

### 2.4 Why it matters

In March 2026, attackers force-pushed malicious code to most version tags of the `aquasecurity/trivy-action` GitHub Action. Secondary reports say the chain began with a misconfigured `pull_request_target` workflow in Trivy's own repository, which poutine had flagged months earlier. Detection existed, but users had no shared evidence for which tool to trust on that class of weakness. (Secondary sources; a primary source should be checked before citing.)

### 2.5 Evidence limits

- The only quantitative evidence is one study (arXiv, January 2026). Its taxonomy was validated with scanner maintainers, but 5 of them responded.
- The claim that no labeled workflow benchmark exists comes from the study plus a shallow search by the author. It is not confirmed. Related work found: RealVuln (labeled, but for application code, not workflows) and a 41,253-workflow corpus used to harden zizmor (unlabeled, used for robustness).

---

## 3. Goals and non-goals

### Goals

| ID | Goal |
|---|---|
| G1 | Provide a labeled corpus covering the 10 weakness classes, with positive and negative cases. |
| G2 | Provide a harness that runs any supported scanner and scores it per class. |
| G3 | Make scoring transparent: per-class metrics and a coverage matrix, not a single ranking. |
| G4 | Publish immutable, versioned corpus and result releases so results stay comparable over time. |
| G5 | Keep the corpus safe and legal: no live vulnerabilities, benign payloads, clear licensing. |
| G6 | Be maintainer-friendly: a clear process to challenge labels and add cases. |

### Non-goals (v0.1)

- Building a new scanner or auto-fixer.
- Producing a single "best scanner" leaderboard.
- Scoring severity or exploitability.
- Supporting CI systems other than GitHub Actions.
- Cataloguing vulnerabilities in real repositories.
- Scoring the quality of automatic fixes (candidate for a later track, see Milestones).
- A hosted service, API or web frontend. Results are published as versioned static files and
  reports. A static results site may follow once there are results worth browsing; it would
  still need no backend and must show per-class evidence, not a ranking.

---

## 4. Users

| User | Need |
|---|---|
| Scanner maintainers | A shared standard to measure precision and recall and catch regressions. |
| Security and platform engineers | Evidence for choosing and combining scanners. |
| Researchers | A labeled dataset to evaluate new detection approaches. |
| Authors of new scanners (including the project owner) | A fair way to compare against incumbents. |

---

## 5. Product definition

### 5.1 Weakness taxonomy

The starting taxonomy is the 10 classes from the 2026 study, as summarized by the author. The list must be checked against the paper before adoption.

- Artifact integrity
- Control flow
- Excessive permission
- GitHub runner compatibility
- Hardening gap
- Injection
- Known vulnerable component
- Privileged trigger
- Secrets exposure
- Unpinned dependency

### 5.2 Case anatomy

Each case is a small workflow (plus any referenced local actions or reusable workflows) with metadata.

| Field | Meaning |
|---|---|
| id | Stable identifier, never reused. |
| files | The workflow and any referenced files. |
| expected findings | Zero or more entries: weakness class, file, line (or step) where the weakness occurs. |
| is_negative | True for clean cases and for "looks risky but is safe" cases. |
| rationale | Why the label is correct, in plain language. |
| reference | Link to GitHub's security-hardening guidance, an advisory, or an incident. |
| provenance | Synthetic-minimal, or derived from a fixed public advisory (see 5.3). |
| status | `proposed` (one reviewer so far), `agreed` (an independent reviewer confirmed), or `disputed`. |
| reviewers | Who labeled and who independently reviewed. |
| added_in | Corpus version that introduced the case. |

### 5.3 Provenance rules

- **Default: synthetic and minimized.** The author writes the smallest workflow that exhibits the weakness.
- **Derived from fixed public advisories** only, with attribution and a license check. Prefer referencing repo, commit and path over copying content.
- **Never** include a case that exposes a live, unfixed vulnerability in a real repository.
- Payloads are benign placeholders. No working exploit code and no real secrets.

### 5.4 Negative cases

Precision cannot be measured without negatives. The corpus must include:

- Clean workflows that follow best practice.
- Near-miss safe patterns, for example untrusted values passed through an environment variable rather than interpolated into the shell, and `contains()` used purely as a boolean.

### 5.5 Harness

- **Adapters per scanner** convert native output (SARIF or JSON where available) to normalized findings: class, file, line.
- **Scope declaration per tool.** Each tool declares the classes it claims to cover. Results outside claimed scope are reported as coverage gaps, not as failures. This matters because, for example, actionlint is a correctness linter and not primarily a security scanner.
- **Matching rule:** a finding matches an expected finding when class and file match and both lines are in the same region: the same step, the same job outside its steps, or the same top-level key. Decided on 2026-10-04 from real scanner output (ADR 0003). Exact-line matching with an optional tolerance remains available for a strict comparison.
- **Metrics:** per-class precision, recall and F1; a coverage matrix (tool by class); a disagreement report listing cases where tools differ from each other or from the label; runtime per tool.
- **Reproducibility:** scanner versions recorded and pinned; runs executable with one command, ideally containerized.

### 5.6 Label review process

- Two reviewers per case: an author and an independent reviewer.
- Every case carries a written rationale and a reference.
- Cases may be marked disputed. Anyone can challenge a label through an issue, and the outcome is recorded.
- Scanner maintainers are invited to review labels before results are published.

### 5.7 Releases

- Corpus and result releases are immutable and versioned. A new corpus version adds or amends cases and never silently rewrites old ones.
- Each result report states the corpus version and scanner versions it used.

---

## 6. Requirements

### Functional

| ID | Requirement |
|---|---|
| FR1 | A corpus format and validator that rejects malformed cases (missing rationale, reference, reviewers). |
| FR2 | Adapters for zizmor, actionlint and poutine in v0.1. |
| FR3 | An adapter for the author's own challenge scanner as a baseline. |
| FR4 | A scoring command producing per-class metrics, coverage matrix and disagreement report. |
| FR5 | Machine-readable results (JSON) and a human-readable report (Markdown). |
| FR6 | A documented contribution path for new cases and new scanner adapters. |

### Non-functional

- **Reproducibility:** the same corpus version, scanner versions and command give the same results.
- **Safety:** no live vulnerabilities, no real secrets, benign payloads.
- **Licensing clarity:** license stated for code and for corpus data, and provenance recorded per case.
- **Documentation:** a contributor guide and a short methodology note explaining labeling and scoring.

---

## 7. Seed cases

These come from probe workflows the author wrote while testing their own scanner. Labels listed here are proposals to be confirmed under the review process.

| Seed | Description | Proposed class | Notes |
|---|---|---|---|
| S1 | Untrusted value wrapped in `format()` and interpolated in a shell step | Injection | Untrusted text still reaches the shell. |
| S2 | `contains(...) && untrusted-value` used in a shell step | Injection | Looks like a boolean helper, but the expression can return the untrusted value. |
| S3 | Untrusted value passed through `toJSON()` into a shell step | Injection | JSON quoting does not neutralize shell command substitution. To be verified before labeling. |
| S4 | Branch name (`github.ref_name`) interpolated into a shell step | Injection | Depends on git ref names allowing shell metacharacters. To be verified before labeling. |
| S5 | `head_commit.author.name` interpolated into a shell step | Injection | Listed as untrusted in GitHub's guidance as the author recalls. To be verified. |
| S6 | Untrusted value interpolated into a `github-script` script | Injection | A non-shell sink. |
| S7 | Composite action whose `- run:` step uses shallow indentation | Injection | Tests parser robustness, not only rules. |
| N1 | Untrusted value passed through an environment variable and referenced as a shell variable | None (negative) | The recommended safe pattern. |
| N2 | `contains()` used purely as a boolean condition | None (negative) | Tests false positives. |

Patch-validity probes (cases where an auto-generated fix produced invalid YAML or changed shell behavior) are reserved for a possible later autofix track.

---

## 8. Milestones

All estimates are rough, assume one person, and are unvalidated.

| Milestone | Scope | Rough duration |
|---|---|---|
| **M0: Spike** | About 50 labeled cases, 4 scanners run end to end with one command, first disagreement report. | 1 week |
| **[HUMAN_GATE] A** | Go/no-go on the spike result. | — |
| **M1: v0.1** | 150–200 cases across the 10 classes (target to revisit after M0), validator, harness, report, contributor guide. | 3–4 weeks |
| **[HUMAN_GATE] B** | License decision, before the first public push. | — |
| **[HUMAN_GATE] C** | Share results privately with scanner maintainers before naming any tool's weaknesses publicly. | — |
| **M2: Public release** | Maintainer review round, then publish corpus v0.1 and results. | 2 weeks |
| **[HUMAN_GATE] D** | Approval needed before adding any case derived from a real repository. | — |
| **M3: Extensions** | More scanners (scorecard, semgrep, frizbee and others), optional autofix-validity track, other CI systems. | TBD |

---

## 9. Success metrics and kill criteria

### Spike (M0) success

Thresholds are proposals, not researched numbers.

- At least 50 cases labeled with rationale and reference.
- At least 3 scanners plus the baseline run end to end with one command.
- At least 2 weakness classes where some scanner shows a notable miss or false positive against the label, each with a documented rationale.
- A second reviewer agrees with the labels on a sample of 20 cases at 80% or better.

### Kill criteria

Stop or pivot if any of these hold after the spike:

- Scanners agree with the labels on nearly all cases, so there is no story to publish.
- Labeling proves too ambiguous to reach reviewer agreement.
- An equivalent labeled workflow benchmark is found.

### Long-term signals

- Scanner maintainers adopt the corpus in their own CI.
- Issues and pull requests arrive from scanner repositories.
- Results are cited by other work. Stars are a secondary signal.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Labels are contested or wrong | Two reviewers, written rationale and reference per case, a disputed status, maintainer review before publishing. |
| Exposing live vulnerabilities | Synthetic and minimized cases by default; derived cases only from fixed public advisories; gate D. |
| Licensing of content from public repos | Reference repo, commit and path instead of copying; check licenses; gate B. |
| Scanners differ in scope, so scoring looks unfair | Per-tool scope declaration; report coverage gaps separately from failures. |
| Maintainers react badly to published weaknesses | Share results privately first; present per-class evidence, not rankings; gate C. |
| Another group publishes a benchmark first | Re-check prior art at each gate; compare against it and build on it if it exists. |
| Small audience, indirect reward | Accept that this is a reputation project; keep scope small and measurable. |
| Solo maintenance burden | Immutable releases, minimal harness, clear contribution path. |

---

## 11. Prior art and differentiation

| Work | What it is | Difference |
|---|---|---|
| 2026 scanner study (arXiv 2601.14455) | Compares 9 scanners on 2,722 workflows | No ground truth, so no precision or recall. ActionsBench provides the labels. |
| RealVuln | Labeled benchmark with ground truth for scanning application code | Not workflows. |
| zizmor hardening corpus | 41,253 workflows used for robustness testing | Unlabeled. |
| Scanners (zizmor, actionlint, poutine, scorecard, semgrep and others) | Detection tools | Subjects of the benchmark, not competitors. |

---

## 12. Open questions

1. **Name:** `actionsbench` is free as a repo name, PyPI package and npm package (checked 2026-10-04). Still to check: GitHub organization handle, domain, and whether using "Actions" in the name conflicts with GitHub's branding guidelines.
2. **Second reviewer:** who provides independent review of labels? The 80% agreement target depends on this.
3. **License:** decided on 2026-10-04: MIT for code and CC BY 4.0 for the corpus (attribution required for reuse).
4. **Harness language:** decided as Python for now, with reasoning and reversibility in [ADR 0001](adr/0001-python-and-minimal-dependencies.md). Revisit if distribution as a single binary becomes important.
5. **Maintainer outreach timing:** recommended before any public result. Confirm at gate C.
6. **IEEE challenge data:** the terms for reusing competition data are unknown. Do not include any until checked.
7. **Taxonomy verification:** done on 2026-10-04. The paper defines exactly ten classes, with the definitions in the schema. Two observations: the classes are defined by grouping scanner rules, so they are broader than their prose, and hardening-gap is the absence of security tooling, which needs an anchoring rule before it can be labeled (see corpus/README.md).
8. **Prior-art re-check:** the search for an existing labeled workflow benchmark was shallow.

---

## 13. Sources

- Unpacking Security Scanners for GitHub Actions Workflows (arXiv 2601.14455): https://arxiv.org/html/2601.14455v2
- zizmor: https://github.com/zizmorcore/zizmor
- RealVuln benchmark: https://arxiv.org/pdf/2604.13764
- We hardened zizmor's GitHub Actions static analyzer (41,253-workflow corpus): https://securityboulevard.com/2026/05/we-hardened-zizmors-github-actions-static-analyzer/
- Trivy GitHub Actions supply chain compromise (Snyk): https://snyk.io/articles/trivy-github-actions-supply-chain-compromise/
- Trivy supply chain attack (Palo Alto Networks): https://www.paloaltonetworks.com/blog/cloud-security/trivy-supply-chain-attack/

---

## Revision log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-10-04 | Initial draft. |
| 0.1.1 | 2026-10-04 | Scaffold added. Case status gains `proposed`; findings input gains `cases_run` ("not run is not clean"); hosted service and frontend added as a non-goal; harness language decided (ADR 0001); name checked for collisions. |
| 0.1.2 | 2026-10-04 | Licenses chosen (MIT code, CC BY 4.0 corpus) and the repository approved for public release by the owner; gate B visibility and license items closed. |
| 0.1.3 | 2026-10-04 | Matching rule decided: same step, job or top-level key instead of a line tolerance (ADR 0003). Taxonomy verified against the paper. |
