"""Behavioral tests for scripts/install-poutine.sh.

The script is exercised end to end with a PATH shim in place of curl, so these tests
touch no network: every file the script downloads is a fixture the test generated.
The extracted `poutine` is a test-generated stub that records its own execution, which
lets the tests prove a checksum-mismatch or missing-manifest-entry aborts *before* the
downloaded tarball is extracted or anything in it is run.
"""

from __future__ import annotations

import hashlib
import io
import os
import platform
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install-poutine.sh"
VERSION = "1.1.6"

# Same derivation as the script: poutine_<os>_<arch>.tar.gz.


def _asset_name() -> str:
    arch = "x86_64" if platform.machine().lower() in ("x86_64", "amd64") else "arm64"
    return f"poutine_{platform.system()}_{arch}.tar.gz"


ASSET = _asset_name()


def _build_tarball(path: Path, marker: Path) -> str:
    """A tarball with one executable stub; returns its sha256."""
    stub = f"#!/bin/sh\necho executed > '{marker}'\necho 'poutine {VERSION} stub'\n"
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo("poutine")
        blob = stub.encode()
        info.size = len(blob)
        info.mode = 0o755
        tar.addfile(info, fileobj=io.BytesIO(blob))
    return hashlib.sha256(path.read_bytes()).hexdigest()


CURL_SHIM = """\
#!/bin/sh
out=
url=
prev=
for arg in "$@"; do
  if [ "$prev" = "-o" ]; then out=$arg; prev=; continue; fi
  prev=$arg
  url=$arg
done
case "${url##*/}" in
  *_checksums.txt) cp "{fixture}/checksums.txt" "$out" ;;
  *) cp "{fixture}/poutine.tar.gz" "$out" ;;
esac
"""


@dataclass(frozen=True)
class InstallerBox:
    """Everything a test needs about its sandbox: script copy, expected install site,
    the fixture curl directory and its generated files."""

    script: Path
    dest: Path
    marker: Path
    fixture: Path
    sha: str
    tmpdir: Path


@pytest.fixture
def sandbox(tmp_path: Path) -> InstallerBox:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "scripts" / "install-poutine.sh")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    marker = tmp_path / "marker"
    sha = _build_tarball(fixture / "poutine.tar.gz", marker)
    (fixture / "curl").write_text(CURL_SHIM.replace("{fixture}", str(fixture)))
    (fixture / "curl").chmod(0o755)
    return InstallerBox(
        script=root / "scripts" / "install-poutine.sh",
        dest=root / ".tools" / f"poutine-{VERSION}",
        marker=marker,
        fixture=fixture,
        sha=sha,
        tmpdir=tmp_path / "script-tmp",
    )


def _run(box: InstallerBox, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    box.tmpdir.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PATH"] = str(box.fixture) + os.pathsep + env["PATH"]
    env["TMPDIR"] = str(box.tmpdir)
    return subprocess.run(
        ["sh", str(box.script), *(args or [])],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_installer_verifies_a_good_checksum_before_running_the_tool(sandbox: InstallerBox) -> None:
    box = sandbox
    box.fixture.joinpath("checksums.txt").write_text(f"{box.sha}  {ASSET}\n")
    result = _run(box)
    assert result.returncode == 0, result.stderr
    assert "checksum verified" in result.stdout
    assert box.dest.joinpath("poutine").is_file()
    assert os.access(box.dest / "poutine", os.X_OK)
    assert box.marker.read_text().strip() == "executed"


def test_installer_refuses_a_checksum_mismatch_before_extraction_or_execution(
    sandbox: InstallerBox,
) -> None:
    box = sandbox
    box.fixture.joinpath("checksums.txt").write_text(f"a2b3c4  {ASSET}\n")
    result = _run(box)
    assert result.returncode != 0
    assert "checksum mismatch" in result.stderr
    assert not box.dest.joinpath("poutine").exists()
    assert not box.marker.exists()


def test_installer_refuses_an_asset_missing_from_the_manifest(sandbox: InstallerBox) -> None:
    box = sandbox
    box.fixture.joinpath("checksums.txt").write_text(
        "0000000000000000000000000000000000000000000000000000000000000001  decoy.tar.gz\n"
    )
    result = _run(box)
    assert result.returncode != 0
    assert "is not listed" in result.stderr
    assert not box.dest.joinpath("poutine").exists()
    assert not box.marker.exists()


def test_installer_rejects_a_nonnumeric_version(sandbox: InstallerBox) -> None:
    result = _run(sandbox, args=["1.1.6-dev"])
    assert result.returncode != 0
    assert "numeric release version" in result.stderr
