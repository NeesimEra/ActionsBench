# Security policy

## What is in this repository

ActionsBench is a benchmark for security scanners, so `corpus/cases/` deliberately contains
vulnerable GitHub Actions workflows. They are inert:

- GitHub only runs workflows under the repository root's `.github/workflows/`. The corpus
  files live deeper, inside `corpus/cases/<id>/.github/`, and are never executed.
- Payloads are benign placeholders. There is no working exploit code and no real secret.
- Do not copy corpus workflows into a real repository.

## What must never be added

- A workflow copied from a real repository that still contains a live, unfixed
  vulnerability. Publishing it would hand out an attack path.
- Real credentials, tokens, or private keys, even revoked ones.
- Cases derived from a real repository without attribution and a license check
  (see plan.md, gate D).

Because the corpus is licensed CC BY 4.0, anything added to it becomes public and
redistributable. Treat a contribution as permanent.

## Reporting a problem

If you find a case that exposes a live issue in a real project, or a vulnerability in the
harness itself (for example, a way a crafted `case.yaml` could read files outside its
directory), please report it privately rather than opening a public issue.

Use GitHub's private vulnerability reporting: open the repository's **Security** tab and
choose **Report a vulnerability**. Only the maintainers can see the report.

## Supported versions

Pre-alpha. There are no supported releases yet.
