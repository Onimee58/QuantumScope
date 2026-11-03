#!/usr/bin/env bash
# Runs the optional GUI tests reliably.
#
# Tests that use the 3-D (VTK) view — the Hydrogen tests and each whole-window test file — run in
# their own processes: when they share one with the many Qt widgets the other GUI tests create, the
# process can crash at random (seen since v0.6.2), while each group passes on its own.
#
# Usage: tools/run_gui_tests.sh   (uses .venv/bin/python when present)
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
export QUANTUMSCOPE_GUI_TESTS=1
[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || export QT_QPA_PLATFORM=offscreen
status=0
"$PY" -m pytest -q tests/test_v050_hydrogen_gui.py || status=1
for file in tests/test_*_mainwindow_gui.py; do              # each whole-window file on its own
    "$PY" -m pytest -q "$file" || status=1
done
others=$(ls tests/test_*_gui.py | grep -v -e test_v050_hydrogen_gui.py -e _mainwindow_gui.py)
"$PY" -m pytest -q $others || status=1
exit $status
