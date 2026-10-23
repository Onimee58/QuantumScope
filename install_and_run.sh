#!/usr/bin/env bash
set -Eeuo pipefail

# QuantumScope v0.1.2: install dependencies, create venv, and launch GUI.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f pyproject.toml ]]; then
  echo "Error: Put install_and_run.sh inside the QuantumScope project folder (next to pyproject.toml)." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed." >&2
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' ; then
  echo "Error: Python 3.11 or newer is required." >&2
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  echo "[1/4] Installing Ubuntu/Debian system libraries (sudo may ask for your password)..."
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
else
  echo "[1/4] Skipping apt dependencies (not an apt-based Linux distribution)."
  echo "       Install Python venv, OpenGL, EGL and X11/Qt runtime libraries with your package manager."
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "[2/4] Creating local Python environment..."
  python3 -m venv .venv
else
  echo "[2/4] Reusing existing .venv"
fi

echo "[3/4] Installing QuantumScope and Python dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "Warning: No graphical display was detected. The GUI may not launch in a headless session." >&2
fi

echo "[4/4] Launching QuantumScope..."
exec .venv/bin/quantumscope
