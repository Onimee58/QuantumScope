# QuantumScope on Windows (v0.1.3)

## Requirements

- Windows 10/11, 64-bit
- Python 3.11+ (Python 3.12 recommended), installed from python.org, with the Windows `py` launcher if possible
- Updated GPU driver with OpenGL support; internet connection for initial package install

## Install and run

1. Extract the ZIP to a writable folder such as `Documents\QuantumScope`.
2. Double-click **install_and_run_windows.bat** (or launch it from Command Prompt).
3. On later runs, double-click **run_windows.bat**.

The installer creates `.venv` beside the source and installs the Python package with pip. No administrator privileges are required in ordinary setups. Windows SmartScreen may warn about an unsigned downloaded BAT file; review the script before running it.

## Troubleshooting

- Open Command Prompt inside the project directory and run `install_and_run_windows.bat` to see installation errors.
- Confirm a 64-bit Python with `py -3.12 --version` or `python --version`.
- If the window is blank, update the graphics driver and try `set QT_OPENGL=desktop` before `run_windows.bat` (environment-dependent; not guaranteed).
- The `run_nvidia.sh` NVIDIA PRIME command is for Linux only. Windows automatically selects the GPU via its graphics settings: **Settings → System → Display → Graphics**, add `.venv\Scripts\python.exe`, choose **High performance**, and relaunch. Verify the actual GPU via QuantumScope's Graphics diagnostics.
- GPU volume mapper selection controls the VTK mapper, not the operating system's GPU selection.

## Packaging status

This is a **Windows source distribution** with batch launchers, not a signed, bundled `.exe` installer. Linux remains supported. Automated physics tests run on Linux and Windows, but native GUI and GPU rendering must be tested on real Windows hardware.
