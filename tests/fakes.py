"""A fake scanner for exercising the runner without any real tool.

Each behavior is a tiny Python program run as the "scanner". It receives the scan directory as
its first argument and prints SARIF (or misbehaves) so every runner rule can be tested
deterministically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from actionsbench.adapters.base import ScannerOutput, ScannerOutputError
from actionsbench.sarif import parse_sarif
from actionsbench.taxonomy import WeaknessClass

RULE_MAP = {"fake/inj": WeaknessClass.INJECTION}

OK_EMPTY = (
    "import json; print(json.dumps({'version': '2.1.0', 'runs': "
    "[{'tool': {'driver': {'name': 'fake', 'version': '9.9'}}, 'results': []}]}))"
)

# One mapped finding at line 13 of the first workflow, plus one unmapped result.
FINDS = r"""
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
wf = sorted((root / ".github" / "workflows").glob("*.yml"))[0]
rel = wf.relative_to(root).as_posix()
def res(rule, line):
    return {"ruleId": rule, "locations": [{"physicalLocation": {
        "artifactLocation": {"uri": rel}, "region": {"startLine": line}}}]}
doc = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "fake", "version": "9.9"}},
       "results": [res("fake/inj", 13), res("fake/other", 1)]}]}
print(json.dumps(doc))
"""

# Fails (exit 3) if the scanner can see the label file or runs inside the corpus.
ISOLATION_PROBE = r"""
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
if (root / "case.yaml").exists() or "corpus" in root.parts or pathlib.Path.cwd() != root.resolve():
    sys.exit(3)
print(json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "fake",
      "version": "9.9"}}, "results": []}]}))
"""

EXIT_2 = "import sys; sys.stderr.write('boom\\n'); sys.exit(2)"
GARBAGE = "print('not json at all')"
SLEEP = "import time; time.sleep(30)"

BAD_PATH = (
    "import json; print(json.dumps({'version': '2.1.0', 'runs': [{'tool': {'driver': "
    "{'name': 'fake', 'version': '9.9'}}, 'results': [{'ruleId': 'fake/inj', 'locations': "
    "[{'physicalLocation': {'artifactLocation': {'uri': 'corpus/cases/x/.github/workflows/"
    "nope.yml'}, 'region': {'startLine': 3}}}]}]}]}))"
)

WRONG_VERSION = OK_EMPTY.replace("9.9", "1.0")


class FakeAdapter:
    name = "fake"
    scope = frozenset({WeaknessClass.INJECTION})
    ok_exit_codes = frozenset({0})
    raw_suffix = "sarif"

    def __init__(
        self,
        script: str,
        *,
        expected_version: str | None = "9.9",
        launcher: str | None = None,
        probed_version: str | None = None,
        marker: str | None = None,
        configuration: str | None = None,
    ) -> None:
        self._script = script
        self._launcher = launcher or sys.executable
        self.expected_version = expected_version
        self.probed_version = probed_version
        self.marker = marker
        self._configuration = configuration

    @property
    def label(self) -> str:
        return "fake-9.9"

    @property
    def configuration(self) -> str | None:
        return self._configuration

    def probe_version(self) -> str | None:
        return self.probed_version

    def prepare(self, scan_dir: Path) -> None:
        if self.marker:
            (scan_dir / self.marker).mkdir()

    def command(self, scan_dir: Path) -> list[str]:
        return [self._launcher, "-c", self._script, str(scan_dir)]

    def parse(self, stdout: str, *, case_id: str, scan_dir: Path) -> ScannerOutput:
        try:
            document = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ScannerOutputError(str(exc)) from exc
        parsed = parse_sarif(document, case_id=case_id, case_root=scan_dir, rule_map=RULE_MAP)
        return ScannerOutput(
            findings=parsed.findings,
            unmapped_rule_ids=parsed.unmapped_rule_ids,
            locationless=parsed.locationless,
            reported_version=document["runs"][0]["tool"]["driver"].get("version"),
        )


# Fails (exit 4) unless the prepare hook ran first and left its marker directory behind.
NEEDS_MARKER = r"""
import json, pathlib, sys
if not (pathlib.Path(sys.argv[1]) / ".marker").is_dir():
    sys.exit(4)
print(json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "fake",
      "version": "9.9"}}, "results": []}]}))
"""
