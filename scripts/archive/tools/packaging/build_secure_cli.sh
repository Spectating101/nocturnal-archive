#!/usr/bin/env bash
set -euo pipefail

# Build a hardened, single-file CLI binary using Nuitka.
# Requirements:
#   - Python 3.10+
#   - `pip install nuitka zstandard ordered-set`
#   - On macOS: Xcode command line tools (for clang and otool)
#   - On Linux: GCC/Clang toolchain and patchelf
#   - On Windows: MSVC Build Tools or full Visual Studio build chain
#
# Usage:
#   ./tools/packaging/build_secure_cli.sh [--clean]
#
# The resulting binary will be written to dist/secure/nocturnal (or nocturnal.exe).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
DIST_DIR="$ROOT_DIR/dist/secure"
PYTHON_BIN="${PYTHON_BIN:-python}"
PACKAGE_NAME="nocturnal_archive"
ENTRY_POINT="nocturnal_archive/cli.py"

mkdir -p "$DIST_DIR"
cd "$ROOT_DIR"

if [[ ${1:-} == "--clean" ]]; then
  rm -rf "$DIST_DIR"
  rm -rf build
  find "$ROOT_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +
  echo "✅ Cleaned secure build artifacts."
  exit 0
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "❌ Unable to find Python interpreter: $PYTHON_BIN" >&2
  exit 1
fi

# Ensure Nuitka is available before we start the build.
if ! "$PYTHON_BIN" -m nuitka --version >/dev/null 2>&1; then
  echo "❌ Nuitka isn't installed in the current environment." >&2
  echo "   Install it with: pip install nuitka zstandard ordered-set" >&2
  exit 1
fi

VERSION="$($PYTHON_BIN -c "import importlib.metadata; print(importlib.metadata.version('nocturnal-archive'))")"
OUTPUT_BASENAME="nocturnal-${VERSION}"
PLATFORM_SUFFIX="$(uname | tr '[:upper:]' '[:lower:]')"
[[ "$PLATFORM_SUFFIX" = "darwin" ]] && PLATFORM_SUFFIX="macos"
[[ "$PLATFORM_SUFFIX" = "mingw"* ]] && PLATFORM_SUFFIX="windows"

TARGET_NAME="$OUTPUT_BASENAME-$PLATFORM_SUFFIX"

NUITKA_ARGS=(
  "--onefile"
  "--standalone"
  "--python-flag=no_site"
  "--nofollow-imports"
  "--follow-imports"
  "--include-package=$PACKAGE_NAME"
  "--include-data-files=$ROOT_DIR/docs/USER_GETTING_STARTED.md=docs/USER_GETTING_STARTED.md"
  "--company-name=NocturnalArchive"
  "--product-name=NocturnalArchiveCLI"
  "--product-version=$VERSION"
  "--file-version=$VERSION"
  "--copyright=© $(date +%Y) Nocturnal Archive"
  "--output-dir=$DIST_DIR"
  "--output-filename=$TARGET_NAME"
  "--clang"
)

# Harden bytecode by disabling Python C-API exposure and removing assertions.
NUITKA_ARGS+=(
  "--disable-asserts"
  "--lto=yes"
  "--static-libpython=yes"
  "--remove-output"
  "--nofollow-import-to=tests"
  "--nofollow-import-to=docs"
  "--nofollow-import-to=examples"
)

# Optional encryption of constants/bytecode (Nuitka commercial feature hints).
if [[ -n ${NUITKA_ENCRYPTION_KEY:-} ]]; then
  NUITKA_ARGS+=("--commercial=bytecode-obfuscation" "--commercial=constants-obfuscation")
fi

set -x
"$PYTHON_BIN" -m nuitka "${NUITKA_ARGS[@]}" "$ENTRY_POINT"
set +x

echo "✅ Secure CLI binary created at $DIST_DIR/$TARGET_NAME"

echo "Next steps:"
echo "  • codesign/notarize (macOS) or sign with signtool (Windows)."
echo "  • run \'nocturnal --version\' from the compiled binary to smoke test."
echo "  • distribute alongside a checksum from: sha256sum $DIST_DIR/$TARGET_NAME"
