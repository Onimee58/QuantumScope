# Hydrogen Dynamics

Open **Experiments → Hydrogen Dynamics (superposition)...**. Select distinct hydrogen eigenstates, relative initial phase, first-state probability, viewing plane and grid size. Play/pause or scrub through one relative beat period.

The exact coherent superposition is `sqrt(p) psi_a + sqrt(1-p) exp(i(phi - (E_b-E_a)t/hbar)) psi_b`, omitting only an irrelevant global phase. Bound-state eigenfunctions are normalized and mutually orthogonal in three-dimensional space. The 2D image is a cross-sectional density in units `a_mu^-3`, **not** the position probability distribution on that plane. Density at nodes is zero, and no trajectories or measurements are simulated.

The model assumes the isolated, nonrelativistic hydrogen Coulomb Hamiltonian with reduced electron/proton mass. States with equal energies have time-independent densities (no physical beat period). The view uses an unchanging color intensity range over time; exported NPZ contains the unmodified slice density. Time is physical femtoseconds. A 2D slice does not establish normalization; integration requires 3D volume.

The animated view is CPU-numerical; the main Explorer continues to support NVIDIA/Intel OpenGL rendering for 3D. This experimental module does not yet provide full 3D time-dependent isosurfaces.

## GIF export and density colors

Hydrogen Dynamics can export the entire quantum beat period as an animated GIF.
Set the number of frames and playback frame rate, then click **Export full-period GIF**.
Frames cover one complete beat period without duplicating the first frame at the end.
The export uses cached analytical wavefunctions and the same fixed density scale as the screen.
It exports the density slice only (not a screenshot of the plot axes). For degenerate
states there is no finite beat period, so full-period export is disabled.

Choose Viridis or grayscale under **Density colors**. These choices affect display
only; they do not modify the physical density. Pillow is required for GIF export.

## v0.1.7 3D dynamics
Open Experiments > Hydrogen Dynamics — 3D animation. Select two distinct eigenstates and use Play or the time slider. Use GPU cloud or isosurface rendering. GIF exports the current 3D camera view for one complete beat period. 3D computations scale as O(N³); start at 96 points per axis on a 2 GB GPU.

## Controls added in v0.5.0

- **Quick-value buttons.** Common settings are one click away instead of stepping up to them:
  - State A probability: 0 / 25 / 50 / 75 / 100 %.
  - Phase: −90° / 0° / 90° / 180°.
  - Grid resolution: Low / Default / High / Max.
  - GIF settings: Min / Max.
  - 3D cloud visibility: Faint / Default / Max.

  Typing a value applies it once you finish (press Enter or leave the field) instead of rebuilding at every keystroke.
- **Fit to states** sets the half-width so the view contains 99.5% of each selected state's probability. It uses the exact radial distribution r²R(r)². When the current half-width clips part of the states, the information panel says so. A larger view is not always better: the 100 a_mu maximum would make a 1s orbital a few pixels wide.
- **2D Reset view** undoes panning and zooming. The axes are labeled with the actual plane coordinates (x, y, z).
- **2D Contrast** changes how density maps to color:
  - *Linear*;
  - *Enhanced (√)*;
  - *Logarithmic*, spanning four decades below the peak.

  The non-linear scales reveal weak lobes next to a much denser state, for example a 3d orbital beside 1s. This is display only: exported NPZ data is always the raw density |ψ|².
- **3D Reset camera** returns to the standard isometric view, centered and zoomed to fit. **Top (xy)**, **Front (xz)** and **Side (yz)** look along the z, y and x axes, matching the 2D cross-sections of the same names.
- **Smoother 3D playback.** Animation updates the existing volume in place instead of rebuilding the scene each frame. Changing the representation or cloud visibility redraws without re-sampling the grid.
