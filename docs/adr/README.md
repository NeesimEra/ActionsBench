# Architecture decision records

Short records of decisions worth remembering, with the alternatives that were rejected.
A superseded decision is not deleted; a new record replaces it and says so.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-python-and-minimal-dependencies.md) | Python harness with a minimal dependency set | Accepted |
| [0002](0002-corpus-format.md) | Cases are fake repositories with a schema-validated `case.yaml` | Accepted |
| [0003](0003-scanner-scope-and-scoring.md) | Per-class scoring with declared scope and explicit `cases_run` | Accepted |
| [0004](0004-branching-model.md) | `dev` is the integration branch and every pull request targets it | Accepted |
