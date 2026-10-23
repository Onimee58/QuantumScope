#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
case "${1:-auto}" in
  nvidia) exec ./run_nvidia.sh ;;
  default|intel) exec ./run_default.sh ;;
  auto)
    if command -v nvidia-smi >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
      exec ./run_nvidia.sh
    else
      exec ./run_default.sh
    fi ;;
  *) echo "Usage: ./run.sh [auto|nvidia|default]" >&2; exit 2 ;;
esac
