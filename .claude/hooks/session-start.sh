#!/bin/bash
# SessionStart hook: install the rtk CLI so the committed PreToolUse hook
# (rtk hook claude) can compress command output and save tokens.
#
# The remote web container is ephemeral, so rtk must be reinstalled on every
# new session. This script is idempotent and safe to run repeatedly.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions. Local machines are
# expected to manage their own rtk installation.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Pin a known-good release: version auto-detection (GitHub /releases/latest
# redirect + REST API) is blocked by the web sandbox proxy, so we pin instead.
# Bump this to upgrade rtk.
RTK_VERSION="${RTK_VERSION:-v0.43.0}"
export RTK_VERSION

# Ensure the install target is on PATH for this session and for later commands.
export PATH="$HOME/.local/bin:$PATH"
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

# Install rtk only if the pinned version isn't already present (idempotent).
if command -v rtk >/dev/null 2>&1 && rtk --version 2>/dev/null | grep -q "${RTK_VERSION#v}"; then
  echo "rtk ${RTK_VERSION} already installed" >&2
else
  echo "Installing rtk ${RTK_VERSION}..." >&2
  # The installer verifies the release SHA-256 checksum before installing.
  curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh 1>&2
fi

# Optional: install rtk's RTK.md usage guidance for the assistant. We use
# --no-patch so it does NOT touch settings.json (the PreToolUse hook already
# lives in the committed project settings), avoiding a duplicate hook.
rtk init -g --no-patch >/dev/null 2>&1 || true

exit 0
