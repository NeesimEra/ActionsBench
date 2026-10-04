# verify-expressions

An evidence check for the injection cases in the corpus. It evaluates each case's expression with
GitHub's own published engine (`@actions/expressions`), puts the result into the script text the way
GitHub does before the shell runs, runs that script in bash, and checks whether a harmless canary file
appeared. Clean twins must not run the payload. It exits non-zero if any result differs from what the
labels claim.

```bash
cd tools/verify-expressions
npm ci --ignore-scripts
npm run verify
```

`--ignore-scripts` matters: the package is pinned to an exact version with its integrity hash in
`package-lock.json`, and nothing it installs should run code at install time.

What it shows and what it does not: see [docs/evidence-audit.md](../../docs/evidence-audit.md). In short,
it demonstrates the shell semantics against GitHub's published JavaScript implementation of the
expression language. It does not run on a live GitHub runner, and the package README calls the library
"one of multiple implementations" of the language, so the C# reference implementation could differ.

Everything runs in a throwaway temporary directory and the only side effect is `touch`.
