# Algorithms, blocks and examples

QuantumScope v0.5.1 adds an **Algorithms** menu, expandable **blocks** for oracles and subroutines, new reversible-logic examples, the controlled-phase gate **CP**, and worked identities in the Gate Explorer.

## Blocks

A block is a named group of real gates that the editor treats as one operation, for example *Oracle*, *Diffusion* or *QFT*.

- **Collapsed:** a labeled box showing how many gates it contains. It occupies one column.
- **Expanded:** double-click the box (or right-click → **Expand to gates**). Its gates appear over several columns inside a light dashed outline. Click the **Collapse** chip on the outline, or right-click → **Collapse**, to fold it again. Columns added by expanding are removed when you collapse.
- **Locked contents:** gates inside a block cannot be moved, edited or removed one by one. A block reserves every wire between its top and bottom qubit across its columns, so no other gate can be placed inside it. To change the contents:
  - **Edit block…** changes the block's parameters, such as Grover's marked item or an oracle's hidden string. The block is rebuilt correctly and keeps its place.
  - **Ungroup** turns the block into ordinary editable gates. This is permanent, but Undo restores the block.
- **As a unit:** drag a block, from any of its cells, to move the whole block. Right-click → **Remove block** deletes all of it. **Show contents…** lists its gates and, for blocks of up to 3 qubits, shows its matrix.

Simulation always uses the real gates, so a circuit gives exactly the same result whether its blocks are collapsed or expanded. The State Inspector steps through a collapsed block in one step and through an expanded one gate by gate. Its Circuit tab always counts the real gates inside blocks (T-count, depth and so on), so collapsing a block never hides its cost. Blocks are one level deep: a block cannot contain another block.

## Algorithms

Choose one from **Algorithms…** in the circuit tab and set its parameters. The algorithms with an ancilla qubit start it in |−⟩ using the initial-state feature, as textbooks draw them. With the ancilla in |−⟩, f(x) appears as a phase (−1)^f(x) on the input register ("phase kickback").

| Algorithm | Parameters | What it shows |
|---|---|---|
| Deutsch | one of the four 1-bit functions | one query decides constant or balanced |
| Deutsch–Jozsa | 1–6 input qubits; constant 0, constant 1, or balanced f(x) = s·x | constant gives \|0…0⟩ with certainty; balanced never does |
| Bernstein–Vazirani | 1–6 input qubits; hidden string s | the input register measures s with certainty, after one query |
| Grover search | 2–5 search qubits; marked item; iterations (or Optimal) | success probability sin²((2k+1)θ), with sin θ = 1/√N, including the overshoot past the optimum |
| Quantum Fourier transform | 1–6 qubits; input value x; optionally followed by QFT† | QFT\|x⟩ = (1/√N) Σ e^{2πixy/N}\|y⟩; the phase pattern is visible in the State Inspector |

Notes on the circuits:

- **Grover** on 4 or more search qubits needs a multi-controlled Z. It is built from Toffoli gates with extra *work qubits* placed below the search register. They start in |0⟩ and are returned to |0⟩.
- **QFT** uses the new CP gate. The input |x⟩ is set by the initial states, so you can change it by clicking the wire labels.

### Specification checks

Each algorithm's specification runs on the **current** circuit and is shown in the verification panel, so edits are judged against the physics:

- **Deutsch, Deutsch–Jozsa and Bernstein–Vazirani** read the function from the oracle block that is present. Edit the oracle and the expected result changes with it.
- **Grover** counts the Oracle blocks present (k) and reads their marked item. If you remove an iteration, the check compares against sin²((2k+1)θ) for the new k. If the oracles disagree, or the diffusions don't match the oracles, it reports that instead of a pass or fail.
- **QFT** compares the final state with the textbook DFT matrix applied to the initial state, so it works for any input, even a superposition.

If you ungroup an oracle, the check falls back to the originally chosen function and says so.

## Reversible-logic examples

The **Examples…** menu also offers these circuits. Their inputs are set with the initial states (|0⟩ or |1⟩), and the truth table checks **every** input combination:

| Example | Qubits | Function |
|---|---|---|
| Full adder | a, b (restored), cin → sum, cout | sum = a ⊕ b ⊕ cin; cout = majority |
| 2-bit comparator | A = q0q1, B = q2q3 (restored), q4 = (A = B), q5 = (A > B), q6 work | equality and greater-than |
| Controlled increment | control, 2-bit counter | counter + 1 (mod 4) when the control is 1 |
| Toffoli as AND | a, b, out | out = a AND b |
| Fredkin multiplexer | s, x, y | swaps x and y when s = 1, so q1 = (s ? y : x) |

## The CP gate

CP(λ) = diag(1, 1, 1, e^{iλ}) adds the phase e^{iλ} to |11⟩. It is symmetric in its two qubits, CP(π) = CZ, and it is Clifford only when λ is a multiple of π. In QASM it is written `cp(λ)`; the older name `cu1` is also read.

## Gate Explorer additions

- **Worked identity:** for H, X, Z, S, T, S†, T†, SX, CX, CZ and SWAP, a tab follows every basis state through a sequence of gates and compares the result with the single equivalent gate, for example H Z H = X.
- **Try it in the circuit:** loads the gate into a small circuit with starting states chosen so that its effect is visible. Phase gates act on |+⟩, and controlled gates get a control in |+⟩, so they create entanglement.

## Files

- **.qscope:** circuits containing blocks are saved as `.qscope` format version 3. Each block is stored with its real gates, parameters and expanded state, so it reopens exactly as left. Older QuantumScope versions refuse version-3 files instead of misreading them. Circuits without blocks keep their earlier format.
- **OpenQASM 2:** export writes each block as its expanded gates, preceded by a comment such as `// block: Oracle on q0,q1,q2 (marked=101)`. Importing that file gives plain gates.
- **PDF:** export draws collapsed blocks as labeled boxes, and expanded blocks with their outline.
