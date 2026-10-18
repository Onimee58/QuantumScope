# QuantumScope

**QuantumScope — Hydrogen Explorer** is an open-source, Windows-and-Linux desktop tool for physically grounded quantum-state visualization.

The initial release calculates *analytical, nonrelativistic* bound-state hydrogen wavefunctions and renders their probability densities in interactive 3D.

## Features

- Hydrogen eigenstates with selectable quantum numbers `n=1..4`, `l=0..n-1`, `m=-l..l`
- Interactive 3D probability-density volume rendering
- Density isosurface chosen to enclose a target fraction of **grid-captured** probability
- Real/imaginary wavefunction amplitude isosurfaces
- Radial probability plot and computed energy level
- Finite-grid probability diagnostic
- PNG screenshot and `.npz` scientific data export
- Separate, independently testable physics package

## Windows setup (new in v0.1.4)

On Windows 10/11 (64-bit), install Python 3.12 (recommended) and extract this repository into a writable folder. Double-click **`install_and_run_windows.bat`** to create `.venv`, install dependencies, and launch the GUI. For subsequent launches, double-click **`run_windows.bat`**. No Linux commands or CUDA are required. See [WINDOWS.md](WINDOWS.md) for Windows GPU selection and troubleshooting.

This release provides source-based Windows installation, **not** a bundled or signed `.exe` installer. Windows GUI/GPU functionality requires local validation; automated physics tests run on Windows as well as Linux.

## Ubuntu setup

Install Python 3.11 or later, venv support, and the OpenGL/X11 runtime libraries. On Ubuntu, for example:

```bash
sudo apt update
sudo apt install python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
```

From inside the repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
quantumscope
```

Alternatively, launch with `python -m quantumscope`. A working desktop display and OpenGL implementation are required. On remote/headless machines, run physics tests only, or set up an appropriate graphical display.

### Controls

Set `n`, `l`, and `m`, choose a rendering mode, adjust the grid resolution or enclosed probability, then click **Render state**. Drag to rotate; use the mouse wheel to zoom. Save the current 3D view as PNG, or export arrays and metadata as `.npz`.

## Physical model and limitations

The physics backend solves the **isolated hydrogen atom** with a Coulomb potential in the nonrelativistic Schrödinger approximation. It uses the electron-proton **reduced mass**, not the bare electron mass, and ignores spin, relativistic corrections, fine/hyperfine splitting, Lamb shift, external fields, and interactions with other particles. Energies are approximately -13.6/n² eV.

- `psi` has units `a_mu^-3/2`; `density = |psi|²` has units `a_mu^-3` with the supplied coordinates expressed in reduced-mass Bohr radii (`a_mu`).
- The volume renderer uses `density / max(density)` **only for the color/opacity mapping**, not for any physics calculation.
- Finite 3D grids do not cover the entire wavefunction. The displayed *grid integral* estimates captured probability using sampled point values and cell volume.
- The enclosure control selects an isodensity cutoff using the fraction of probability **inside the sampled grid**. It does not guarantee the same percentage of the exact unbounded wavefunction, and surface geometry can cause discretization error.
- `m ≠ 0` hydrogen spherical-harmonic eigenstates are generally complex. The real and imaginary part plots show signed amplitude, not electron trajectories. Classical-looking `p_x/p_y` real combinations are not included yet.
- The nucleus marker is **illustrative** and not to physical scale.
- `Imag(psi)` may be identically zero for some eigenstates (e.g. `m=0`), yielding no amplitude isosurface.

## Numerical API

```python
from quantumscope.physics import HydrogenAtom
atom = HydrogenAtom()
state = atom.state(n=2, l=1, m=0)
print(state.energy_ev)
print(state.probability_density(0.0, 0.0, 2.0))
```

## Roadmap

- **v0.2:** phase visualization, orbital comparisons, improved probability-enclosing algorithms
- **v0.3:** time-dependent wavefunctions and quantum dynamics
- **v0.4:** documented approximate multi-electron models
- **v0.5–0.6:** qubits, Bloch sphere, quantum circuits
- **v0.7–0.8:** QML, quantum noise
- **v0.9–1.0:** extensibility and stable research tooling

## Contributing

Contributions, bug reports and scientific validation cases are welcome via GitHub issues and pull requests. For scientific changes, please add tests and document physical assumptions.

## License

MIT (see `LICENSE`).

## v0.1.1 update: visualization, layout, and hardware selection

- Probability-weighted camera framing focuses on the spatial region containing 99.5% of the **sampled** electron probability instead of the full rectangular simulation grid. This is only a camera choice; exported scientific data is unchanged.
- Display intensities use `(density / maximum density) ** 0.35` to bring out dim radial structures. This is a **visual transfer function**, not a physically transformed probability density. Scientific `.npz` exports contain the original computed values.
- Volume rendering offers **Auto (GPU preferred)** (VTK smart mapper), **GPU** (VTK GPU mapper), and **CPU** (fixed-point mapper). Auto may choose a CPU backend on machines where GPU rendering is unavailable. The displayed mapper preference is not proof of physical VRAM allocation.
- Scrollable left control panel, clearer scientific readouts, radial plot framing, reset-camera button, adjustable cloud visibility, and optional auto-refresh.
- The program does not require CUDA. OpenGL graphics/VTK runtime drivers still need to be available on the host.

### Upgrade from v0.1.0

Extract this version into a new folder (don't merge with the old repository files), then run:

```bash
chmod +x install_and_run.sh
./install_and_run.sh
```

The shell script creates a virtual environment and installs the project's dependencies, then starts the GUI. It requests sudo access to install required system packages on Debian/Ubuntu.

### Known limits

The orbital volume renderer requires a machine with an actual graphical display and compatible OpenGL stack. This release's Qt / VTK window was not exercised in the automated headless build environment; numerical physics unit tests were run. VTK chooses the final OpenGL implementation; neither requested GPU mode nor a driver-reported GPU name guarantees the particular GPU is used. For a reliable driver diagnostic on Linux, use `glxinfo -B` (package `mesa-utils`).

## About dialog

Select **Help → About QuantumScope** to view the project description, developer credit, dependencies, scientific scope, and license.

### About panel

Open **Help → About QuantumScope** for version and developer credits. Use **Change profile picture (local)** to choose an image stored on your machine, and **Set GitHub repository URL** after creating your repository. The image stays local and is not bundled into exports.

## v0.1.2 graphics and visualization

After installing with `./install_and_run.sh`, use `./run.sh` for automatic
NVIDIA preference on X11, `./run.sh nvidia` for the tested NVIDIA PRIME/GLX
configuration, or `./run.sh default` for the system default GPU. A physical
GPU change requires restarting the program. NVIDIA detection by `nvidia-smi`
is not proof that the Qt rendering context selected NVIDIA: use **Graphics
diagnostics** inside the application to inspect the active VTK OpenGL context.

The **Probability enclosure** mode can now color its isosurface using complex
wavefunction phase. This is a phase visualization, not a claim that probability
density contains phase. Phase at low-amplitude points should not be interpreted
as physically measurable, and global phase is arbitrary. Standard camera views,
zoom, coordinate bounds in reduced-mass Bohr radii, and renderer diagnostics
are also provided. The About dialog is unchanged in this release.

## v0.1.4 update: Windows source distribution

- Added `install_and_run_windows.bat`, `run_windows.bat`, and Windows setup guide.
- Preserved Linux launchers (`run.sh`, `run_nvidia.sh`, `run_default.sh`).
- Added Windows test matrix to GitHub Actions.
- Native GUI/graphics validation remains pending on a Windows machine.

## GitHub binary packages

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
