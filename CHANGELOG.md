## v0.5.2 — Learn & Settings (in progress)

### Settings
- **A new Settings window**, titled "Settings", with sections for Appearance, Circuits, Graphics and Files. It has only a Close button, with no maximize or minimize, and a fixed size, so it can no longer fill the whole application window.
- **Appearance:**
  - theme: Dark, Light or **Follow system** (tracks the operating system's light/dark switch live);
  - **interface size** 100–175% for projecting in classrooms, applied after a restart.
- **Circuits:** default qubit count, default measurement shots, Bloch spheres beside wires, and **ask before clearing a circuit**.
- **Graphics:**
  - the **graphics device** (Automatic, Integrated or NVIDIA PRIME offloading on Linux) is now a saved setting, applied at start-up by QuantumScope itself, so `run_nvidia.sh` is optional and the packaged app gets the same choice;
  - the 3D volume rendering method and graphics information moved here from the Orbital Explorer panel.
- **Files:**
  - a default folder for saving and exporting, and a **Recent ▾** menu in the circuit tab;
  - **autosave with crash recovery:** if QuantumScope did not close normally, it offers to restore the circuit;
  - the probability report in PDFs can be set to Ask, Always or Never.
- **Restore defaults** resets every setting. **Restart now** appears when a change needs a restart; the restart drops the old session's graphics and size variables, so the new choice really applies.
- **Test isolation:** the test suite uses its own settings file and data folder, so it never reads or changes a user's settings.

### Circuit tab
- **QuantumScope now starts with an empty circuit** sized by Settings → Circuits. The Bell pair stays in Examples….
- **Toolbar cleanup:**
  - removed the leftover **Bell example** button and an orphan "Gate" label left from the old placement controls (along with the hidden, unused controls behind it);
  - Open, Save, Open recent, QASM import/export and PDF export are grouped under a **File** menu.
- **Gate angle units:** degrees or radians, set in Settings.
  - **New-gate angle fields** show the chosen unit.
  - **The gate-edit dialog** reads plain numbers in that unit, while expressions with pi (such as `pi/4`) are always radians.
- **Bit order in labels:** |q0 q1 …⟩ (textbook) or |… q1 q0⟩ (Qiskit). This is display only, applied everywhere basis states are written. Algorithm parameters and CSV data always list q0 first.
- **Amplitudes:** exact forms (1/√2) or decimals, with 2–8 decimal places.
- **Tools → Simplify circuit…:**
  - **What it does:** cancels neighboring inverse pairs (H·H, X·X, CX·CX, S·S†, T·T†, …), merges consecutive rotations about the same axis (including CP), and removes rotations that equal the identity.
  - **Preview:** shows every change before applying.
  - **Safety check:** every result is verified against the full unitary, and global phases are reported honestly. Gates inside blocks are never changed, and Undo restores the original.
- **Tools → Check equivalence with a saved circuit…:** compares two circuits' unitaries up to global phase. A new vectorized unitary calculation handles 10 qubits in under a second.

### Learn
- **A 📖 Learn button** on each area's tab bar opens the Learn window. It has a contents tree, search, Back/Forward, text size, and **Export PDF** for printable handouts.
- **Lectures:**
  - learning objectives, explanations, and crisp equations pre-rendered for both themes (matrices included);
  - **▶ Try it** links that set up the matching circuit, algorithm, example or view;
  - **Check your understanding** questions with reveal-able answers;
  - textbook further reading.
- **Labs:** guided steps that turn **✓ Done** automatically as the student's circuit meets each goal, with a progress counter. Once a later step passes, earlier ones stay done.
- **My course:** a folder of a teacher's own Markdown lessons, which can use the same links, questions and lab checks. [LEARN.md](LEARN.md) documents the format.
- **First content:** the lectures *Qubits, state vectors and bit order* and *Single-qubit gates*, and the lab *Make a Bell pair*.
- **Built-in content is tested:**
  - every equation has an up-to-date image;
  - every Try it link works;
  - every question has exactly one correct answer;
  - every lab can be completed.

  The packaged-app self-test also checks that the lessons ship with the app.
- **Fixes:**
  - **tree views** were unthemed (white) in the dark theme;
  - **disabled buttons** in the light theme used the dark theme's colors.

## v0.5.1 — Algorithms and examples

- **Blocks:** named groups of real gates that act as one operation.
  - **Collapsed**, a block is a labeled box.
  - **Expanded** (double-click), it shows its gates inside a light dashed outline with a Collapse chip.
  - **Locked:** contents can't be edited, and a block reserves its whole wire span.
  - **Right-click actions:** Expand/Collapse, Edit block… (rebuilds with new parameters), Show contents… (gate list, and the matrix for blocks of up to 3 qubits), Ungroup (make the gates editable) and Remove. All are covered by Undo.
  - **Same physics:** simulation is identical collapsed or expanded, and the State Inspector always counts the real gates inside.
- **Algorithms menu:** Deutsch, Deutsch–Jozsa, Bernstein–Vazirani, Grover search and the quantum Fourier transform (with QFT†).
  - Oracles, diffusion and QFT are blocks.
  - Ancillas start in |−⟩, and Grover uses Toffoli-based multi-controlled Z with work qubits that return to |0⟩.
  - Each algorithm has a **specification check on the current circuit**: constant versus balanced, the hidden string s, Grover's sin²((2k+1)θ) for the oracles actually present, and QFT against the DFT matrix.
- **New reversible examples** with truth-table checks: full adder, 2-bit comparator, controlled increment, Toffoli as AND, and Fredkin multiplexer. Their inputs are set with initial states.
- **New gate CP(λ)** (controlled phase), across the palette, simulator, Gate Explorer, QASM (`cp`, and `cu1` on import), PDF and Clifford classification.
- **Gate Explorer:**
  - a **Worked identity** tab (for example H Z H = X, step by step on every basis state);
  - a **Try it in the circuit** button, which uses starting states that make the gate's effect visible.
- **Files:**
  - circuits with blocks save as `.qscope` **version 3**, which older versions refuse instead of misreading; other circuits keep their format;
  - QASM export writes blocks as their gates, marked by `// block:` comments;
  - PDF export draws blocks.
- **Fixes:**
  - dialogs (Gate Explorer, parameter and custom-state dialogs) were unreadable in the dark theme when the operating system used a light color scheme; they now have a dark style;
  - a multi-qubit gate's angle was lost while its placement was pending, so CP would have become CP(0);
  - the circuit status line now counts the gates inside blocks.
- **New user guide:** [ALGORITHMS.md](ALGORITHMS.md).
- **New Qt-free modules:**
  - `physics/blocks.py`;
  - `physics/algorithms.py` (library, block builders, specifications);
  - `gui/parameter_dialog.py`.
- Automated tests: 577 passing (468 existing + 109 new), plus 27 opt-in GUI tests. The 44-step editing replay from v0.4.3 is unchanged.

## v0.5.0 — See inside the state

- **Initial states:**
  - every qubit can start in |0⟩ (the default), |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩, or a custom state cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩, chosen by clicking the qubit's wire label;
  - the custom dialog accepts expressions like `pi/3` and shows a live Bloch preview;
  - initial states are covered by Undo/Redo, and Clear and the examples reset them.
- **State Inspector window** (State Inspector… button), which follows the step slider, with a Freeze toggle:
  - **Amplitudes:** exact amplitudes, magnitudes, probabilities and phases (as multiples of π), phase color swatches, and filtering and sorting.
  - **Statevector:** Dirac notation, with Copy as text, Copy as LaTeX, Copy as CSV and Save CSV.
  - **Reduced state:** the reduced density matrix of up to 3 qubits (table and heatmap), purity, entanglement entropy in bits, a pure/mixed verdict, and the single-qubit Bloch vector.
  - **Circuit:** gate counts; single-, two- and three-qubit counts; T-count; Clifford and non-Clifford counts; parameterized gates; drawn depth versus minimum depth.
  - An optional "remove global phase" view.
- **Files:**
  - `.qscope` files that use initial states are saved as format version 2, so older versions refuse them instead of silently simulating from |0⟩; all-|0⟩ files stay version 1;
  - OpenQASM export writes exact preparation gates (x, h, s, sdg or u3);
  - PDF export labels each wire with its initial state;
  - the converter reports when it writes preparation gates.
- **Self-test:** the packaged-app self-test now also renders the State Inspector.
- **Hydrogen Dynamics 2D and 3D:**
  - **3D Reset camera fixed.** It did nothing: Qt's `clicked(checked)` argument reached PyVista as `render=False`, and a plain reset also kept the current rotation. It now restores the isometric view, centered and fitted.
  - **New 3D view buttons:** Top (xy), Front (xz) and Side (yz).
  - **Quick-value buttons** (Max, Min and common presets) for probability, phase, grid resolution, cloud visibility and GIF settings.
  - **Fit to states** for the half-width, which contains 99.5% of each state's probability; a hint appears when the view clips the states.
  - **Rebuilds wait** until you finish typing.
  - **Smoother 3D playback,** because the volume is updated in place.
  - **2D:** a Reset view button, axes named after the plane, and a display-only Contrast option (Linear, Enhanced √, Logarithmic).
  - Removed the stale "(v0.2.0)" from the 3D window title.
- **New user guide:** [STATE_INSPECTOR.md](STATE_INSPECTOR.md).
- **New Qt-free modules:**
  - `physics/initial_states.py`;
  - `physics/state_analysis.py` (partial trace, purity, entropy, Dirac/LaTeX/CSV, Clifford test, depth and counts).
- Automated tests: 468 passing (393 existing + 75 new), plus 16 opt-in GUI tests.

## v0.4.3 — Circuit editor model

An internal release with no intended change to how QuantumScope looks or behaves; it prepares the editor for the v0.5 education features.

- **Editor logic moved into a Qt-free `CircuitModel`** (`src/quantumscope/editor/circuit_model.py`). Placement, multi-qubit anchoring, moving, column insertion and deletion, terminal-measurement rules, undo/redo, examples, verification and per-column simulation now live there. The circuit workspace widget only turns input into model calls and draws the result. The widget shrank from 884 to 788 lines.
- **40 new unit tests** cover every editing rule without a display. An opt-in GUI test file checks the widget delegates correctly; run it with `QUANTUMSCOPE_GUI_TESTS=1`.
- **Verified unchanged behavior:**
  - A scripted 44-step editing session gives the same gates, measurements, columns, status messages and verification results as v0.4.2.
  - The rendered workspace is pixel-identical in both themes.
- **Small fixes that fell out of the refactor:**
  - right-clicking any wire of a multi-qubit gate (not only its anchor row) now offers Remove;
  - loading a circuit or undoing now cancels a half-finished multi-qubit placement;
  - empty trailing columns shrink after reducing the qubit count removes gates;
  - removing nothing no longer adds an empty undo step.
- Automated tests: 393 passing (353 existing + 40 new), plus 4 opt-in GUI tests.

## v0.4.2 — Light Mode, Gate Explorer and release checks

- **Light Mode circuit canvas is readable.** Gate symbols, control dots, targets, measurement boxes, Bloch glyphs, probability charts, PASS/FAIL results and step highlights now use theme-aware colors instead of dark-theme colors painted onto the light canvas. Control dots went from 1.08:1 to 12.3:1 contrast. Every color pairing meets WCAG 2.1 AA (4.5:1 for text, 3:1 for graphics), enforced by automated tests. Switching themes recolors the circuit workspace immediately.
- Fixed light-grey empty header areas in the dark circuit table.
- Self-contained visualization panels (Bloch scene, entanglement, double slit, dynamics plots) intentionally keep their dark display background in both themes.
- **Gate Explorer:**
  - full matrices for every gate, including 4×4 and 8×8 matrices for multi-qubit gates, with basis-state labels;
  - readable exact amplitudes (1/√2, i/2, …);
  - a Properties section covering unitary, Hermitian, Clifford, inverse, eigenvalues, the Bloch vector of the gate applied to |0⟩, a useful identity and related gates;
  - angle fields that accept exact expressions such as `pi/2`, plus φ and λ controls for U;
  - fixed the "Overview _matrix" tab label.
  - Every displayed identity and inverse is verified numerically by tests.
- **Packaged-app launch check:** `quantumscope --self-test` starts Qt, the 3D libraries and the circuit workspace without opening a window. The release workflow now runs it on the packaged Linux, Windows and macOS apps before building installers.
- **CI:** the test workflow now also runs on macOS.
- **Shell scripts are executable** in the repository, so `./install_and_run.sh` and `./run.sh` work after a fresh clone without `chmod`.
- Development notes moved from the repository root to `docs/dev-notes/`.
- Automated tests: 353 passing (127 existing + 226 new).

## v0.4.1 — Circuit file integrity and import hardening

- **Circuit layout is preserved on save and load.** `.qscope` files now store each operation's column, the terminal-measurement column and the total column count, so parallel gates, intentional empty columns and spare trailing columns survive a save/reopen. The new fields are optional: v0.4.0 can still open v0.4.1 files (ignoring the layout), and older files open in v0.4.1 with simultaneous gates packed into shared columns.
- **QASM import packs gates into columns** instead of placing one gate per column. Packing only reorders gates that act on disjoint qubits, so the simulated circuit is unchanged.
- **`barrier` statements are no longer dropped silently.** They now separate columns on import, and the editor and converter report that barriers are not saved or exported.
- **Safer QASM angle parsing.** The QASM reader now uses the same safe expression parser as the gate-parameter dialog (no `eval`), with limits on length, nesting and exponent size. Crafted angles such as `9**9**9**9` are rejected instead of freezing the application.
- **Example circuits keep their verification after edits.** Editing the half adder, half subtractor or ripple-carry adder now re-runs the original specification and shows FAIL rows, instead of discarding the check. Undo/redo restores the matching example state.
- Built-in examples moved to `physics/circuit_examples.py` and layout logic to `physics/circuit_layout.py` (Qt-free, unit-tested).
- Removed accidentally tracked `src/quantumscope.egg-info/` build metadata.
- Automated tests: 127 passing (95 existing + 32 new).

## v0.2.0 — Interactive principles update (post-release candidate)

- Added **Quantum Superposition**: pure spin-½ state, Bloch-sphere schematic, selectable measurement basis, Born probabilities, collapse demonstration, and repeated preparations.
- Added **Quantum Entanglement**: animated electron-spin singlet schematic, independent Alice/Bob measurement controls, joint probabilities, simulated correlation statistics, and ideal CHSH reference.
- Added optional ideal which-path marking at the slits in the Double-Slit Experiment. The probability curve and detector samples now switch between coherent fringes and an incoherent single-slit envelope.
- Kept all original Hydrogen Explorer, 2D/3D dynamics, tab workspace, export support, and installer build configuration.
- Distinguish illustrations and ideal-model statistical predictions from real trajectories, real hardware data, and physical signaling.

## v0.2.0 — workspace redesign (stable-release candidate)

- Introduced a cohesive modern dark Qt application theme and a top experiment-launch bar.
- Replaced separate modal experiment windows with closable, state-preserving workspace tabs for Hydrogen Dynamics 2D, Hydrogen Dynamics 3D, and Double-Slit Experiment.
- Kept the Hydrogen Explorer anchored as the primary tab and preserved all physics modules, experiment controls, plots, and exports.
- Refreshed About details and linked directly to https://github.com/Onimee58/QuantumScope.
- Updated documentation to reflect the full v0.2.0 scope rather than the older Hydrogen-only release.
- Physics tests: 40 passing. GUI requires desktop verification with PySide6/VTK.

## 0.2.0 — First stable release candidate

- Double-Slit Experiment: normalized Fraunhofer interference with sampled detection events.
- Added an animated apparatus schematic (source, double-slit barrier, and detector) with detector marks tied to sampled events; optional animation toggle.
- Retained the original probability-density plot, histogram, parameter controls, and CSV export.
- Consistent tag-based artifact filenames and source version 0.2.0.
- Existing hydrogen explorer and 2D/3D dynamics preserved.
- First labeled stable release, subject to packaged GUI verification on Windows and Linux.

## v0.1.7 — 3D Hydrogen Dynamics and layout repair

- Added 3D dynamics experiment with time evolution, density cloud, isosurface, and 3D GIF export.
- Fixed main sidebar startup width (previously hard-coded 330 px); increased minimum width and disabled horizontal overflow.
- Kept v0.1.6 2D dynamics and Windows/Linux workflows.
- Requires real GUI validation on both platforms before tagging.

## v0.1.6 — Hydrogen Dynamics
- New **Experiments → Hydrogen Dynamics** interactive 2D cross-section of exact two-state hydrogen superpositions.
- Physical femtosecond time evolution, play/pause, time scrubber, amplitudes, relative phase, slice controls and export.
- Preserves v0.1.5 comparison, Linux NVIDIA PRIME and Windows/Linux build workflow.

# Changelog

## v0.1.5 — Visualization refinement
- Resizable sidebar and full-height layout.
- Collapsible radial probability plot and scientific information.
- Camera synchronization between comparison viewers, with optional toggle.
- Orbital labels over both viewers.
- Mask numerically undefined phases near nodal points; cyclic phase colormap retained.
- Windows/Linux build workflow preserved; NVIDIA PRIME launcher preserved.

## 0.1.4 — Real orbitals and comparison

- Introduced real tesseral hydrogen orbital basis with unit-normalized cosine/sine combinations.
- Added optional dual 3D orbital viewer and state selectors.
- Added 1–4× PNG screenshot export scale and extended NPZ basis metadata.
- Updated version and portable cross-platform PyInstaller action; avoided broad pyqtgraph collection on headless CI.
- Added numerical checks for real-orbital angular nodes and density identities.

## 0.1.3 — Cross-platform source release
- Added Windows batch installer and launcher using an isolated Python virtual environment.
- Added Windows setup and graphics selection documentation.
- Extended CI physics tests to Windows.
- Kept existing Linux graphics configurations and About dialog unchanged.
- No claim of a compiled Windows executable or Windows GPU validation yet.

## v0.1.1 — About dialog enhancement

- GlassBalance-inspired About panel, local portrait selection, custom logo, maintainer credits and configurable GitHub link.
- Existing hydrogen rendering and scientific computation remain unchanged.

# Changelog

## 0.1.1 — GUI and orbital visualization fixes

- Added Help → About QuantumScope dialog with project details, developer attribution, license, and website.
- Probability-aware camera positioning and reset camera button.
- Density contrast enhancement without changing computed or exported density.
- Scrollable control panel and more legible scientific readouts.
- Automatic radial plot axis framing.
- Selectable VTK smart/GPU/CPU volume mapper, CPU fallback for Auto.
- Optional automatic rerender on controls change.
- More accurate explanations of probability capture and visualization transforms.

## 0.1.0 — Hydrogen Explorer

- Initial hydrogen wavefunction engine and interactive desktop application.

## 0.1.2
- Add phase-colored probability-enclosing isosurfaces (complex wavefunction phase).
- Add standard camera orientations, zoom, optional physical coordinate bounds.
- Add in-application VTK OpenGL capability diagnostics.
- Add NVIDIA PRIME / GLX and system-default launch scripts.
- Preserve About dialog for future revision.

### v0.1.4 UI/graphics hotfix (post-release candidate)
- Sidebar extends to the bottom of the application; radial plot is compact and placed below the viewers only.
- Phase colors on probability-enclosing surfaces now use trilinear interpolation of the complex wavefunction at mesh vertices instead of nearest-voxel cell sampling.
- Clarified VTK volume mapper versus physical GPU choice.
- Added a Linux restart-on-NVIDIA action using the previously verified XCB/GLX PRIME environment; the active GPU is reported by graphics diagnostics.
- Scientific calculations and Windows/Linux packaging workflows retained.

### v0.2.0 — Installer and branding preparation
- Adopted the Modern Q / Wave icon in the main window, About dialog, and native application metadata.
- Added reusable SVG, PNG, and ICO branding resources.
- Added GitHub Actions builds for Ubuntu/Debian `.deb` and Windows Inno Setup `Setup.exe` installers.
- Kept existing tabbed experiment UI and numerical physics modules unchanged.

### v0.2.0 — stable UI polish (pre-release)
- Replaced the legacy Experiments/Help menu bar and three quick-launch buttons with a unified New Experiment dropdown.
- Added the same experiment catalog to the tab-bar + control, organized for future expansion.
- Applied the official QuantumScope Q/Wave icon in the workspace header and Hydrogen Explorer tab.
- Added header Settings and About buttons, including a persistent dark/light interface preference.
- Kept native window decoration, the existing dock/taskbar application icon, and the .deb/Windows installer configurations.

### Quantum principles interaction refinements (v0.2.0 development update)
- Bloch sphere uses a drag-rotatable 3D orthographic projection with three great circles and state vector.
- Superposition state and measurement angles, plus Alice/Bob axes, have synchronized sliders and degree boxes.
- Entanglement electrons are clickable to measure after separation; changing measurement angles no longer restarts their travel animation.
- Previous shot/correlation statistics clear on parameter changes to avoid confusion with the current theoretical prediction.
- After one electron is measured, changing an axis requires preparing a new pair, avoiding mixing incompatible measurement settings.

### Interactive entanglement preparation station (v0.2.0 development update)
- Entanglement demonstration now begins with separately adjustable Alice and Bob spin states (polar angle and phase for each).
- Animated electron symbols move into a schematic H(A) then CNOT(A,B) preparation station and emerge as a joint two-qubit state.
- Displays input product-state amplitudes, output joint-state amplitudes, and pure-state concurrence (0–1).
- Default |up,up> input produces maximally entangled Bell |Phi+>; other inputs can produce partially entangled or separable states.
- After preparation, each electron is clickable for its own local projective spin measurement; sequential measurements condition the same joint state.
- Changing measurement axes does not restart electron motion. Altering initial preparation requires reset and preparation of a new pair.
- Batch statistics use the generated joint state and current measurement axes, not an assumed singlet for every input.

### Quantum Circuit Workspace update (v0.2.0 development)

- Organized the interface into three top-level workspaces: Hydrogen, Quantum Principles, and Quantum Circuits. Experiments retain their individual tabs within each workspace.
- Added an ideal statevector quantum gate simulator with an editor, gate palette, two-qubit controls, Bloch previews of reduced single-qubit states at every step, sample measurement counts, and OpenQASM 2 subset import/export.
- Interactive circuit limit: 10 qubits; explicitly reject unsupported OpenQASM operations.
