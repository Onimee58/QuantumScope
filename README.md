# QuantumScope

<p align="center">
  <img src="src/quantumscope/assets/quantumscope-256.png"
       alt="QuantumScope Logo"
       width="144"
       height="144">
</p>

<p align="center">
  <strong>Visualizing the Quantum World</strong>
</p>

**Visualizing the Quantum World**

[![Release](https://img.shields.io/github/v/release/Onimee58/QuantumScope?label=release)](https://github.com/Onimee58/QuantumScope/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux-informational)](https://github.com/Onimee58/QuantumScope/releases/latest)

QuantumScope is a free, open-source desktop application for **interactive visualization of quantum mechanics**. Built with Python and PySide6, it brings hydrogen atomic orbitals, time-dependent wavefunctions, and the double-slit experiment into a unified scientific workspace.

**Current release: v0.2.0 — First Stable Release**

**[Download QuantumScope](https://github.com/Onimee58/QuantumScope/releases/tag/v0.2.0)** · [Report an issue](https://github.com/Onimee58/QuantumScope/issues) · [Release notes](https://github.com/Onimee58/QuantumScope/releases/tag/v0.2.0)

## Highlights

- **Modern desktop interface:** Dark and light themes, a persistent tab-based workspace, and a categorized **New Experiment** menu.
- **Hydrogen Explorer:** Interactive 3D renderings of hydrogen orbitals, probability densities, wavefunction amplitudes, and orbital comparisons.
- **Hydrogen Dynamics 2D & 3D:** Animated visualization of time-dependent wavefunctions and superpositions.
- **Double-Slit Experiment:** Illustrated source/barrier/detector apparatus, animated schematic wavefronts, simulated detections, and interference plots.
- **Scientific outputs:** Export options for plots, detection data, and numerical results, as supported by each experiment.
- **Desktop distribution:** Linux Debian packages and Windows setup-wizard builds, with QuantumScope branding.

## Download and install

Visit **[Releases → v0.2.0](https://github.com/Onimee58/QuantumScope/releases/tag/v0.2.0)** and select the asset appropriate for your operating system.

### Windows 10/11 (64-bit)

1. Download the Windows release asset. If it is a `.zip`, extract it first.
2. Run `QuantumScope-0.2.0-Setup.exe` (or the `Setup.exe` included in the extracted asset).
3. Follow the setup wizard and launch QuantumScope from the Start menu or desktop shortcut.

Windows may show a security warning for a new, unsigned open-source installer. Only run installers obtained from the official repository. If an installer is not available in your release assets, see [WINDOWS.md](WINDOWS.md) for source-based setup.

### Ubuntu / Debian (64-bit)

1. Download the Linux release asset. If it is a `.zip`, extract it first.
2. Open a terminal in the folder containing the `.deb` package.
3. Install with:

```bash
sudo apt install ./quantumscope_0.2.0_amd64.deb
```

Then launch **QuantumScope** from your application menu. The precise downloaded `.deb` filename may differ; use the filename from the release asset. A graphical desktop and compatible OpenGL drivers are required for 3D visualizations.

For packaging details, see [PACKAGING.md](PACKAGING.md).

## Experiments

### Hydrogen Explorer

Explore analytical, nonrelativistic hydrogen bound states by choosing the principal, orbital, and magnetic quantum numbers (`n`, `l`, and `m`). Available representations include 3D probability density, isosurfaces, real/imaginary amplitudes, and phase-aware visualizations. Inspect radial probability distributions, energy estimates, and finite-grid diagnostics; compare orbitals and export scientific data.

### Hydrogen Dynamics (2D and 3D)

Visualize the evolution of superposed hydrogen states and the resulting time-dependent probability patterns. Adjustable playback and visualization controls let you explore the spatial and temporal structure of quantum dynamics.

### Double-Slit Experiment

Adjust wavelength, slit separation, slit width, and detector geometry to study how the interference pattern changes. The experiment combines a **schematic apparatus** (source, two apertures, and detector), illustrative wavefront animation, simulated detection events, and a theoretical interference probability distribution. Export detection data to CSV.

> **Scientific note:** The double-slit wavefront display is illustrative; it does not depict measured particle trajectories. The interference calculation uses an idealized Fraunhofer diffraction model, so its assumptions and scale should be considered when interpreting results.

## Workspace and controls

The **Hydrogen Explorer** is the permanent home tab. Select **+ New Experiment** (or the **+** on the tab bar) to open an experiment in a new tab. You can switch between experiments without opening extra application windows, close experiment tabs, and reopen them from the same menu. The header also provides access to **Settings** (including appearance preferences) and **About**.

## Install from source (developers)

Requires **Python 3.11+** and a supported graphical environment.

```bash
git clone https://github.com/Onimee58/QuantumScope.git
cd QuantumScope
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
quantumscope
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`. See [WINDOWS.md](WINDOWS.md) for more information. Linux helper scripts such as `install_and_run.sh` and `run.sh` are also included.

## Scientific scope and limitations

Hydrogen calculations use the isolated atom in the nonrelativistic Coulomb/Schrödinger approximation, with electron–proton reduced mass. They do not include spin, relativistic corrections, fine/hyperfine structure, radiative corrections, external fields, or many-body interactions. Display transformations used to improve visibility should not be confused with transformations of physical probability. Finite numerical grids capture only part of an unbounded wavefunction.

3D rendering depends on the system's graphics stack (OpenGL/VTK). GPU availability and performance vary by machine; CUDA is not required for the physics calculations. Visualizations are intended for education and research exploration, not precision spectroscopy or claims about individual quantum trajectories.

## Project structure

- `src/quantumscope/` — application, visualization modules, and physics code
- `tests/` — automated tests
- `.github/workflows/` — test and release automation
- `PACKAGING.md` — native installer build guidance
- `WINDOWS.md` — Windows installation and troubleshooting
- `CHANGELOG.md` — development history

## Roadmap

QuantumScope is designed to grow into a broader quantum science workspace. Potential future modules include measurement experiments, Bloch sphere and qubit visualization, quantum circuits, noise models, and quantum machine-learning demonstrations. These are **planned ideas**, not features claimed for v0.2.0.

## Contributing

Bug reports, scientific validation cases, documentation improvements, and code contributions are welcome. Please open an [issue](https://github.com/Onimee58/QuantumScope/issues) or pull request; for changes to physical models, include tests and describe model assumptions. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License and author

QuantumScope is released under the [MIT License](LICENSE).

**Developed and maintained by Md. Saif Hassan Onim.**

Project: https://github.com/Onimee58/QuantumScope
