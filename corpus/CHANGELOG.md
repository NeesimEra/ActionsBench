# Corpus changelog

Corpus versions are immutable once released. A new version adds or amends cases; it never
silently rewrites old ones. Each case records the version that introduced it in `added_in`.

## Unreleased (0.1.0)

Seed set of 9 cases (7 positive, 2 negative), all `proposed`:

- AB-INJ-0001: untrusted value wrapped in `format()`
- AB-INJ-0002: `contains(...) && untrusted value`
- AB-INJ-0003: untrusted value passed through `toJSON()`
- AB-INJ-0004: branch name (`github.ref_name`)
- AB-INJ-0005: commit author name (`head_commit.author.name`)
- AB-INJ-0006: untrusted value in an `actions/github-script` script
- AB-INJ-0007: composite action sink with a tainted input and shallow indentation
- AB-NEG-0001: untrusted value passed through an environment variable
- AB-NEG-0002: `contains()` used as a boolean condition only
