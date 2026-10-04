# Contributing

Labels are claims, and the project improves when they are challenged. There are three
ways to help: add a case, challenge a label, or improve the harness.

## Development setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
uv run actionsbench validate
```

CI runs the same commands on Python 3.11 and 3.13.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, with a scope when useful, for
example `feat(corpus): add AB-INJ-0008`). Keep unrelated changes in separate commits.

## Adding a case

Read [docs/methodology.md](docs/methodology.md) first. In short:

1. Create `corpus/cases/<id>/` containing the workflow files under `.github/` and a
   `case.yaml`. Use the next free ID. The ID prefix is the case's primary weakness class
   (`INJ`, `PIN`, ...) or `NEG` for a clean case that looks risky but is safe.
2. Keep the case minimal and single-purpose. Pin every `uses:` to a full commit SHA and
   set `permissions:` unless the case is about exactly that, so that only the intended
   weakness is labeled.
3. Anchor each expected finding at the **sink**: the line where untrusted data reaches the
   interpreter. Put a short `evidence` substring that appears on that line.
4. Write a `rationale` a reviewer can check, and add `references`. If you reasoned the
   label from first principles and found no independent source, say so in the rationale.
5. Leave `status: proposed` and `reviewer: null`. An independent reviewer moves a case to
   `agreed`. You cannot review your own case.
6. Run `uv run actionsbench validate`.

Never add a workflow from a real repository that still has a live vulnerability, real
secrets, or anything that works as a real exploit. See [SECURITY.md](SECURITY.md).

## Challenging a label

Open an issue with the **Challenge a label** template. Include evidence: documentation,
an advisory, or a minimal reproduction. A challenge that cannot be resolved marks the case
`disputed`; it is not deleted. The outcome is recorded in the case's `notes`.

## Reviewing a case

Read the workflow, decide independently whether the label is right, then set `status:
agreed` and your handle as `reviewer` in a pull request, or comment on the case's pull
request or issue if you disagree.

## Adding a scanner adapter

Not open yet. Per-tool adapters are added in the M0 spike (plan.md), after each tool's
real output has been checked. In the meantime, any scanner can be scored by producing a
findings file that matches
[findings.schema.json](src/actionsbench/schemas/findings.schema.json).

## License

The project has no license yet (plan.md, gate B). Please wait for one before contributing
substantial work.
