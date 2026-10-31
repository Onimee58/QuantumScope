# State Inspector and initial states

QuantumScope v0.5.0 adds two ways to look inside a circuit's quantum state: choosing each qubit's **initial state**, and the **State Inspector** window.

## Initial states

Every qubit starts in |0⟩ unless you change it. Click a qubit's label at the left end of its wire (for example `q0 |0⟩`) and choose one of the following:

| Choice | State | Bloch vector |
|---|---|---|
| \|0⟩ | \|0⟩ | (0, 0, 1) |
| \|1⟩ | \|1⟩ | (0, 0, −1) |
| \|+⟩ | (\|0⟩ + \|1⟩)/√2 | (1, 0, 0) |
| \|−⟩ | (\|0⟩ − \|1⟩)/√2 | (−1, 0, 0) |
| \|+i⟩ | (\|0⟩ + i\|1⟩)/√2 | (0, 1, 0) |
| \|−i⟩ | (\|0⟩ − i\|1⟩)/√2 | (0, −1, 0) |
| Custom (θ, φ) | cos(θ/2)\|0⟩ + e^{iφ} sin(θ/2)\|1⟩ | (sin θ cos φ, sin θ sin φ, cos θ) |

For a custom state, enter θ (0 to π) and φ (0 to 2π) in radians; expressions such as `pi/3` work. A Bloch preview shows where the state points. At the poles (θ = 0 or π), φ only changes a global phase and is ignored. A custom state that equals a preset is shown with the preset's label; otherwise the wire shows |ψ⟩.

The register starts in the product of the qubits' states. Initial states are part of the circuit: Undo and Redo cover them, and Clear, the Bell button and the built-in examples reset them to |0⟩.

**Saving and exporting**

- **.qscope:** files that use non-|0⟩ initial states are saved as format version 2. Older QuantumScope versions refuse to open them, rather than silently simulating from |0⟩. Files where every qubit starts in |0⟩ stay version 1 and open in older versions as before.
- **OpenQASM 2:** this format has no initial-state syntax, so export adds the equivalent preparation gates at the start, marked with a comment. The presets use |1⟩: `x`; |+⟩: `h`; |−⟩: `x, h`; |+i⟩: `h, s`; |−i⟩: `h, sdg`; a custom state uses `u3(θ, φ, 0)`. The exported circuit is exactly equivalent. Importing it back shows these as ordinary gates on qubits starting in |0⟩.
- **PDF:** each wire is labeled with its initial state.

**Verification table.** The truth table checks the gate logic for every basis input, so it does not use the chosen initial states. A note appears when they differ from |0⟩.

## State Inspector

Open it with **State Inspector…** in the circuit tab. It is a separate window that you can keep open while editing. By default it shows the state after the column selected by the step slider, and it updates as you step, play or edit. Tick **Freeze** to hold the current state while you step elsewhere to compare.

The inspector always shows the ideal state *before* any terminal measurement. Basis labels list q0 first (leftmost), as everywhere in QuantumScope.

**Remove global phase** rotates every amplitude by one common phase, so that the first nonzero amplitude is real and positive. A global phase has no observable effect. This option makes, for example, −|1⟩ and |1⟩ display identically. CSV exports always contain the raw amplitudes.

### Amplitudes

Each nonzero basis state is listed with its amplitude (exact forms such as 1/√2 where possible), magnitude, probability and phase. Phases are shown as multiples of π, with degrees in the tooltip. The color swatch encodes phase around the color wheel (red = 0), which makes phase patterns easy to spot, for example after a QFT. Tick **Show all basis states** to include zero amplitudes. You can sort by basis order or by probability.

### Statevector

This tab shows the state in Dirac notation, for example (1/√2)|00⟩ + (1/√2)|11⟩. Its buttons:

- **Copy as text:** the Dirac notation as plain text.
- **Copy as LaTeX:** the same expression, ready to paste into notes or papers.
- **Copy as CSV / Save CSV…:** every basis state's real and imaginary parts, magnitude, probability and phase, at full precision.

### Reduced state

Tick up to three qubits to see their reduced density matrix ρ, with the other qubits traced out, as a table and a heatmap of |ρᵢⱼ|. Below the matrix:

- **Purity Tr(ρ²):** 1 for a pure state, down to 1/d (d = the matrix size) for a maximally mixed one.
- **Entanglement entropy S(ρ):** in bits, from 0 up to the number of qubits kept. Because the whole register is in a pure state, a nonzero entropy means the selected qubits are entangled with the rest.
- **For a single qubit:** its Bloch vector. Its length is 1 when the qubit is pure and less than 1 when it is entangled with the others.

For example, either qubit of a Bell pair has ρ = I/2, purity 0.5 and entropy 1 bit.

### Circuit

This tab describes the circuit rather than the state:

- **Counts:** gate counts by type; single-, two- and three-qubit gate counts; and parameterized gates.
- **T-count:** the number of T and T† gates.
- **Clifford and non-Clifford counts:** a gate is Clifford if it maps Pauli operators to Pauli operators. Rotations count as Clifford only at multiples of π/2.
- **Two depths:** *drawn depth* is the number of occupied columns as laid out. *Minimum depth* is the fewest layers possible if every gate ran as early as it could. A large difference between the two means the drawing spreads out gates that could run in parallel.

## With noise (v0.6.0)

When the circuit has noise (see [NOISE.md](NOISE.md)), the inspected state is a **mixed state** described by a density matrix ρ, and the inspector adapts:

| Tab | With noise |
|---|---|
| **Probabilities** (was Amplitudes) | Noisy probabilities (the diagonal of ρ) beside the ideal ones. A mixed state has no amplitudes or phases. |
| **Density matrix** (was Statevector) | The full ρ for up to 3 qubits, with purity Tr(ρ²) and fidelity ⟨ψ\|ρ\|ψ⟩ with the ideal state. The copy buttons are disabled, because there is no statevector. |
| **Reduced state** | Taken from the noisy ρ. Because the whole register is mixed, entropy now reflects noise as well as entanglement, and the verdict says so. |
| **Circuit** | Also lists the global noise preset and the number of noise elements. |

The header shows purity and fidelity at the current step. Up to 8 qubits this works at every step; for larger noisy circuits it is shown at the final column only.
