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

## Current contents (seed set)

| Cases | What they test |
|---|---|
| AB-INJ-0001 to 0003 | Untrusted values wrapped in expression functions (`format()`, `contains(...) &&`, `toJSON()`) |
| AB-INJ-0004, 0005 | Branch name and commit author name as untrusted inputs |
| AB-INJ-0006 | A non-shell sink: `actions/github-script` |
| AB-INJ-0007 | A composite action with a tainted input and shallow YAML indentation |
| AB-NEG-0001, 0002 | Safe patterns that look risky (environment-variable indirection, boolean-only `contains()`) |

Every seed label is `proposed`: one reviewer, not yet independently checked.
