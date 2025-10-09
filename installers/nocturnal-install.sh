#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${NOCTURNAL_CHANNEL:-beta}"
PACKAGE_SPEC="${NOCTURNAL_PACKAGE_SPEC:-nocturnal-archive}"
PACKAGE_SHA256="${NOCTURNAL_PACKAGE_SHA256:-}"
PYTHON_CMD="${NOCTURNAL_PYTHON:-python3}"
INSTALL_ROOT="${NOCTURNAL_HOME:-$HOME/.nocturnal_archive}"
VENV_DIR="$INSTALL_ROOT/venv"
BIN_DIR="$VENV_DIR/bin"
SETUP_FLAGS=${NOCTURNAL_SETUP_FLAGS:-}
TMP_DOWNLOAD=""

log() {
  printf "[nocturnal-install] %s\n" "$1"
}

cleanup() {
  if [ -n "$TMP_DOWNLOAD" ] && [ -d "$TMP_DOWNLOAD" ]; then
    rm -rf "$TMP_DOWNLOAD"
  fi
}

die() {
  printf "[nocturnal-install] ERROR: %s\n" "$1" >&2
  cleanup
  exit 1
}

trap cleanup EXIT

command -v "$PYTHON_CMD" >/dev/null 2>&1 || die "Python not found. Install Python 3.9+ first."

log "Creating install directory at $INSTALL_ROOT"
mkdir -p "$INSTALL_ROOT"

if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment"
  "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$BIN_DIR/activate"

log "Upgrading pip"
pip install --upgrade pip >/dev/null

EXTRA_INDEX_URL=${NOCTURNAL_EXTRA_INDEX_URL:-}

if [ -n "$PACKAGE_SHA256" ]; then
  log "Downloading package for hash verification"
  TMP_DOWNLOAD=$(mktemp -d)
  DOWNLOAD_CMD=(pip download "$PACKAGE_SPEC" --no-deps -d "$TMP_DOWNLOAD")
  if [ "$CHANNEL" != "stable" ]; then
    DOWNLOAD_CMD+=("--pre")
  fi
  if [ -n "$EXTRA_INDEX_URL" ]; then
    DOWNLOAD_CMD+=("--extra-index-url" "$EXTRA_INDEX_URL")
  fi
  "${DOWNLOAD_CMD[@]}" >/dev/null || die "Unable to download package for verification"

  DOWNLOAD_TARGET=$(
    TMP_DOWNLOAD="$TMP_DOWNLOAD" "$PYTHON_CMD" - <<'PY'
import os, sys
path = os.environ.get('TMP_DOWNLOAD')
if not path or not os.path.isdir(path):
    sys.exit(1)
files = [f for f in os.listdir(path) if not f.startswith('.')]
if not files:
    sys.exit(1)
files.sort()
sys.stdout.write(os.path.join(path, files[0]))
PY
  )
  if [ -z "$DOWNLOAD_TARGET" ] || [ ! -f "$DOWNLOAD_TARGET" ]; then
    die "Downloaded package artifact not found for hash verification"
  fi

  CALCULATED_HASH=$(
    DOWNLOAD_TARGET="$DOWNLOAD_TARGET" "$PYTHON_CMD" - <<'PY'
import hashlib, os, sys
target = os.environ.get('DOWNLOAD_TARGET')
if not target or not os.path.isfile(target):
    sys.exit(1)
sha = hashlib.sha256()
with open(target, 'rb') as fh:
    for chunk in iter(lambda: fh.read(1024 * 1024), b''):
        sha.update(chunk)
sys.stdout.write(sha.hexdigest())
PY
  )
  if [ -z "$CALCULATED_HASH" ]; then
    die "Failed to calculate hash"
  fi
  if [ "${CALCULATED_HASH,,}" != "${PACKAGE_SHA256,,}" ]; then
    die "Hash mismatch for $PACKAGE_SPEC (expected $PACKAGE_SHA256, got $CALCULATED_HASH)"
  fi
  log "Hash verified for $(basename "$DOWNLOAD_TARGET")"
  log "Installing verified artifact"
  pip install "$DOWNLOAD_TARGET" >/dev/null || die "Package install failed"
else
  INSTALL_CMD=(pip install "$PACKAGE_SPEC")
  if [ "$CHANNEL" != "stable" ]; then
    INSTALL_CMD+=("--pre")
  fi
  if [ -n "$EXTRA_INDEX_URL" ]; then
    INSTALL_CMD+=("--extra-index-url" "$EXTRA_INDEX_URL")
  fi
  log "Installing $PACKAGE_SPEC ($CHANNEL channel)"
  "${INSTALL_CMD[@]}" >/dev/null || die "Package install failed"
fi

log "Running nocturnal setup"
NOCTURNAL_ONBOARDING_MODE=beta "${BIN_DIR}/nocturnal" --setup $SETUP_FLAGS

log "Launch the agent any time with: $BIN_DIR/nocturnal"
