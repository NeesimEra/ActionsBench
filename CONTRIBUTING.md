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

## Branches and pull requests

- **`dev` is the default branch and the only target for pull requests.** Branch from `dev`
  (for example `feat/...`, `fix/...`, `docs/...`) and open the pull request against `dev`. It
  is squash-merged, and the pull request title becomes the commit title, so write it as a
  Conventional Commit.
- **`main` is the released state.** It changes only through a release pull request from `dev`,
  merged with a merge commit by a maintainer. Release tags (`v*`) are created on `main` and are
  immutable.
- The required check **PR target** fails any pull request whose base is not `dev`, except the
  release pull request from `dev` into `main`. If it fails, change the base branch of your pull
  request to `dev`; the check re-runs on its own.
- Direct pushes to `dev` and `main` are blocked. Both CI checks must pass.

Reasoning and trade-offs: [ADR 0004](docs/adr/0004-branching-model.md).

### Releasing (maintainers)

1. Update `corpus/CHANGELOG.md` on `dev` through a normal pull request.
2. Open a pull request from `dev` to `main` titled `release: vX.Y.Z` and merge it with a merge
   commit.
3. Tag the merge commit `vX.Y.Z` on `main`. Tags cannot be moved or deleted.

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

Two adapters exist so far (zizmor and actionlint). Add another only after checking the tool's
real output:

1. Run the tool by hand on an isolated copy of a case's `.github/` and read its raw output.
   Record the version and the exact flags that make the run deterministic.
2. Add `src/actionsbench/adapters/<tool>.py` implementing the contract in `adapters/base.py`:
   the command, accepted exit codes, a parser, a pinned version, and a rule map. Use `prepare`
   if the tool needs something in the isolated copy (actionlint needs a project marker) and
   `probe_version` if the tool does not print its version in its output. If the tool is a
   binary, add a pinned installer under `scripts/` that verifies a checksum.
   If any setting changes the tool's verdict (zizmor's persona is one), expose it through
   `from_options`, pass it to the tool explicitly, and report it in `configuration`; the
   baseline is the tool's default made explicit.
3. Map only rules whose meaning you have reviewed against a benchmark class. Everything else
   stays unmapped and is reported by the runner. Record each decision, mapped or deliberately not
   mapped, in [docs/rule-mappings.md](docs/rule-mappings.md), including where you disagree with
   the source study. Never map a rule just because it fired on a labeled case. Set `scope` to the classes that have a
   reviewed mapping, not to everything the tool claims.
4. Add unit tests with a trimmed real output sample, and an opt-in integration test
   (`pytest -m integration`) that runs the real tool.
5. Register it in `adapters/__init__.py` and say in the pull request which rules you mapped and
   why.

Any scanner can also be scored without an adapter by producing a findings file that matches
[findings.schema.json](src/actionsbench/schemas/findings.schema.json).

## License

By contributing you agree that your contribution is licensed under the license of the part
of the repository it touches: MIT for code, CC BY 4.0 for the corpus under `corpus/`.
