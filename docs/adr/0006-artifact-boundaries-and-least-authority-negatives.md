# ADR 0006: Artifact sink anchors and least-authority negatives

**Status:** Accepted (2026-10-22; owner explicitly chose the artifact classification)

## Decision

- Retain AB-ART-0001 under `artifact-integrity` for compatibility with the source study's
  artipacked mapping. This is an explicit confidentiality-related exception: disclosing
  credentials through an artifact is not itself a content-integrity failure. Preserve
  the case ID and disclose the exception in labels, methodology and rule mappings.
- Anchor that case at the artifact upload `uses:` line, where persisted credentials are
  exposed, not the earlier checkout step that creates the credential file.
- Anchor AB-ART-0002 at archive extraction, where unverified content is consumed. Its
  illustrative curl URL is not the study's literal example or a verified available release.
- No region broadening or scanner-location rewriting. A finding at checkout cannot match
  the upload step simply because both participate in one exposure path. Record the score
  change as an anchor-convention mismatch, not proof that the scanner failed to flag risk.
- Resolve unnecessary access in negatives by changing fixtures, not by declaring all read
  permissions or all single-secret grants necessary. AB-NEG-0004's echo-only job requests
  `permissions: {}`. AB-NEG-0015 uses one named key for a concrete, benign HMAC operation,
  with no token permission, source interpolation, raw-key output or secret CLI argument.

## Consequences

- Expected artifact anchors change in this unreleased corpus. Comparisons must state the
  corpus revision; existing tags and published results are not rewritten.
- Zizmor's checkout anchor may produce a region mismatch despite detecting persisted
  credentials. This is exposed, not “fixed” through tool-specific matching exceptions.
- The HMAC fixture is not a production signing design. Fork PRs without the secret fail
  its explicit empty-key check; no successful secret-bearing run is claimed for them.
- Revised cases require targeted agent review before `ai-reviewed`, still not human `agreed`.
