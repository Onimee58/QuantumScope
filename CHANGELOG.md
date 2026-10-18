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
