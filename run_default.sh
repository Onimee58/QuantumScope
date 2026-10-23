#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/quantumscope ]]; then
  echo "QuantumScope is not installed. Run ./install_and_run.sh first." >&2
  exit 1
fi
unset QT_XCB_GL_INTEGRATION __NV_PRIME_RENDER_OFFLOAD __GLX_VENDOR_LIBRARY_NAME
exec .venv/bin/quantumscope
