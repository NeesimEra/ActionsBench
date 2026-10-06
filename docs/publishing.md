# Publishing (maintainers)

Where a release goes:

| Place | What | How |
|---|---|---|
| GitHub release | everything: wheel, sdist, corpus archive, checksums | `gh release create`, see CONTRIBUTING |
| PyPI | the wheel (harness **and** the bundled corpus) and the sdist | the `Publish` workflow, on a published release |
| Zenodo | an archive of the repository with a permanent DOI | automatically, on each published release, once enabled |

## What cannot be undone

- **A PyPI version number can never be reused.** A release can be "yanked" (hidden from new installs) but the
  version stays taken. If a bad version goes out, the fix is the next patch version.
- **A Zenodo DOI is permanent**, and the archive is of the tagged content.
- **A `v*` tag cannot be moved or deleted** (the `immutable-release-tags` ruleset has no bypass).

That is why the workflow checks the tag against the package version, checks the built wheel the way a user
receives it, and waits for a human approval before the PyPI upload.

## One-time setup (web steps only the maintainer can do)

### PyPI and TestPyPI

1. Create an account with two-factor authentication on <https://pypi.org> and, separately, on
   <https://test.pypi.org>.
2. On each site: account settings, **Publishing**, **Add a new pending publisher**, and enter:

   | Field | PyPI | TestPyPI |
   |---|---|---|
   | PyPI project name | `actionsbench` | `actionsbench` |
   | Owner | `NeesimEra` | `NeesimEra` |
   | Repository name | `ActionsBench` | `ActionsBench` |
   | Workflow filename | `publish.yml` | `publish.yml` |
   | Environment name | `pypi` | `testpypi` |

   A pending publisher **does not reserve the name** until the first successful publish, and if someone else
   registers the name first the pending publisher is invalidated (PyPI documentation). Do this soon.

### Zenodo

1. On <https://zenodo.org> choose **Log in with GitHub** and authorize Zenodo. For an organization repository
   an organization owner may need to approve Zenodo's access (GitHub documentation).
2. In Zenodo's GitHub settings, switch **`NeesimEra/ActionsBench`** on.
3. From then on each published GitHub release is archived with a new DOI. Zenodo's documentation does not say
   whether releases that predate enabling are archived; `v0.1.0` predates it and is not expected to be.

Metadata comes from `CITATION.cff` (there is deliberately no `.zenodo.json`, which would override it). Both
files take a **single** license string, so the record names the corpus license (CC BY 4.0), the citable
asset, and the abstract states that the code is MIT.

### GitHub environments (already configured)

`pypi` and `testpypi` require the maintainer's approval before a job that uses them runs. `pypi` accepts only
`v*` tags; `testpypi` accepts only the `dev` and `main` branches. Adjust them under Settings, Environments.

## Release sequence

1. Through a pull request into `dev`: bump the version in `pyproject.toml`, `src/actionsbench/__init__.py` and
   `uv.lock`; update `corpus/CHANGELOG.md`; set `version` and `date-released` in `CITATION.cff`.
2. **Dry run on TestPyPI.** Actions, **Publish**, **Run workflow** on `dev`, then approve the `testpypi`
   deployment. In a clean environment install it and run it from an empty directory:

   ```bash
   uv venv /tmp/t && uv pip install --python /tmp/t/bin/python \
     --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ actionsbench==X.Y.Z
   (cd /tmp && /tmp/t/bin/actionsbench validate)
   ```

   A TestPyPI version is also single-use there, so a failed dry run means bumping the version.
3. Release pull request from `dev` to `main`, merged with a merge commit (ADR 0004).
4. Create the GitHub release, which creates the tag on `main`'s merge commit. That publishes to GitHub, makes
   Zenodo archive it, and starts the `Publish` workflow, which builds, checks, and then **waits for approval**.
5. Approve the `pypi` deployment. Then check the project page on PyPI, install it into a clean environment, run
   `actionsbench validate` from an empty directory, and record the result in `status.md`.
6. Add the Zenodo DOI to the README and `CITATION.cff` in a follow-up pull request.

## If something goes wrong

- **Wrong content on PyPI:** yank that version and release the next patch version.
- **Zenodo did not archive:** the archive reflects the tag, which cannot change, so fix forward in the next
  release.
- **The workflow fails before upload:** nothing was published; fix and re-run, or cut a new version if the
  fix has to be in the tagged content.
