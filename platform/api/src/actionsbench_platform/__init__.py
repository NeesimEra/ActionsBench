"""Read-only web view of the ActionsBench corpus and per-class results.

The platform is a viewer: it loads the corpus with the harness's own loader, renders case
pages, and scores only findings documents the harness can validate. It never executes
corpus content and never produces an overall score (ADR 0007, docs/platform.md).
"""
