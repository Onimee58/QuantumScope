#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/quantumscope ]]; then
  echo "QuantumScope is not installed. Run ./install_and_run.sh first." >&2
  exit 1
fi
export QT_QPA_PLATFORM=xcb
export QT_XCB_GL_INTEGRATION=xcb_glx
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
exec .venv/bin/quantumscope
