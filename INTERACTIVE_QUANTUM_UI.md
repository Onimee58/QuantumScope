# Interactive quantum principles UI

## Superposition (redesigned in v0.7.4)
- **Prepare** a spin-½ state by **dragging the arrow** on the Bloch sphere, with the θ and φ sliders (which follow the drag), or with a preset: |0⟩, |1⟩, |+⟩, |−⟩, |+i⟩ or |−i⟩.
  - **Grabbing the arrow** keeps it on its side of the sphere, front or back.
  - **Dragging past the rim** carries it round to the other side, so every state can be reached.
- **The amber dashed axis** is the measurement axis, set with the **Axis** slider. Its ends are the +1 and −1 outcomes.
- **Measure once:** one measurement. The arrow sweeps to +1 or −1 with a flash (the collapse), and the result is counted. Measuring again along the same axis repeats it; **Reset state** returns to the prepared state.
- **Measure many:** fresh copies of the prepared state are measured one after another, at **Slow**, **Fast** or **Instant** speed (**Stop** ends early). The bars grow toward the dashed **Born-rule** targets.
- **Changing** the state or the axis clears the counts, so they always match the targets shown.

## Double-Slit (redesigned in v0.7.4)
- **Fire particles** sends particles through the slits at **Slow**, **Fast** or **Instant** speed (**Stop** ends early).
  - **Each particle lands as one glowing dot** on the **detector screen**; the fringes appear as the dots pile up.
  - **The chart** compares the detections with the exact Fraunhofer pattern.
- **The wavelength sets the light's colour,** on the screen and in the drawn waves. Ultraviolet and infrared are invisible, so they are shown in a labelled false colour.
- **Drag the slits** in the apparatus, up or down, to change their separation.
- **Which-path detectors** at the slits destroy the interference: the screen clears, and new particles show the single-slit pattern.
- **Changing any setting** clears the screen, so it always shows one experiment.

## Entanglement
- "Prepare entangled electron pair" animates the pair separating to Alice and Bob.
- After the pair separates, click either **electron symbol** or the corresponding measure button to reveal only that electron's spin result.
- Move the Alice and Bob angle sliders to choose measurement axes. This does **not** restart the separation animation.
- If either electron was already measured, changing a setting disables further measurement of that pair; click "Prepare entangled electron pair" to begin a new pair.
- Correlation counts represent fresh independent pair preparations for the current settings; altering axes clears prior counts.
- The screen is a schematic of two ideal spin-1/2 measurements. Electron paths and symbols do not represent literal quantum particle trajectories or faster-than-light communication.

## Runtime checks
The app requires PySide6 on the test machine. Run `PYTHONPATH=src pytest -q` for the computational suite and use Ubuntu/Windows to check the GUI interactions.
