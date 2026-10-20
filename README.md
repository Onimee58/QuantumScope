<div align="center">

<img src="src/quantumscope/assets/quantumscope-128.png" alt="QuantumScope logo" width="104" />

# QuantumScope

### Explore quantum mechanics. Build quantum circuits. See quantum states evolve.

**QuantumScope is an open-source, cross-platform desktop studio for interactive quantum visualization and ideal statevector circuit simulation.**

[![Version](https://img.shields.io/badge/version-v0.3.0-2365a8)](https://github.com/Onimee58/QuantumScope/releases)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-555)](https://github.com/Onimee58/QuantumScope/releases)

**[Download latest release](https://github.com/Onimee58/QuantumScope/releases)** · **[Getting started](#getting-started)** · **[Features](#three-workspaces-one-studio)** · **[Report an issue](https://github.com/Onimee58/QuantumScope/issues)**

</div>

---

## Welcome to QuantumScope

QuantumScope connects the mathematics of quantum mechanics with interactive visualization. Explore hydrogen orbitals, investigate foundational quantum experiments, and create quantum circuits with a visual editor—all in one Python/PySide6 application.

Designed for **students, educators, researchers, and curious builders**, QuantumScope makes abstract quantum concepts easier to explore while keeping the physics and GUI code modular.

> **v0.3.0 highlight:** An expanded quantum circuit studio with visual gate editing, column-by-column state inspection, canvas pan/zoom, and terminal measurement support.

## Three workspaces, one studio

| Workspace | What you can explore |
| --- | --- |
| **Hydrogen** | Hydrogen Orbital Explorer, Hydrogen Dynamics 2D, and Hydrogen Dynamics 3D: investigate wavefunctions, orbital structure, and time evolution. |
| **Quantum Principles** | Double-slit interference, superposition with an interactive Bloch sphere, and entanglement through interactive preparation and gate operations. |
| **Quantum Circuits** | Build, simulate, inspect, verify, save, and exchange quantum circuits with an interactive circuit editor. |

### Quantum Circuit Studio

- **Visual editing:** place quantum gates on qubit wires, expand circuit columns, and use Undo/Redo.
- **State inspection:** step through columns and see statevector-derived probabilities and single-qubit Bloch representations.
- **Built-in examples:** explore Bell states, GHZ states, and reversible arithmetic circuits.
- **Measurements:** place terminal `M` gates and inspect sampled measurement outcomes.
- **Navigation:** pan with middle-drag or Shift + left-drag; zoom with Ctrl + wheel or the toolbar; use **Fit Circuit** to reframe.
- **Interoperability:** save native `.qscope` circuits and import/export the implemented subset of OpenQASM 2 (`.qasm`, `.qasm2`).
- **Simulation:** ideal pure-state statevector simulation with support for **up to 10 qubits**.

**Available gates**

`H` · `X` · `Y` · `Z` · `S` · `T` · `Sdg` · `Tdg` · `SX` · `RX` · `RY` · `RZ` · `U/U3` · `P` · `CX` · `CZ` · `SWAP` · `CCX` · `CSWAP` · `M` (terminal measurement)

## What's new in v0.3.0?

- Interactive circuit workspace with gate placement and built-in circuit examples.
- Column-aligned simulation controls, Bloch spheres, and probability visualizations.
- Circuit truth-table verification and reversible-arithmetic examples.
- Canvas panning, zoom controls, and **Fit Circuit**.
- Terminal measurement markers and measurement-aware QASM conversion.
- Refined dark UI, updated **Q/Wave** identity, and About dialog.

See [GitHub Releases](https://github.com/Onimee58/QuantumScope/releases) for release packages and details.

## Getting started

### Download an installer

Visit **[QuantumScope Releases](https://github.com/Onimee58/QuantumScope/releases)** and select **v0.3.0** when its release assets are available.

| Platform | Release asset | Installation |
| --- | --- | --- |
| **Ubuntu / Debian (x86_64)** | `quantumscope_0.3.0_amd64.deb` | `sudo apt install ./quantumscope_0.3.0_amd64.deb` |
| **Windows (x64)** | `QuantumScope-0.3.0-Setup.exe` | Run the setup wizard. |

Installer assets are produced by the release workflow and depend on successful builds. Installers may not be code-signed.

### Run from source

**Requirements:** Python **3.11+**, a desktop environment, and appropriate OpenGL graphics support.

```bash
git clone https://github.com/Onimee58/QuantumScope.git
cd QuantumScope
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
quantumscope
```

On Ubuntu/Debian, additional system graphics libraries may be required:

```bash
sudo apt update
sudo apt install python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
```

**Windows source setup:** Install Python 3.11+ and run `install_and_run_windows.bat`; subsequent launches can use `run_windows.bat`. See [WINDOWS.md](WINDOWS.md).

## Your first quantum circuit

1. Open **Quantum Circuits**.
2. Load a **Bell** example or place an `H` followed by a `CX` gate.
3. Step through the circuit to inspect how the state changes.
4. Check the probability distribution and measurement statistics.
5. Save as `.qscope` or export supported operations as OpenQASM 2.

## Screenshots

The application includes a modern dark interface across the three workspaces. Screenshots can be added here after capturing them from the v0.3.0 desktop build.

<!-- Suggested: store images at docs/images/ and replace this comment with screenshots. -->

## Scientific scope and limitations

QuantumScope is an **educational and scientific visualization application**, not a hardware execution backend.

- Circuit simulation uses **ideal statevectors** (maximum **10 qubits**) without a hardware-noise model.
- Measurements are **terminal only**; mid-circuit measurement and classical feed-forward are not supported.
- OpenQASM support covers an **implemented OpenQASM 2 subset**, not the full standard or OpenQASM 3. Unsupported instructions must not be silently accepted.
- Editor column-layout metadata is not guaranteed to survive file conversion.
- Hydrogen models use the **nonrelativistic isolated-hydrogen approximation**; plots and integrals can depend on finite numerical sampling domains.
- Double-slit visualizations use an idealized interference model rather than a full microscopic apparatus simulation.
- Reduced single-qubit Bloch vectors may lie **inside** the Bloch sphere for entangled states.

For details, see the repository's supporting guides.

## Developers and contributors

QuantumScope is written in **Python**, with **PySide6** for the desktop GUI and scientific Python/visualization libraries for computations and plotting. Physics and circuit calculations are organized separately from GUI components.

Run the regression suite after installing developer dependencies:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

The uploaded **v0.3.0** source baseline passed **77 automated regression tests** during review. Desktop GUI and installer validation should also be performed before release.

Contributions, bug reports, and ideas are welcome through [Issues](https://github.com/Onimee58/QuantumScope/issues) and pull requests. Please include tests for simulation or file-format changes and document relevant physics assumptions.

**Packaging:** Linux `.deb` and Windows Inno Setup installer configurations, plus GitHub Actions test and release workflows, are included in the repository. See [PACKAGING.md](PACKAGING.md).

## License

Distributed under the [MIT License](LICENSE).

---

<div align="center">

**QuantumScope — a window into the quantum world.**

[Releases](https://github.com/Onimee58/QuantumScope/releases) · [Source code](https://github.com/Onimee58/QuantumScope) · [Issues](https://github.com/Onimee58/QuantumScope/issues)

</div>
