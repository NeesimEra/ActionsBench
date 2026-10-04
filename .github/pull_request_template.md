## What changed

<!-- One or two sentences. -->

## Checklist

- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest` pass
- [ ] `uv run actionsbench validate` passes

If this adds or changes a corpus case:

- [ ] The case is minimal and single-purpose (one weakness, or a clean negative)
- [ ] Every `uses:` is pinned to a full commit SHA and the workflow sets `permissions:`,
      unless the case is about exactly that
- [ ] The payload is benign and contains no real secrets or live vulnerabilities
- [ ] `rationale` explains why the label is correct and `references` supports it
- [ ] `status` is `proposed`; an independent reviewer sets it to `agreed`
- [ ] The label is anchored at the sink, and `evidence` appears on the labeled line
