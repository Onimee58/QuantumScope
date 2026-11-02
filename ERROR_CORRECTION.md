# Error correction and phase estimation

## Error-correcting codes (Examples menu)

| Example | Qubits | Corrects | How |
|---|---|---|---|
| **Bit-flip code** | 5 (data q0–q2, syndrome q3–q4) | one X error | Parity checks q0⊕q1 and q1⊕q2 are measured mid-circuit into c0 and c1; corrections are conditioned on both bits (c0c1 = 10 → q0, 11 → q1, 01 → q2) |
| **Phase-flip code** | 5 | one Z error | The same code in the \|±⟩ basis (Hadamards around the parity checks), corrected with Z |
| **Shor code (9 qubits)** | 9 | any single-qubit error (X, Y or Z) | The phase-flip code across three bit-flip blocks; corrected coherently with Toffoli majority votes, and the logical qubit ends back in q0 |

**Parameters:**
- **logical state:** the starting state of q0, one of the six standard states;
- **error:** none, one error on a chosen qubit, **two errors** (beyond what the code can correct), or **random errors on every data qubit** (noise boxes of strength p).

**The check** tests the current circuit for all six logical inputs. After correction, the data qubits must hold the encoded input.

## Logical error rate

**Plot logical error rate**, in the verification panel of the repetition codes:
- **What it does:** sets every noise box in the *current* circuit to strength p and plots the worst-case logical failure rate, together with the failure rate of an unprotected qubit.
- **It follows your edits:** change the circuit and the curve changes. For example, removing a correction gate visibly raises it.

**Quantum Circuits → + → Error-correction explorer** uses the same sweep. Choose a code (none, bit-flip or phase-flip) and a noise type (bit flips, phase flips or depolarizing), then drag p to read the verdict.

| Code against noise | Failure rate | Compared with one qubit |
|---|---|---|
| bit-flip code vs bit flips (or phase-flip code vs phase flips) | 3p² − 2p³ | better for every p < ½ (3.6× better at p = 0.1) |
| bit-flip code vs phase flips (or the reverse) | (1 − (1 − 2p)³)/2 ≈ 3p | **worse** |
| a repetition code vs depolarizing noise | — | worse: depolarizing noise contains both error types |

Our model puts errors only on the data qubits. With faulty gates, as on real devices, a code helps only below a *threshold* error rate.

## Conditions on several bits

Correcting the codes needs conditions on two bits at once. Right-click a gate and choose **Run only if… → Several bits…**, then pick 0, 1 or "any" for each measured bit. The gate shows a badge such as **c0c1=10**.

- **Files:** circuits with these conditions are saved as `.qscope` schema 6.
- **OpenQASM 2:** bits that are tested together share one register (`creg r0[2];`), and the condition becomes `if(r0==value)`, where `r0[0]` has weight 1.

## Quantum phase estimation (Algorithms menu)

It estimates φ in U = P(2πφ), with t = 1–6 counting qubits, the eigenstate |1⟩ in the last qubit, controlled powers of U, and the inverse QFT.

- **Exact phases** (3/8, 1/4, 5/16) give one certain result.
- **Inexact phases** (1/3, 0.3, 0.1) peak at the closest t-bit value, with probability at least 4/π² ≈ 0.405.

The check confirms both cases.

## Example titles and qubit labels

- **Title bar:** a circuit built from Examples or Algorithms shows a title bar with its parameters, **Change parameters…** and **Learn more**, which opens the matching lecture. It shows *(edited)* after changes; Undo removes that mark if the circuit matches the example again.
- **Labels:** examples label their qubits (data, syndrome, Alice, Bob…). Click any qubit's label → **Label this qubit…** to name the qubits of your own designs, up to 24 characters.
- **How labels behave:**
  - they're kept when the number of qubits changes;
  - **Clear** removes them along with everything else, and Undo brings them back;
  - they're saved in `.qscope` files, printed in PDF exports, and written as comments in QASM (`// q3: syndrome`).

## Learn more

- **Lectures:** *The bit-flip code*, *The phase-flip code*, *Logical error rates and thresholds*, *The Shor code and stabilizers*, *Quantum phase estimation*.
- **Labs:** *Build the bit-flip code*, *Beat the noise*, *Phase estimation precision*.
