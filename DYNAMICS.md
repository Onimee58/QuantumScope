# Hydrogen Dynamics — QuantumScope v0.1.6

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
