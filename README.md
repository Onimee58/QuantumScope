# QuantumScope

**QuantumScope v0.2.0 — Quantum Visualization Studio** is an open-source Python/PySide6 desktop application for scientifically grounded, interactive quantum visualizations on Linux and Windows.

The v0.2.0 workspace includes hydrogen orbitals, coherent hydrogen-state dynamics in 2D and 3D, and an interactive double-slit experiment. Experiments open as tabs inside one window; the physics packages remain independent of the GUI.

## Workspace and experiments (v0.2.0)

- Modern dark interface with a persistent Hydrogen Explorer tab and closable experiment tabs.
- Reopen an active experiment from the top shortcuts or Experiments menu to focus its existing tab without resetting parameters.
- Hydrogen Dynamics 2D: coherent state superpositions, evolving density and export tools.
- Hydrogen Dynamics 3D: animated superposition density and available export tools.
- Double-Slit Experiment: source/slit/detector schematic with illustrative animated wavefronts, Fraunhofer probability curve, sampled detection histogram, event visualization and CSV export.
- **Scientific interpretation:** the source/slit/detector drawing is schematic and not to scale; the wavefront rings depict illustrative phase fronts, not individual particle trajectories. Detection events follow the model's sampled far-field probability distribution.
**QuantumScope** is a free, open-source desktop application for exploring quantum physics through interactive, scientifically grounded visualizations. It runs on **Linux and Windows** and currently focuses on hydrogen atomic states.

**Latest downloads:** [GitHub Releases](https://github.com/Onimee58/QuantumScope/releases/latest)  
**Source code and issues:** [github.com/Onimee58/QuantumScope](https://github.com/Onimee58/QuantumScope)

> **Project status:** Early development (0.x). Scientific calculations are unit-tested, but graphical behavior and bundled executables depend on operating-system graphics drivers and Qt/VTK runtime support.

## Features

- Interactive 3D visualizations of hydrogen electron probability density, including volume rendering and probability-enclosing surfaces.
- Selectable hydrogen states using principal, angular, and magnetic quantum numbers (`n`, `l`, `m`).
- Complex spherical-harmonic eigenstates and real orbital combinations (including familiar p-orbital orientations).
- Phase-aware coloring, optional coordinate axes, camera views, and adjustable magnification.
- Optional **side-by-side orbital comparison** with independently selected states.
- Radial probability plots, energy information, and a finite-grid probability diagnostic.
- PNG figure export and `.npz` numerical-data export.
- GPU-capable 3D rendering through VTK/OpenGL, plus renderer diagnostics.
- Linux NVIDIA PRIME launcher and standard cross-platform launch options.

## Screenshots

Screenshots will be added here. For contributions, screenshots of the 3D orbital viewer and side-by-side comparison are particularly helpful.

## Windows setup
## Download and install

Download the appropriate ZIP from the [latest release](https://github.com/Onimee58/QuantumScope/releases/latest) and **extract it fully before launching**. The automatically built packages are unsigned preview builds.

### Windows (downloadable build)

1. Download the `Windows.zip` release asset.
2. Extract the archive.
3. Open the extracted `QuantumScope` folder and launch **`QuantumScope.exe`**.

Windows may warn about unsigned applications. Only run software downloaded from a source you trust. For a laptop with multiple GPUs, use **Windows Settings → System → Display → Graphics** to choose a high-performance GPU; restart the application for the change to take effect.

### Linux (downloadable build)

1. Download the `Linux.zip` release asset and extract it.
2. In a terminal opened in the extracted folder, run:

```bash
chmod +x QuantumScope/QuantumScope
./QuantumScope/QuantumScope
```

On systems with NVIDIA PRIME configured, the archive also includes `run_packaged_nvidia.sh`:

```bash
chmod +x run_packaged_nvidia.sh
./run_packaged_nvidia.sh
```

The prebuilt Linux package requires a compatible desktop environment, graphics drivers, and system libraries. Linux builds made on Ubuntu are **not guaranteed** to run on every distribution or older glibc version.

## Install from source (developers)

Python **3.11+** is required; Python **3.12** is recommended for reproducible cross-platform development.

```bash
git clone https://github.com/Onimee58/QuantumScope.git
cd QuantumScope
python -m venv .venv
```

Activate the environment:

- **Linux:** `source .venv/bin/activate`
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`

Then:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python -m quantumscope
```

Alternatively, use the included operating-system-specific scripts: `install_and_run.sh` / `run.sh` on Linux, or `install_and_run_windows.bat` / `run_windows.bat` on Windows. Ubuntu users may need packages such as `libgl1`, `libegl1`, `libxkbcommon-x11-0`, and `libxcb-cursor0`.

For NVIDIA PRIME rendering on Linux, launch the **source installation** with:

```bash
./run_nvidia.sh
```

The graphics-backend selection in the interface controls the VTK **volume mapper**, not the physical GPU. A physical GPU change generally requires restarting the application; consult the **Graphics diagnostics** panel to see the actual OpenGL renderer.

## Using QuantumScope

Choose a hydrogen state (`n`, `l`, `m`) and the appropriate complex or real orbital basis. Select a visualization representation, adjust the probability enclosure and rendering controls, and rotate or zoom the 3D view. Enable orbital comparison to display two independently selected states. Use the radial probability plot and scientific information to interpret the result; export screenshots or numerical grids when needed.

## Scientific model and interpretation

The hydrogen module uses analytical bound-state solutions of the **nonrelativistic Coulomb Schrödinger equation**, including the electron–proton **reduced mass**. The model neglects electron spin, relativistic/fine-structure effects, hyperfine structure, Lamb shifts, external fields, and multi-particle interactions.

\[
\psi_{nlm}(r,\theta,\phi)=R_{nl}(r)Y_l^m(\theta,\phi),\qquad
\rho(\mathbf r)=|\psi(\mathbf r)|^2.
\]

- **Probability density** is not an electron trajectory. Probability within a spatial region is the integral of density over volume.
- **Enclosing surfaces** are found from density thresholds chosen to capture a specified percentage of the probability **on the sampled finite grid**. They are not solid physical boundaries.
- **Phase coloring** represents the complex wavefunction's phase, which is undefined at nodes where amplitude vanishes. Abrupt phase/color transitions are not necessarily discontinuities in the probability density.
- **Real orbitals** are mathematically defined linear combinations of complex eigenstates. Sign and phase coloring must not be interpreted as charge density.
- The density-cloud brightness/opacity may use a display-only transfer function; `.npz` exports preserve scientific numerical data.
- Finite-grid normalization is an approximation to the integral over unbounded space. Numerical values depend on grid extent and resolution.
- The nucleus marker is illustrative and not drawn to atomic scale.

Please report apparent physics or rendering inconsistencies with the state parameters, visualization mode, platform, and a screenshot.

## Development and testing

The physics engine is separate from the Qt interface and can be tested without launching a desktop window.

```bash
python -m pytest -q
```

GitHub Actions runs tests and builds downloadable packages for Windows and Linux. **A successful build does not establish that the bundled GUI has been tested on every machine.** Test published binaries on actual target systems, particularly 3D volume rendering and Qt/OpenGL initialization.

## Project roadmap

| Stage | Focus |
|---|---|
| Hydrogen Explorer (0.1.x) | Hydrogen physics, real/complex orbitals, 3D rendering, comparison, cross-platform packaging |
| Advanced atomic visualization (0.2.x) | Improved nodal/phase interpretation, precision and visualization controls |
| Quantum dynamics (0.3.x) | Superposition, wave packets, time evolution, tunneling |
| Multi-electron models (0.4.x) | Explicitly documented approximate atomic models |
| Quantum computing (0.5–0.6.x) | Qubits, Bloch spheres, gates and circuits |
| Quantum ML and noise (0.7–0.8.x) | Feature maps, quantum kernels, variational circuits, noise |
| Research tooling (0.9–1.0) | Extensible interfaces, reproducibility and stable releases |

This roadmap expresses goals rather than promised delivery dates.

## Contributing

Bug reports, scientific validation checks, documentation improvements and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), or open a [GitHub issue](https://github.com/Onimee58/QuantumScope/issues). Please include tests and document physical assumptions when changing the physics backend.

## v0.1.4 update: Windows source distribution
## License and developer

QuantumScope is released under the **MIT License**; see [LICENSE](LICENSE).

Developed by **Md. Saif Hassan Onim, PhD** — [developer website](https://people.smu.edu/monim).

See [PACKAGING.md](PACKAGING.md) for automated GitHub Actions builds of runnable Windows and Linux releases.


## v0.1.4: Real orbital basis and comparisons

- Select **Complex Y(l,m)**, **Real cosine**, or **Real sine** orbital bases. The real choices use `|m|`, with the conventional relative global phase not physically observable. `m=0` has only a cosine choice; sine is mapped to cosine in the GUI.
- Enable **Side-by-side comparison** to render two independent hydrogen states at once. Both viewers share representation, resolution, camera orientation, and color options; each computes its own state. Memory usage rises with grid resolution.
- **PNG export scale** supports 1–4× resolution for the main 3D viewer.
- The older probability enclosure is a constant-density isosurface threshold chosen from sampled grid mass. It is not an exact probability-enclosing mesh because voxel rankings and mesh interpolation are approximate.
- Phase coloring applies to the wavefunction, not its density; angular real-orbital colors differ by sign (0 or π), subject to the arbitrary overall sign convention.
- All builds should be validated with Windows and Linux GUI launch smoke tests after downloading CI artifacts.


## v0.1.5 visualization controls

- Drag the divider to resize the sidebar and 3D comparison panels.
- Enable **Synchronize comparison cameras** to rotate both orbital viewers together.
- Uncheck **Radial probability** to collapse the plot temporarily.
- Uncheck **Scientific information** to collapse detailed state metadata.
- Phase colors use a cyclic colormap; near-zero wavefunction magnitudes are masked because phase is undefined at nodes.
- Linux users can restart on NVIDIA PRIME from the graphics diagnostics panel; selecting a GPU volume mapper does not select a physical graphics device.


### Hydrogen Dynamics (v0.1.6)
Choose **Experiments → Hydrogen Dynamics (superposition)...** for time-dependent coherent superpositions of two bound states. See [DYNAMICS.md](DYNAMICS.md) for model assumptions, animation controls, and data interpretation.


## Quantum Phenomena Lab (v0.2.0)

**Experiments → Quantum Phenomena — Double-Slit Experiment** opens a coherent far-field double-slit model. The theoretical curve is the normalized Fraunhofer diffraction envelope multiplied by the two-slit interference factor. The detector controls sample independent outcomes from that curve. This is a **paraxial, monochromatic, idealized model**; no particle paths or time-dependent wave propagation are simulated. Results and sampled detections can be exported as CSV.

### Double-slit apparatus (v0.2.0)

The Double-Slit Experiment dialog now includes an animated, **not-to-scale** apparatus showing a source, two apertures, and a detector. The arcs illustrate coherent wavefronts, **not individual particle paths** or a time-dependent propagation calculation. The detector marks are drawn from the exact sampled hit positions used for the original histogram. Uncheck **Animate illustrative wavefronts** to freeze the diagram. Adjusting experiment parameters clears accumulated detections, consistent with the underlying probability plot. The Fraunhofer physics model, CSV export, and other experiments are unchanged.

## Project

Source, issues and contributions: https://github.com/Onimee58/QuantumScope

QuantumScope is MIT-licensed. Models use the nonrelativistic hydrogen approximation and an idealized paraxial Fraunhofer double-slit approximation; neither includes full experimental apparatus or environment modeling.

## Native installers (v0.2.0)

The `.github/workflows/release.yml` pipeline prepares installable `quantumscope_0.2.0_amd64.deb` and `QuantumScope-0.2.0-Setup.exe` files. See [PACKAGING.md](PACKAGING.md) for how to build, install, and verify these releases. The source download is **not** a compiled installer.
*QuantumScope — Visualizing Quantum Physics Through Scientific Computation.*
