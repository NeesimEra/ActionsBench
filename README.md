# ActionsBench

A labeled benchmark and evaluation harness for GitHub Actions workflow security scanners.

> **Status: pre-alpha, not published.** The corpus is a 9-case seed set, every label is
> still `proposed` (one reviewer), and the license has not been chosen yet. Nothing here
> is a result yet.

## Why this exists

Several open-source scanners analyze GitHub Actions workflows for security weaknesses,
and they disagree widely. In a 2026 study of 9 scanners on 2,722 real workflows, one tool
reported 107 injection findings where another reported 1,778 on the same files. The same
study found no verified, labeled dataset of workflows with known weaknesses, so precision
and recall could not be computed ([arXiv 2601.14455](https://arxiv.org/html/2601.14455v2)).

ActionsBench provides the missing piece:

1. A **labeled corpus** of minimized workflows, each tagged with the weakness it contains,
   or marked clean.
2. A **harness** that scores any scanner against the corpus, per weakness class.
3. **Versioned, reproducible releases** so results stay comparable over time.

It is not a scanner, and it does not rank tools. It reports per-class evidence.

Full motivation, scope and risks: [docs/PRD.md](docs/PRD.md).

## Quickstart

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run actionsbench validate      # check every case in corpus/cases
uv run actionsbench stats         # cases per weakness class
uv run actionsbench score findings.json
```

`score` takes a normalized findings file (schema:
[findings.schema.json](src/actionsbench/schemas/findings.schema.json)), so any scanner can
be scored today by producing that file. Built-in scanner adapters come later (see
[plan.md](plan.md)).

Run the commands from the repository root, or pass `--corpus` explicitly.

## How scoring works

- A tool is judged only on the weakness classes it declares in `scope`. Anything outside
  that scope is reported as a coverage gap, never as a miss or a false alarm.
- Cases the tool did not run on are excluded, not counted as clean.
- Matching is one-to-one (class, file, line within a tolerance), so duplicate findings do
  not inflate recall.
- Results are per class. There is no overall score on purpose.

Details: [docs/methodology.md](docs/methodology.md).

## Repository layout

| Path | Contents |
|---|---|
| `corpus/cases/` | The labeled cases. Each case directory is a fake repository root plus a `case.yaml`. |
| `src/actionsbench/` | Corpus loader and validator, SARIF parser, scorer, CLI. |
| `src/actionsbench/schemas/` | JSON Schemas for `case.yaml` and the findings file (the public contracts). |
| `docs/` | PRD, methodology, architecture decision records. |
| `plan.md`, `status.md` | The work plan with human gates, and an append-only progress log. |

## A note on the corpus

The cases contain deliberately vulnerable workflows. They are inert: GitHub only runs
workflows under the repository root's `.github/workflows/`, and these live inside
`corpus/cases/`. Payloads are benign placeholders. Never copy them into a real repository.
See [SECURITY.md](SECURITY.md).

## Contributing

Labels are claims, and they are meant to be challenged. See
[CONTRIBUTING.md](CONTRIBUTING.md) for adding cases, challenging a label, and the
development setup.

## License

Not chosen yet. This is a deliberate decision gate (plan.md, gate B), so please do not
assume any license until one is added.
