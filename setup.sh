#!/usr/bin/env bash
# Provision the automontage engine on macOS / Linux.
#
# The real work lives in setup.py so that Windows and POSIX share one tested
# code path; this wrapper only finds a Python to run it with.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done

if [ -z "$PY" ]; then
  echo "Python 3.10+ не найден. Установите его и запустите ещё раз." >&2
  exit 1
fi

exec "$PY" "$ROOT/setup.py" "$@"
