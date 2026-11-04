# Interactive quantum principles UI

## Superposition (redesigned in v0.7.4)
- **Prepare** a spin-½ state by **dragging the arrow** on the Bloch sphere, with the θ and φ sliders (which follow the drag), or with a preset: |0⟩, |1⟩, |+⟩, |−⟩, |+i⟩ or |−i⟩.
  - **Grabbing the arrow** keeps it on its side of the sphere, front or back.
  - **Dragging past the rim** carries it round to the other side, so every state can be reached.
- **The amber dashed axis** is the measurement axis, set with the **Axis** slider. Its ends are the +1 and −1 outcomes.
- **Turn the sphere** to look from any side: **right-drag**, or **Shift + left-drag** on a trackpad. **Double-click** resets the view. |0⟩ always stays on top. (v0.7.5)
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

## Entanglement (redesigned in v0.7.5)
- **The pair:** choose a Bell state (|Φ⁺⟩, |Φ⁻⟩, |Ψ⁺⟩, |Ψ⁻⟩) or a **classically correlated** mixture for contrast. **Clean pairs** mixes in noise (0–100%).
- **Each qubit's own state** is shown on its sphere, Alice's and Bob's. For an entangled pair, both are **random** (no arrow): neither qubit has a state of its own.
- **Aim the detectors:** left-drag the amber axis on a sphere, or use the sliders. Right-drag (or Shift + left-drag) turns a sphere, and double-click resets it.
- **Send one pair:** the pair flies out.
  - **Alice measures,** and both arrows jump to the surface: Bob's qubit is now definite as well.
  - **Then Bob measures,** and his result is counted.
  - **No signal travels:** on his own, Bob's results stay 50/50 until the two compare notes.
- **Send many:** pairs at **Slow**, **Fast** or **Instant** speed.
  - **The grid** counts the four joint results against their predicted shares.
  - **The curve** compares the measured correlation with the quantum prediction and a simple classical model.
- **Run Bell test:** many pairs at each of the four standard axis settings. The meter shows **|S|** with its uncertainty.
  - **Entangled pairs beat the classical limit of 2,** up to 2√2 ≈ 2.83.
  - **Noisy pairs** fall below 2 once fewer than about 71% are clean.
  - **The classical mixture** never exceeds 2.
- The physics (`physics/bell.py`) is exact. The flying particles are a schematic, not trajectories.

## Runtime checks
The app requires PySide6 on the test machine. Run `PYTHONPATH=src pytest -q` for the computational suite and use Ubuntu/Windows to check the GUI interactions.
