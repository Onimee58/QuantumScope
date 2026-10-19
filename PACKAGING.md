# QuantumScope v0.2.0 — Native installers

The **source ZIP** is not an installed application. The GitHub Actions workflow `.github/workflows/release.yml` builds self-contained application folders using PyInstaller and packages these as native installers.

## Build the installers on GitHub

Push this project's contents (including `.github/`) to your repository. In **Actions → Build installable QuantumScope releases → Run workflow**, run the workflow. When both jobs finish, download the two installer artifacts:

- `quantumscope_0.2.0_amd64.deb` — Ubuntu/Debian x86_64 package; launcher appears in desktop applications menu.
- `QuantumScope-0.2.0-Setup.exe` — Windows x64 setup wizard, with optional desktop shortcut and uninstall entry.

To attach installers to a GitHub release, push a version tag **only after testing** (for example `v0.2.0`). Both jobs upload installers to that GitHub Release. An Actions workflow run is not proof of successful GUI rendering: test installers on representative machines first.

## Ubuntu/Debian

Install: `sudo apt install ./quantumscope_0.2.0_amd64.deb`

Launch: `quantumscope` (or the graphical application launcher).

Remove: `sudo apt remove quantumscope`

The package contains the Python runtime and app dependencies via PyInstaller. The host must still provide system graphics libraries and compatible drivers. It is built on Ubuntu 24.04 and is not guaranteed to run on significantly older distributions.

## Windows

Run `QuantumScope-0.2.0-Setup.exe`; follow the wizard and choose whether to create a desktop shortcut. The installed application includes a Start Menu shortcut and an uninstaller. Windows Defender or SmartScreen may flag unsigned executables; signing requires a publisher code-signing certificate and is not included.

## Build scripts

- `packaging/build_deb.sh 0.2.0` packages a Linux `dist/QuantumScope` PyInstaller folder.
- `packaging/QuantumScope.iss` is the Inno Setup 6 installer recipe and expects a Windows `dist/QuantumScope` folder.
- `src/quantumscope/assets/` contains the selected Q/Wave SVG master, PNG raster sizes, and multi-resolution Windows ICO. Use these assets consistently rather than editing copies independently.

**Architectures:** packages currently target amd64/x64 only. There is no ARM package, no package signing, and no automatic update mechanism.
