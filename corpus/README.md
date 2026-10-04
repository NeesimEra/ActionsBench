# Corpus

Labeled test cases for GitHub Actions workflow scanners. Each directory under `cases/` is a
fake repository root plus a `case.yaml` label. How cases are labeled, reviewed and scored:
[docs/methodology.md](../docs/methodology.md). How to add one:
[CONTRIBUTING.md](../CONTRIBUTING.md).

**These workflows are deliberately vulnerable and are never executed.** GitHub only runs
workflows at the repository root's `.github/workflows/`; these live inside
`corpus/cases/<id>/.github/`. Do not copy them into a real repository.

Tools that scan this repository as a whole will see these files. Exclude `corpus/` when
scanning the repository itself.

## License

The corpus is licensed under [CC BY 4.0](LICENSE), separately from the code (MIT). When you
reuse it, credit ActionsBench and state the corpus version.

## ID scheme

`AB-<CLASS>-NNNN`, where the class code is the case's primary weakness class, or `NEG` for a
clean case that looks risky but is safe.

| Code | Class |
|---|---|
| ART | artifact-integrity |
| CTL | control-flow |
| PRM | excessive-permission |
| RUN | runner-compatibility |
| HRD | hardening-gap |
| INJ | injection |
| KVC | known-vulnerable-component |
| TRG | privileged-trigger |
| SEC | secrets-exposure |
| PIN | unpinned-dependency |
| NEG | negative (clean) |

## Current contents

| Cases | What they test |
|---|---|
| AB-INJ-0001 to 0003 | Untrusted values wrapped in expression functions (`format()`, `contains(...) &&`, `toJSON()`) |
| AB-INJ-0004, 0005 | Branch name and commit author name as untrusted inputs |
| AB-INJ-0006 | A non-shell sink: `actions/github-script` |
| AB-INJ-0007 | A composite action with a tainted input and shallow YAML indentation |
| AB-PIN-0001, 0002 | An action referenced by a mutable tag, and by a branch |
| AB-PRM-0001 | `permissions: write-all` |
| AB-TRG-0001 | `pull_request_target` that checks out and builds the pull request head |
| AB-SEC-0001 | `secrets: inherit` passed to a reusable workflow |
| AB-KVC-0001 | An action pinned to a version inside a published advisory's vulnerable range |
| AB-RUN-0001 | A job that targets the retired `ubuntu-18.04` runner image |
| AB-CTL-0001 | A step guarded by the constant condition `if: ${{ true }}` |
| AB-ART-0001 | Checkout credentials uploaded inside a workflow artifact |
| AB-INJ-0008 to 0010 | Untrusted values on a deep line of a multi-line script, in an issue title, and in a review comment |
| AB-PIN-0003 | A reusable workflow referenced by a tag |
| AB-PRM-0002 | Workflow-level `contents: write` |
| AB-SEC-0002, 0003 | A hardcoded container registry password, and `toJSON(secrets)` in a step's environment |
| AB-KVC-0002 | `shivammathur/setup-php` pinned inside a second advisory's vulnerable range |
| AB-RUN-0002 | The retired `macos-10.15` runner image |
| AB-ART-0002 | An archive downloaded and unpacked without an integrity check |
| AB-NEG-0001 to 0018 | Clean twins and probes. 0001 to 0009:  environment-variable indirection, boolean-only `contains()`, a pinned action, read-only permissions, a `pull_request` head checkout, a single named secret, the patched action version, credentials not persisted, and a real condition. 0010 to 0018: `pull_request_target` with nothing untrusted (a definitional split), a multi-line script via the environment, safe contexts (the pull request number and the commit SHA), a pinned reusable workflow, credentials from secrets, one named secret, the patched setup-php, `macos-latest`, and a checksum-verified download |

Every label is `proposed`: one reviewer, not yet independently checked.

## Classes not covered yet

- **hardening-gap.** In the source study this class is the *absence* of integrated security
  tooling (for example no static analysis step, or publishing with a long-lived token instead of
  trusted publishing). An absence has no natural line to anchor a label to, and some of the
  study's rules for it work at repository level. Before adding cases the project has to decide
  whether this class belongs in a per-workflow benchmark and where an absence is anchored.

The paper's classes are defined by grouping the rules of real scanners, so they are broader than
their one-line definitions (for example, persisted checkout credentials are filed under
artifact integrity). Each case's rationale states the concrete pattern, and notes say where a
class assignment is debatable.
