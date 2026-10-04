# ADR 0001: Python harness with a minimal dependency set

**Status:** Accepted (2026-10-04). Reversible; see Consequences.

## Context

The PRD left the harness language open (open question 4). The harness runs scanner
binaries, parses JSON and SARIF, validates YAML against JSON Schema, and computes
per-class counts. It is small glue code. The real work and the real value are in the
corpus labels.

## Decision

- **Language:** Python 3.11 or newer.
- **Tooling:** uv for environments and the lockfile, hatchling as the build backend, ruff
  for lint and formatting, mypy in strict mode, pytest.
- **Runtime dependencies, two only:**
  - `pyyaml`: read `case.yaml` (`safe_load` only).
  - `jsonschema`: validate `case.yaml` and the findings file against the published schemas.
- **CLI:** the standard library's `argparse`, to avoid a third dependency.
- **Data model:** standard-library dataclasses, not a validation framework.

## Why

- The task is glue between command-line tools and data files, which Python handles with
  little code and fast iteration during the spike.
- The people most likely to label and review cases (security researchers, academics) tend
  to work in Python. This is an assumption; contributor demographics were not measured.
- The author works fluently in it.
- The language matters less than usual: the corpus (YAML plus files) and the findings
  contract (JSON Schema) are language-neutral, and any scanner can already be scored in any
  language by producing a findings file.

## Consequences

- **Distribution:** users need Python and uv. Tools like zizmor (Rust) and actionlint (Go)
  ship as single binaries, which security users often prefer.
- **Dependency footprint:** `jsonschema` brings in a compiled package (`rpds-py`) through
  `referencing`. For a security project this is a real, if small, supply-chain surface. It
  is accepted because the JSON Schemas are the public contract and hand-rolling a validator
  would be worse.
- **Type safety:** weaker than Go or Rust, mitigated by strict mypy in CI.
- **Reversibility:** the harness is a few hundred lines. Rewriting it in another language
  would not touch the corpus or the schemas.

## Alternatives considered

- **Go or Rust:** single static binary and a closer fit to the scanner ecosystem, but slower
  iteration and, probably, a smaller pool of contributors who would also label cases.
- **TypeScript:** familiar to the author and common in the Actions ecosystem, but it adds a
  build step for no clear gain.
- **Pydantic instead of dataclasses plus JSON Schema:** better ergonomics, but a larger
  dependency and it would not give non-Python users a schema to validate against.
