#!/usr/bin/env python3
"""Check a built wheel the way a user receives it.

    uv build && uv run python scripts/check_wheel.py dist/*.whl

First it checks the contents: every case of the repository's corpus is packaged with its `.github/`
files, and both licenses and both schemas are present. Then it installs the wheel into a clean
virtual environment and runs the installed command from an empty directory, so the bundled corpus
is the only one it can find. The exit code is non-zero if anything is wrong.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def packaged_cases(names: list[str]) -> set[str]:
    prefix = "actionsbench/_corpus/cases/"
    return {n.split("/")[3] for n in names if n.startswith(prefix) and n.endswith("/case.yaml")}


def check_contents(wheel: Path) -> list[str]:
    problems: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()

    expected = {p.name for p in (ROOT / "corpus" / "cases").iterdir() if p.is_dir()}
    packaged = packaged_cases(names)
    if packaged != expected:
        problems.append(
            "packaged cases differ from the repository corpus: "
            f"missing {sorted(expected - packaged)}, unexpected {sorted(packaged - expected)}"
        )
    for case in sorted(packaged):
        has_workflow = any(
            n.startswith(f"actionsbench/_corpus/cases/{case}/.github/")
            and n.endswith((".yml", ".yaml"))
            for n in names
        )
        if not has_workflow:
            problems.append(f"case {case} has no workflow file under .github/ in the wheel")

    for suffix in ("licenses/LICENSE", "licenses/corpus/LICENSE"):
        if not any(n.endswith(suffix) for n in names):
            problems.append(f"missing license file {suffix}")
    for schema in ("case.schema.json", "findings.schema.json"):
        if f"actionsbench/schemas/{schema}" not in names:
            problems.append(f"missing schema {schema}")
    return problems


def check_install(wheel: Path) -> list[str]:
    problems: list[str] = []
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    expected_cases = sum(1 for p in (ROOT / "corpus" / "cases").iterdir() if p.is_dir())
    with tempfile.TemporaryDirectory(prefix="actionsbench-wheel-") as tmp:
        venv = Path(tmp) / "venv"
        subprocess.run(["uv", "venv", "-q", str(venv)], check=True)
        bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        subprocess.run(
            ["uv", "pip", "install", "-q", "--python", str(python), str(wheel)], check=True
        )

        empty = Path(tmp) / "empty"
        empty.mkdir()
        command = bin_dir / ("actionsbench.exe" if os.name == "nt" else "actionsbench")

        reported = subprocess.run(
            [str(command), "--version"], capture_output=True, text=True, cwd=empty
        )
        if reported.stdout.strip() != f"actionsbench {version}":
            problems.append(f"installed version is {reported.stdout.strip()!r}, expected {version}")

        validated = subprocess.run(
            [str(command), "validate"], capture_output=True, text=True, cwd=empty
        )
        want = f"OK: {expected_cases} case(s) valid."
        if validated.returncode != 0 or want not in validated.stdout:
            problems.append(
                "the installed command could not validate the bundled corpus "
                "from an empty directory: "
                f"exit {validated.returncode}, stdout {validated.stdout.strip()!r}, "
                f"stderr {validated.stderr.strip()[:300]!r}"
            )
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    wheel = Path(argv[1])
    if not wheel.is_file():
        print(f"error: {wheel} does not exist", file=sys.stderr)
        return 2

    problems = check_contents(wheel) + check_install(wheel)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"OK: {wheel.name} bundles the corpus and works from an empty directory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
