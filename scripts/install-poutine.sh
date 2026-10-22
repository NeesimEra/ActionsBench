#!/bin/sh
# Install the pinned release into .tools/, checking the release's SHA-256 manifest.
# This detects download corruption, not a compromised upstream release.
set -eu

# Keep in sync with PINNED_VERSION in src/actionsbench/adapters/poutine.py.
DEFAULT_VERSION="1.1.6"
VERSION="${1:-$DEFAULT_VERSION}"
case "$VERSION" in
  '' | *[!0-9.]*) echo "error: expected a numeric release version" >&2; exit 1 ;;
esac
case "$(uname -s)" in
  Darwin) os="Darwin" ;;
  Linux) os="Linux" ;;
  *) echo "error: unsupported OS" >&2; exit 1 ;;
esac
case "$(uname -m)" in
  x86_64 | amd64) arch="x86_64" ;;
  arm64 | aarch64) arch="arm64" ;;
  *) echo "error: unsupported architecture" >&2; exit 1 ;;
esac

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/.tools/poutine-$VERSION"
asset="poutine_${os}_${arch}.tar.gz"
checksums="poutine_${VERSION}_checksums.txt"
base="https://github.com/boostsecurityio/poutine/releases/download/v${VERSION}"
if [ -x "$dest/poutine" ]; then
  echo "already installed: $dest/poutine"
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/$asset" "$base/$asset"
curl -fsSL -o "$tmp/$checksums" "$base/$checksums"
expected="$(awk -v asset="$asset" '$2 == asset {print $1}' "$tmp/$checksums")"
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
  exit 1
fi
echo "checksum verified: $actual"
tar -xzf "$tmp/$asset" -C "$tmp" poutine
mkdir -p "$dest"
mv "$tmp/poutine" "$dest/poutine"
chmod +x "$dest/poutine"
"$dest/poutine" version --disable-version-check
