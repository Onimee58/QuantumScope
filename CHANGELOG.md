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
