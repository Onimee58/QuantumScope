#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
export QT_QPA_PLATFORM=xcb
export QT_XCB_GL_INTEGRATION=xcb_glx
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
exec ./QuantumScope/QuantumScope "$@"
