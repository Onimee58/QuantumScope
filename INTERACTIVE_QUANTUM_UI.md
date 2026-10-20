# Interactive quantum principles UI (v0.2.0)

## Superposition
- Move the theta, phi, and measurement-axis sliders or type degrees precisely.
- Drag the 3D Bloch sphere with the mouse to rotate the **view**. This does not alter the physical state.
- "Prepare / reset state" restores the qubit specified by theta and phi.
- "Measure one electron" measures a single prepared state and displays the collapsed Bloch vector.
- "Run shot statistics" samples fresh identically prepared electrons at the current measurement axis.
- Changing preparation or measurement angles clears old shot counts rather than showing them next to changed theoretical values.

## Entanglement
- "Prepare entangled electron pair" animates the pair separating to Alice and Bob.
- After the pair separates, click either **electron symbol** or the corresponding measure button to reveal only that electron's spin result.
- Move the Alice and Bob angle sliders to choose measurement axes. This does **not** restart the separation animation.
- If either electron was already measured, changing a setting disables further measurement of that pair; click "Prepare entangled electron pair" to begin a new pair.
- Correlation counts represent fresh independent pair preparations for the current settings; altering axes clears prior counts.
- The screen is a schematic of two ideal spin-1/2 measurements. Electron paths and symbols do not represent literal quantum particle trajectories or faster-than-light communication.

## Runtime checks
The app requires PySide6 on the test machine. Run `PYTHONPATH=src pytest -q` for the computational suite and use Ubuntu/Windows to check the GUI interactions.
