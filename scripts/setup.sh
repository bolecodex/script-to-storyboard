#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${ARKCLAW_SKILLS_DIR:-${HOME}/.agents/skills}"

echo "========================================="
echo "  script2storyboard setup"
echo "========================================="

PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    ver=$("$cmd" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)
    major=${ver%%.*}
    minor=${ver#*.}
    if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; }; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "需要 Python >= 3.11。"
  exit 1
fi

echo "Python: $($PYTHON --version)"
echo "Installing CLI from $ROOT_DIR ..."
if ! "$PYTHON" -m pip install -e "$ROOT_DIR"; then
  echo "Direct pip install failed; trying pipx ..."
  if command -v pipx >/dev/null 2>&1; then
    pipx install "$ROOT_DIR" --force
  else
    echo "请先进入 Python 3.11+ 虚拟环境后重试，或安装 pipx。"
    exit 1
  fi
fi

echo "Syncing skills to $SKILLS_DIR ..."
mkdir -p "$SKILLS_DIR"
cp -R "$ROOT_DIR/skills/"* "$SKILLS_DIR/"

echo "Done."
echo "Next:"
echo "  cp .env.example .env"
echo "  script2storyboard auth check"
