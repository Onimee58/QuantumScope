# Entanglement Station: Professor Demo Guide

This interactive visualization models ideal spin-1/2 *qubits* using electron symbols. It does not simulate a literal lab apparatus or electron trajectories.

1. Open **New Experiment > Quantum Entanglement**. Initially, Alice and Bob each have an independently prepared state, |psi_A> and |psi_B>.
2. Adjust each electron's **initial polar angle theta** and **phase phi** with sliders or degree inputs. The product state is |psi_A> tensor |psi_B>.
3. Start from defaults (all 0 degrees) and click **Send electrons through entangling box**. The box represents **Hadamard on Alice, then CNOT controlled by Alice**. Output from |up,up> is Bell |Phi+> = (|up,up> + |down,down>)/sqrt(2).
4. After the schematic separation, click either electron or use the Measure Alice/Bob buttons. Each click performs a local projective measurement and reveals only that electron's outcome. The joint post-measurement state is updated internally.
5. Change measurement axes *before measuring*; the displayed theoretical joint outcome distribution updates without moving the electrons. Collect statistics across separately prepared pairs.
6. Click **Reset to independent electrons** to change the initial spin preparation. Try Alice theta=90, phi=0, Bob theta=0, phi=0: this gate sequence produces a *separable* output. A box containing an entangling-capable gate does not entangle every possible input.

## Scientific boundaries

- The animation shows an ideal gate sequence and local measurements; no physical travel, wire connecting entangled particles, instantaneous signaling, or universal deterministic preparation of a fixed Bell state is claimed.
- The initial state is a product of individual spin wavefunctions. After the joint gate sequence, the two-qubit *joint* state is shown with four complex basis amplitudes. It can be entangled or separable depending on input.
- Concurrence C=0 means separable; C=1 means maximally entangled (for pure two-qubit states).
- The default Bell state here is **|Phi+>**, not the spin singlet **|Psi->** previously used by the demonstration. Their same-axis correlations differ; this change is intentional and physically important.
- All modeled spin axes used for measurement lie in the xz plane, while initial spin-state phases can vary over the Bloch sphere.

## Persistent three-stage explanation

The right panel now keeps **BEFORE**, **ENTANGLING OPERATION**, and **AFTER** visible at the same time. BEFORE gives Alice's and Bob's individual spin amplitudes, the middle card identifies H(A) then CNOT(A,B), and AFTER shows the joint output amplitudes and concurrence. Hover over the final card for the complete (untruncated) joint state.

Use **Back** and **Next** to highlight each explanation without undoing any measurement. **Replay preparation** starts a *fresh* pair with the currently selected preparation settings and replays the gate-station animation. It never time-reverses a measured state. Click the electrons in the larger scene only after preparation completes.

### Visual three-stage overview

The persistent overview shows independently prepared spins and their spin-up
probabilities, the **H on Alice + controlled-NOT (Alice controls Bob)** gate
circuit, and the resulting joint-state concurrence. A wire on the circuit is
an abstract qubit register, not an electron trajectory. To inspect complete
state amplitudes, use the text below the large animation scene.

The highlighted stage can be changed with Back and Next without changing the
quantum state. Replay prepares a fresh pair. Click the electron symbols in the
main scene after preparation to measure them. The instruction is drawn below
the electrons to avoid hiding either target.
