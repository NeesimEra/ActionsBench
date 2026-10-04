# Evidence audit

**Date:** 2026-10-04. **Scope:** all 44 cases in the corpus. **Method:** desk research against primary
sources, plus one experiment, with nobody else involved.

## What this is, and what it is not

For each case this audit checks the *facts the label rests on*: is the context attacker-controlled, does the
advisory range hold, was the runner image retired, what does the shell actually do with the expanded text, what
does the pinned action version really do. It records the evidence and the result.

It does **not** make a label `agreed`. `agreed` means an independent person checked the label, and a re-read by
the author, or by the same assistant that wrote the cases, is not independent. Verifying facts is necessary for a
trustworthy label but not sufficient: the choice of class, the anchoring, and where a case sits on a definitional
boundary are judgements. Those cases are marked `J` below, and they remain contestable. Every case stays
`proposed`.

## Result codes

| Code | Meaning |
|---|---|
| D | Demonstrated: run with GitHub's published expression engine and a real shell ([tools/verify-expressions](../tools/verify-expressions/README.md)) |
| P | Confirmed in primary documentation (GitHub, the tools' own docs, OWASP, the action's README) |
| A | Confirmed in advisory or API data, with the commits resolved from the repository |
| S | Confirmed in the source code of the action at the pinned version |
| J | Depends on a judgement that desk research cannot settle |

Counts over 44 cases (a case can carry several codes): D 13, P 35, A 4, S 2, J 4.

## Defects the audit found

1. **AB-ART-0001 and its twin AB-NEG-0008 described a weakness that did not exist at the version they pinned.**
   They used `actions/checkout` 7.0.1 and claimed the job token ends up in `.git/config` inside the uploaded
   workspace. The checkout changelog says 6.0.0 "Persist creds to a separate file", and the source confirms it:
   at 7.0.1 credentials live in a file under `RUNNER_TEMP` and `.git/config` holds only an `includeIf` path,
   while at 4.2.2 `configureToken` writes the token into `<workspace>/.git/config`. Both cases now pin 4.2.2
   (commit resolved from the repository), and the twin is confirmed to remove the token when
   `persist-credentials` is false. Side effect worth knowing: zizmor flags a checkout without
   `persist-credentials: false` at both versions tried (4.2.2 and 7.0.1), so at a newer checkout that finding is
   arguably a false alarm.
2. **AB-SEC-0001 omitted a documented restriction.** `secrets: inherit` only works for a called workflow in the
   same organization or enterprise as the caller. The fictional example organization is now stated to be the
   caller's own.
3. **AB-INJ-0004 cited an advisory about `github.ref`, not `github.ref_name`.** The case now says so and records
   that the two are the long and short forms of the same branch or tag name, and that git accepts a payload
   branch name as valid.

Found earlier by running the tools, not by this audit, and already fixed: two cases that were not valid YAML, a
note that misdescribed how a class is scored, and a claim that region matching equals a one-line tolerance.

## Per-case results

| Case | What the label rests on | Evidence | Result |
|---|---|---|---|
| AB-ART-0001 | at checkout 4.2.2 the token is written to .git/config and an upload with hidden files includes it | checkout source at 4.2.2 and 7.0.1, changelog 6.0.0, upload-artifact metadata. **A defect was found and fixed here** | S P J |
| AB-ART-0002 | an archive used without an integrity check is an artifact-integrity weakness | OWASP CICD-SEC-9 (definition, Codecov example); the study's example. The class fit is a judgement | P J |
| AB-CTL-0001 | a constant true condition guards nothing | actionlint docs (constant condition message). Whether this is a security weakness is the paper's class definition | P J |
| AB-INJ-0001 | format() returns text containing the value, which is expanded into the script before the shell runs | tools/verify-expressions: payload ran. Secure-use page: the expression is used during script generation | D P |
| AB-INJ-0002 | `a && b` yields b when a is truthy, so the untrusted head_ref reaches the script | tools/verify-expressions: payload ran | D |
| AB-INJ-0003 | toJSON() output is a double-quoted string and command substitution still runs inside double quotes | tools/verify-expressions: evaluated to a quoted string, payload ran | D |
| AB-INJ-0004 | a branch name can carry shell metacharacters and ref_name reaches the script | tools/verify-expressions plus `git check-ref-format`; toolhive advisory (github.ref) and Ken Muse article (a real attack's branch name) | D P |
| AB-INJ-0005 | head_commit.author.name is attacker-controlled and reaches the script | tools/verify-expressions; actionlint's documented list of untrusted properties | D P |
| AB-INJ-0006 | the script input is JavaScript and expressions are evaluated before it | actions/github-script README, quoted | P |
| AB-INJ-0007 | the caller's untrusted value flows through an input into the composite action's script | tools/verify-expressions (inputs.title) | D |
| AB-INJ-0008 | an untrusted value on a deep line of a multi-line script is expanded the same way | tools/verify-expressions; actionlint's list | D P |
| AB-INJ-0009 | the issue title is attacker-controlled and reaches the script | tools/verify-expressions; actionlint's list; zizmor's own example | D P |
| AB-INJ-0010 | the review comment body is attacker-controlled and reaches the script | tools/verify-expressions; actionlint's list | D P |
| AB-KVC-0001 | the pinned action version is inside the advisory's vulnerable range | GitHub advisories API (>= 4.0.0, < 4.1.3, patched 4.1.3); the commit was resolved from the repository | A |
| AB-KVC-0002 | the pinned action version is inside the advisory's vulnerable range | GitHub advisories API (>= 2.25.0, < 2.37.1, patched 2.37.1); both commits resolved, the patched one is 'Bump version to 2.37.1' | A |
| AB-NEG-0001 | a value passed through an environment variable is not parsed as script | tools/verify-expressions: payload printed, did not run; secure-use page recommends it | D P |
| AB-NEG-0002 | a boolean-only contains() cannot inject | tools/verify-expressions: evaluates to true; actionlint docs | D P |
| AB-NEG-0003 | a full commit SHA is immutable | Secure-use page | P |
| AB-NEG-0004 | read-only is the recommended default | Secure-use page | P |
| AB-NEG-0005 | pull_request from a fork gets no write token or secrets | GitHub Security Lab article, quoted | P |
| AB-NEG-0006 | passing one named secret is the least-authority form | zizmor docs | P |
| AB-NEG-0007 | 4.1.3 is the patched version | GitHub advisories API; the commit was resolved | A |
| AB-NEG-0008 | with persist-credentials false the step removes the token | checkout 4.2.2 source: removeAuth runs when persistCredentials is false | S |
| AB-NEG-0009 | a real condition restricts when the step runs | actionlint docs | P |
| AB-NEG-0010 | the trigger alone, with nothing untrusted, is not the class by the paper's definition | The study's definition versus zizmor's rule, which flags the trigger itself. A deliberate definitional split | J |
| AB-NEG-0011 | an environment variable keeps the value out of a multi-line script | tools/verify-expressions; secure-use page | D P |
| AB-NEG-0012 | the pull request number and the commit SHA cannot carry a payload | tools/verify-expressions (42 and hex); absent from actionlint's list; zizmor docs | D P |
| AB-NEG-0013 | a pinned reusable workflow is immutable | Reusable-workflow docs | P |
| AB-NEG-0014 | credentials from the secrets context is the recommended form | actionlint docs; zizmor docs | P |
| AB-NEG-0015 | one named secret is the recommended form | zizmor docs | P |
| AB-NEG-0016 | 2.37.1 is the patched version | GitHub advisories API; the commit resolved | A |
| AB-NEG-0017 | macos-latest is a maintained label | actionlint's documented label list | P |
| AB-NEG-0018 | verifying a checksum before use addresses the weakness | OWASP CICD-SEC-9 (the Codecov tampering was detected by comparing hashes) | P |
| AB-PIN-0001 | a tag can be moved, and only a full commit SHA is immutable | Secure-use page, quoted twice | P |
| AB-PIN-0002 | a branch ref moves on every push | Secure-use page | P |
| AB-PIN-0003 | a reusable workflow reference has the same floating-ref risk as an action's | Reusable-workflow docs: the commit SHA is the safest option | P |
| AB-PRM-0001 | write-all grants more than the job needs | Secure-use page: minimum required permissions, default read; actionlint docs: write-all is a valid value | P |
| AB-PRM-0002 | workflow-level write is inherited by every job | Secure-use page; zizmor docs | P |
| AB-RUN-0001 | the ubuntu-18.04 image was retired | runner-images issue #6002 (fully unsupported by 2023-04-03); GitHub changelog; absent from actionlint's label list | P |
| AB-RUN-0002 | the macos-10.15 image was removed | GitHub changelog 2022-07-20 (removed by 2022-08-30); runner-images issue #5583 | P |
| AB-SEC-0001 | secrets: inherit implicitly passes the secrets to the called workflow | Reusable-workflow docs; zizmor docs | P |
| AB-SEC-0002 | a literal registry password in the workflow is a credential exposure | zizmor docs (its example is `password: hackme`); actionlint docs | P |
| AB-SEC-0003 | toJSON(secrets) hands every secret to a step that needs none | zizmor docs (overprovisioned-secrets) | P |
| AB-TRG-0001 | pull_request_target combined with checking out untrusted pull request code is dangerous | GitHub Security Lab article, quoted | P |

## What this audit does not establish

- **Live GitHub behavior.** The expression experiment uses `@actions/expressions` 0.3.61, which calls itself "one
  of multiple implementations" of the language; the runner's C# code is the reference. The substitution of the
  evaluated expression into the script is modeled from GitHub's documentation, not observed on a live runner.
  The checkout behavior comes from reading source at pinned tags, not from running a workflow. A live run would be
  a stronger check, and needs a workflow execution.
- **The JavaScript sink.** AB-INJ-0006 rests on the action's README; the experiment covers shell sinks only.
- **Judgement.** Cases marked J, and the choice of class for every case, are not settled by sources.
- **Tool behavior.** What each scanner reports is recorded in `status.md` from real runs, separately.
- **Independent review and maintainer feedback.** Neither has happened; see plan.md gates A and C.

## Reproducing

```bash
# the experiment (injection and clean-twin semantics)
cd tools/verify-expressions && npm ci --ignore-scripts && npm run verify

# an advisory range, read from GitHub's API
gh api /advisories/GHSA-cxww-7g56-2vh6 --jq '.vulnerabilities[] | [.package.name, .vulnerable_version_range, .first_patched_version]'
gh api /advisories/GHSA-pqwm-q9pv-ph8r --jq '.vulnerabilities[] | [.package.name, .vulnerable_version_range, .first_patched_version]'

# where checkout writes the token at each version
gh api 'repos/actions/checkout/contents/src/git-auth-helper.ts?ref=11bd71901bbe5b1630ceea73d27597364c9af683' -H 'Accept: application/vnd.github.raw' | grep -n "configureToken\|'.git', 'config'"
gh api 'repos/actions/checkout/contents/src/git-auth-helper.ts?ref=3d3c42e5aac5ba805825da76410c181273ba90b1' -H 'Accept: application/vnd.github.raw' | grep -n "credentialsConfigPath\|includeIf"
```

The experiment is not part of CI yet; it needs Node and an npm install, so it is run by hand when labels or the
injection cases change.

## Sources read for this audit

- GitHub, [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- GitHub, [Reusing workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- GitHub Security Lab, [Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)
- actions/checkout, [README](https://github.com/actions/checkout/blob/main/README.md), [CHANGELOG](https://github.com/actions/checkout/blob/main/CHANGELOG.md) and `src/git-auth-helper.ts` at the 4.2.2 and 7.0.1 commits
- actions/github-script, [README](https://github.com/actions/github-script/blob/main/README.md)
- actions/upload-artifact, `action.yml` at the pinned commit
- actionlint, [checks documentation](https://github.com/rhysd/actionlint/blob/main/docs/checks.md); zizmor, [audits](https://docs.zizmor.sh/audits/)
- OWASP, [CICD-SEC-9](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation)
- GitHub advisories GHSA-cxww-7g56-2vh6 and GHSA-pqwm-q9pv-ph8r (API), toolhive GHSA-g976-wp3r-q8c6, Ken Muse, [The Hidden Danger in Git Ref Names](https://www.kenmuse.com/blog/the-hidden-danger-in-git-ref-names/)
- `@actions/expressions` 0.3.61 (MIT, from `actions/languageservices`)
