#!/bin/sh
# Install a pinned actionlint release into .tools/ and verify its checksum.
#
#   scripts/install-actionlint.sh            # installs the pinned default version
#   scripts/install-actionlint.sh 1.7.12     # installs a specific version
#
# The binary is written to .tools/actionlint-<version>/actionlint (gitignored). The adapter
# looks for it there, then in $ACTIONSBENCH_ACTIONLINT, then on PATH.
#
# The checksum comes from the same GitHub release as the archive and is fetched over HTTPS. It
# detects a corrupted or altered download, but it is not a signature: it does not protect
# against a compromised release. Review the version you pin.

set -eu

# Keep in sync with PINNED_VERSION in src/actionsbench/adapters/actionlint.py
# (a unit test checks that they match).
DEFAULT_VERSION="1.7.12"
VERSION="${1:-$DEFAULT_VERSION}"

case "$(uname -s)" in
  Darwin) os="darwin" ;;
  Linux) os="linux" ;;
  *) echo "error: unsupported OS $(uname -s); install actionlint $VERSION manually" >&2; exit 1 ;;
esac
case "$(uname -m)" in
  x86_64 | amd64) arch="amd64" ;;
  arm64 | aarch64) arch="arm64" ;;
  *) echo "error: unsupported architecture $(uname -m)" >&2; exit 1 ;;
esac

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/.tools/actionlint-$VERSION"
asset="actionlint_${VERSION}_${os}_${arch}.tar.gz"
checksums="actionlint_${VERSION}_checksums.txt"
base="https://github.com/rhysd/actionlint/releases/download/v${VERSION}"

if [ -x "$dest/actionlint" ]; then
  echo "already installed: $dest/actionlint"
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "downloading $asset"
curl -fsSL -o "$tmp/$asset" "$base/$asset"
curl -fsSL -o "$tmp/$checksums" "$base/$checksums"

expected="$(grep " $asset\$" "$tmp/$checksums" | awk '{print $1}')"
if [ -z "$expected" ]; then
  echo "error: $asset is not listed in $checksums" >&2
  exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$tmp/$asset" | awk '{print $1}')"
else
  actual="$(shasum -a 256 "$tmp/$asset" | awk '{print $1}')"
fi
if [ "$expected" != "$actual" ]; then
  echo "error: checksum mismatch for $asset" >&2
  echo "  expected $expected" >&2
  echo "  actual   $actual" >&2
  exit 1
fi
echo "checksum verified: $actual"

mkdir -p "$dest"
tar -xzf "$tmp/$asset" -C "$tmp" actionlint
mv "$tmp/actionlint" "$dest/actionlint"
chmod +x "$dest/actionlint"
echo "installed: $dest/actionlint"
"$dest/actionlint" -version | head -1
