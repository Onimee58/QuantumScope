<div align="center">
  <img src="src/quantumscope/assets/quantumscope-128.png" alt="QuantumScope logo" width="96">

  # QuantumScope

  **Explore quantum mechanics. Build quantum circuits. Visualize quantum states.**

  An open-source, cross-platform quantum visualization and circuit simulation studio built with Python and PySide6.

  [![Version](https://img.shields.io/badge/version-v0.4.3-1878b9)](https://github.com/Onimee58/QuantumScope/releases)
  [![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20Windows%20%7C%20macOS-555)](https://github.com/Onimee58/QuantumScope/releases)

  **[Download releases](https://github.com/Onimee58/QuantumScope/releases)** · **[Features](#what-you-can-explore)** · **[Getting started](#getting-started)** · **[Contributing](CONTRIBUTING.md)** · **[Report an issue](https://github.com/Onimee58/QuantumScope/issues)**
</div>

---

## What is QuantumScope?

QuantumScope is a desktop application for exploring quantum phenomena *and* building quantum circuits in one environment. It connects wavefunctions, probability distributions, superposition and entanglement to gate-based quantum computation through interactive visualizations and an editable statevector circuit simulator.

Use it for self-study, classroom demonstrations, coursework or experimenting with small ideal quantum circuits. No programming is required to use the graphical interface.

## What you can explore

| Workspace | Experiments and tools |
|---|---|
| **Hydrogen** | Hydrogen Orbital Explorer; coherent-state Hydrogen Dynamics in 2D and 3D; probability density, amplitude and phase visualization; available image/data exports |
| **Quantum Principles** | Double-Slit Experiment; interactive quantum superposition and Bloch sphere; quantum entanglement demonstrations |
| **Quantum Circuits** | Drag-and-drop circuit editor, statevector simulation, simulation stepping, Bloch spheres beside wires, measurements, example circuits, verification, QASM Converter and PDF export |

### Quantum circuit studio

- **Up to 10 simulated qubits**, with a dynamically expanding operation-column layout.
- **Drag-and-drop gate placement** and movement of existing gates; multi-qubit placement with guided operand selection and temporary anchors.
- **Edit parameters after placing gates** using the gate's dedicated parameter dialog. Expressions such as `pi/2` and `-pi/4` are supported.
- **Undo/Redo**, column insertion and removal, canvas panning, Ctrl+wheel zoom, Fit Circuit and Reset Zoom.
- **Step-by-step statevector inspection**, theoretical output probabilities, measurement sampling and Bloch sphere views.
- **Terminal measurement (`M`) gates**: measured-qubit outcomes are distinguished from diagnostic sampling of the complete state.
- **Circuit verification** and example circuits, including Bell/GHZ and reversible logic/arithmetic demonstrations.
- **Save/open `.qscope` circuits**, import/export supported **OpenQASM 2** instructions, and **export circuit diagrams to PDF**.
- **Quantum Gate Explorer**: double-click a gate in the *left palette* for its definition, circuit symbol, matrix/operation and basic state transformations. Double-clicking a placed parameterized gate opens its parameter editor instead.

**Supported operations:** `H`, `X`, `Y`, `Z`, `S`, `T`, `Sdg`, `Tdg`, `SX`, `RX`, `RY`, `RZ`, `U`/`U3`, `P`, `CX`, `CZ`, `SWAP`, `CCX`, `CSWAP`, and terminal `M`.

## What's new in v0.4.3?

An internal maintenance release: the circuit editor's rules now live in a tested, Qt-free model, preparing for the v0.5 education features. The app looks and works the same, with a few small editing fixes. See [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.4.2?

- **Readable Light Mode circuits:** gates, control dots, targets and results now use theme-aware colors that meet WCAG 2.1 AA contrast.
- **Richer Gate Explorer:** full matrices (including multi-qubit gates), exact amplitudes, properties such as inverse, Clifford membership and eigenvalues, related gates, and angle fields that accept expressions like `pi/2`.
- **More reliable releases:** every packaged app is launch-tested in CI on Linux, Windows and macOS.
- Shell scripts work right after cloning, with no `chmod` needed.

See [CHANGELOG.md](CHANGELOG.md) for details.

## What's new in v0.4.1?

A maintenance release focused on circuit-file integrity:

- `.qscope` files now keep the circuit's column layout (parallel gates and intentional spacing) across save and reopen, while staying readable by v0.4.0.
- QASM import packs simultaneous gates into shared columns, and `barrier` statements are reported instead of silently ignored.
- Safer, bounded parsing of QASM gate angles.
- Arithmetic example circuits keep checking their specification after you edit them, so broken edits show FAIL rows.

See [CHANGELOG.md](CHANGELOG.md) for details.

## What's new in v0.4.0?

QuantumScope v0.4.0 builds on the v0.3.0 circuit studio with:

- **Post-placement gate parameter editing** and mathematical angle expressions.
- **PDF circuit export**, including an optional simulation summary.
- **Gate Explorer** reference dialogs launched from the gate palette.
- **Improved drag-and-drop editing** of existing gates, multi-qubit gate placement previews and column insertion.
- **Fit Circuit improvements and Reset Zoom** for navigating long circuits.
- **Light-theme contrast improvements** and consistent `v0.4.0` application labeling.
- **macOS packaging in GitHub Actions** alongside existing Debian/Linux and Windows installer builds.

**Release status:** macOS CI packaging has completed successfully, but the resulting app still needs hands-on testing on a Mac. The packages are not represented as signed or notarized. Some remaining small visual refinements, such as symbol contrast in light mode, may be addressed in later updates.

## Screenshots

Screenshots of the Hydrogen, Quantum Principles and Quantum Circuits workspaces will be added here. Contributions with platform-specific screenshots are welcome.

## Getting started

### Download a desktop package

Check **[GitHub Releases](https://github.com/Onimee58/QuantumScope/releases)** for the latest available files. Package availability depends on whether the release artifacts have been published.

| Platform | Package | Basic installation |
|---|---|---|
| **Ubuntu/Debian (x86-64)** | `.deb` | `sudo apt install ./<downloaded-file>.deb`, then launch QuantumScope |
| **Windows** | `Setup.exe` | Run the setup wizard and launch QuantumScope from the Start Menu |
| **macOS** | `.dmg` | Open the disk image, drag `QuantumScope.app` to Applications, then launch it |

**macOS note:** The current DMG is unsigned/not notarized. macOS Gatekeeper may require explicit user approval under **System Settings → Privacy & Security**. Install only builds you trust. The successful macOS Actions build does **not** by itself confirm runtime or graphics compatibility.

**Graphics note:** 3D rendering uses VTK/OpenGL and requires a compatible graphical environment and drivers; GPU availability and behavior differ by machine and operating system.

### Run from source (Python 3.11+)

Clone the repository and install the application in a virtual environment:

```bash
git clone https://github.com/Onimee58/QuantumScope.git
cd QuantumScope
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
quantumscope
```

On **Windows PowerShell**, activate with `.venv\Scripts\Activate.ps1` and use `python` instead of `python3`. Alternatively, use the included `install_and_run_windows.bat` and `run_windows.bat` launchers. On Linux, `install_and_run.sh` and `run.sh` are also available.

For Ubuntu, the following host packages may be necessary before installing Python dependencies:

```bash
sudo apt update
sudo apt install python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
```

More setup details: [Windows guide](WINDOWS.md) · [Packaging and builds](PACKAGING.md).

## Your first quantum circuit

1. Launch QuantumScope and open **Quantum Circuits → Gate Circuit Simulator**.
2. Choose **2 qubits** (or leave the current qubit count if already set).
3. Drag **H** from the left palette onto `q0` in the first operation column.
4. Drag **CX** into the next column, then choose its remaining operand as prompted. To prepare a Bell state, use `q0` as control and `q1` as target.
5. Step through the circuit or play the simulation to inspect state probabilities and Bloch spheres.
6. Optionally add terminal **M** gates and run measurement shots, or use **Export PDF** to save the circuit diagram.

For the Bell state, the ideal output is `(|00⟩ + |11⟩)/√2`, with theoretical probabilities of **50%** for `00` and **50%** for `11` (up to the displayed bit-order convention). Finite-shot measurements will vary statistically.

**Editor tips:** Drag from the palette to add a gate; click a placed gate to select it; double-click a placed parameterized gate to edit it. Double-click a palette gate to learn about it in the Gate Explorer. Use middle-drag or Shift+left-drag to pan, Ctrl+wheel to zoom, and **Reset Zoom** to restore a readable working size.

## Files and interoperability

| Format | Purpose |
|---|---|
| `.qscope` | QuantumScope's native circuit file |
| `.qasm` / `.qasm2` | Import/export for the implemented **OpenQASM 2 subset** |
| `.pdf` | Exported circuit diagram; optional simulation-related report content |

OpenQASM support is **not** a complete implementation of all OpenQASM 2 features. Unsupported instructions must be handled explicitly rather than silently discarded. The current circuit simulator supports **terminal** measurements, not arbitrary mid-circuit measurement and feed-forward.

## Scientific scope and limitations

QuantumScope aims for scientifically meaningful *models*, but visual demonstrations should be understood within their documented assumptions:

- **Circuit simulation:** ideal statevector evolution on at most 10 qubits; no physical hardware execution, hardware noise, or decoherence model in the current release.
- **Measurements:** terminal measurement statistics are obtained from simulated quantum-state probabilities. Sampling error depends on shot count.
- **Hydrogen:** nonrelativistic isolated-atom model; finite numerical grids approximate bounded portions of wavefunctions. Spin, relativistic and other advanced corrections are outside the current model.
- **Double slit:** idealized far-field/Fraunhofer interference and diffraction model. The apparatus drawing and animated wavefronts are illustrative, not particle paths or a complete propagation simulation.
- **Graphics:** screen representations (cloud brightness, phase coloring and rendered meshes) are visualization choices and should not be mistaken for additional physical observables.

Explore the accompanying documentation: [Dynamics](DYNAMICS.md) · [Circuit simulator](CIRCUIT_SIMULATOR.md) · [Circuit verification](CIRCUIT_VERIFICATION_GUIDE.md) · [Entanglement demo](ENTANGLEMENT_DEMO.md).

## For educators and students

QuantumScope can support demonstrations of complex amplitudes, superposition, interference, Bloch-sphere rotations, entanglement, quantum gates, measurement, reversible computation and basic circuit design. The Gate Explorer and step-by-step simulator help connect mathematical descriptions with observable circuit outputs.

**Planned future additions (not present in v0.4.0)** include more guided lessons, richer state/matrix inspection, additional quantum algorithms, noise/error-correction education and quantum kernel visualization. These are roadmap goals, not currently shipped features.

## Tests and development

Install development dependencies and run the regression suite:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

The v0.4.3 source passes **393 automated tests**. GUI interactions, installers and graphical rendering still require platform-specific testing.

Build configuration and workflows live in `.github/workflows/`, and desktop packaging scripts live in `packaging/`. Please report reproducible errors with your OS version, installation method, screenshots or logs, and a short reproduction sequence.

## Contributing

Issues, pull requests, documentation improvements, classroom exercises and scientific validation cases are welcome. Please keep physics calculations separate from UI logic, add regression tests for changed behavior, and document numerical and physical assumptions.

See [CONTRIBUTING.md](CONTRIBUTING.md) or [open an issue](https://github.com/Onimee58/QuantumScope/issues).

## License

QuantumScope is distributed under the **MIT License**. See [LICENSE](LICENSE).

---

<div align="center">
  <strong>QuantumScope</strong> — bringing quantum physics and quantum circuits together in one interactive desktop studio.
</div>
