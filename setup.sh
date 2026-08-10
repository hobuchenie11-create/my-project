#!/usr/bin/env bash
# Provision the automontage engine: OpenMontage (agent + tools) + Remotion
# (animation, titles, transitions). Safe to re-run — every step is idempotent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE="$ROOT/engine/OpenMontage"
OPENMONTAGE_REPO="${OPENMONTAGE_REPO:-https://github.com/calesthio/OpenMontage.git}"

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

# --- system dependencies ---------------------------------------------------
step "Checking system dependencies"
missing=()
have git  || missing+=("git")
have node || missing+=("nodejs (18+)")
have npm  || missing+=("npm")
have python3 || missing+=("python3 (3.10+)")
if ((${#missing[@]})); then
  echo "Install these first: ${missing[*]}" >&2
  exit 1
fi

if ! have ffmpeg || ! have ffprobe; then
  echo "ffmpeg/ffprobe missing — attempting install"
  if have apt-get; then
    (sudo -n true 2>/dev/null && SUDO=sudo || SUDO="")
    $SUDO apt-get update -qq || true
    # --no-install-recommends skips the VA driver packages, which are optional
    # for our use and frequently 404 on stale mirrors.
    $SUDO apt-get install -y --no-install-recommends ffmpeg
  elif have brew; then
    brew install ffmpeg
  else
    echo "Install ffmpeg manually: https://ffmpeg.org/download.html" >&2
    exit 1
  fi
fi
echo "node $(node -v) · python $(python3 -V 2>&1 | cut -d' ' -f2) · $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

# --- OpenMontage -----------------------------------------------------------
step "Fetching OpenMontage"
mkdir -p "$ROOT/engine"
if [ -d "$ENGINE/.git" ]; then
  echo "already cloned — pulling"
  git -C "$ENGINE" pull --ff-only || echo "pull skipped (local changes)"
else
  git clone --depth 1 "$OPENMONTAGE_REPO" "$ENGINE"
fi

# --- Python side -----------------------------------------------------------
step "Installing Python dependencies"
[ -d "$ROOT/.venv" ] || python3 -m venv "$ROOT/.venv"
PIP="$ROOT/.venv/bin/pip"
"$PIP" install -q --upgrade pip
"$PIP" install -q -r "$ENGINE/requirements.txt"
# Local speech-to-text for captions, the Claude SDK for --select llm, and
# HEIC support — ffmpeg has no HEIF demuxer, so iPhone photos need transcoding.
"$PIP" install -q faster-whisper anthropic pillow-heif
echo "installed into $ROOT/.venv"

# --- Remotion --------------------------------------------------------------
step "Installing Remotion"
# Our config makes the headless browser environment-driven; the upstream
# checkout ships none, so install it after every clone/pull.
cp "$ROOT/montage/remotion/remotion.config.ts" "$ENGINE/remotion-composer/remotion.config.ts"
(cd "$ENGINE/remotion-composer" && npm install --no-audit --no-fund)
echo "remotion $(cd "$ENGINE/remotion-composer" && node -p "require('remotion/package.json').version")"

# --- Remotion browser ------------------------------------------------------
# Remotion renders in headless Chrome. It downloads its own by default, but
# locked-down networks block that, so prefer a Chromium that is already here.
step "Checking the Remotion renderer"
BROWSER=""
for candidate in \
  /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell \
  /opt/pw-browsers/chromium-*/chrome-linux/chrome; do
  [ -x "$candidate" ] && BROWSER="$candidate" && break
done
[ -z "$BROWSER" ] && BROWSER="$(command -v chromium chromium-browser google-chrome 2>/dev/null | head -1 || true)"

if [ -n "$BROWSER" ]; then
  echo "using local browser: $BROWSER"
else
  echo "no local Chromium found — Remotion will download its own on first render"
fi

step "Done"
cat <<EOF

Run a montage with:

  ./automontage <video-file>

EOF
