# Corpus changelog

Corpus versions are immutable once released. A new version adds or amends cases; it never
silently rewrites old ones. Each case records the version that introduced it in `added_in`.

## Unreleased (0.1.0)

Seed set of 25 cases (16 positive, 9 negative), all `proposed`.

Injection (first batch):

- AB-INJ-0001: untrusted value wrapped in `format()`
- AB-INJ-0002: `contains(...) && untrusted value`
- AB-INJ-0003: untrusted value passed through `toJSON()`
- AB-INJ-0004: branch name (`github.ref_name`)
- AB-INJ-0005: commit author name (`head_commit.author.name`)
- AB-INJ-0006: untrusted value in an `actions/github-script` script
- AB-INJ-0007: composite action sink with a tainted input and shallow indentation
- AB-NEG-0001: untrusted value passed through an environment variable
- AB-NEG-0002: `contains()` used as a boolean condition only

Other classes (second batch, each positive has a clean twin):

- AB-PIN-0001, AB-PIN-0002: action referenced by a tag, by a branch
- AB-PRM-0001: `permissions: write-all`
- AB-TRG-0001: `pull_request_target` checking out and building the pull request head
- AB-SEC-0001: `secrets: inherit` to a reusable workflow
- AB-KVC-0001: action pinned inside a published advisory's vulnerable range
- AB-RUN-0001: retired `ubuntu-18.04` runner image
- AB-CTL-0001: constant `if` condition
- AB-ART-0001: checkout credentials uploaded in an artifact
- AB-NEG-0003 to 0009: clean twins for the above
