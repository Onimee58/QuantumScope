# Glossary

<!-- QuantumScope's glossary. Each "### Term" has optional "aliases:", "lesson:" (the lecture opened by
     Learn more) and "see:" (related terms) lines, then its definition. "## Group" headings group the
     Glossary page. In a lesson, the first occurrence of each term (or alias) is linked automatically;
     see LEARN.md for [[Term]] links and the noglossary: field. -->

## Quantum basics

### Qubit
aliases: qubits
lesson: circuits/01-qubits
see: Superposition, Bloch sphere
A two-level quantum system, the quantum version of a bit. Its state can be any superposition α|0⟩ + β|1⟩ with |α|² + |β|² = 1.

### Superposition
aliases: superpositions
lesson: principles/01-superposition-and-bloch-sphere
see: Amplitude, Measurement
A state that is a weighted sum of basis states, such as α|0⟩ + β|1⟩. A measurement gives one of the outcomes, with probabilities set by the weights.

### Amplitude
aliases: amplitudes, probability amplitude
lesson: circuits/01-qubits
see: Born rule, Phase
The complex number multiplying a basis state in a superposition. Its squared magnitude |α|² is the probability of that outcome.

### Basis state
aliases: basis states, computational basis
lesson: circuits/01-qubits
see: Qubit
One of the states |0⟩ and |1⟩ (|00⟩, |01⟩, … for several qubits) that a standard measurement returns.

### Dirac notation
aliases: ket, kets, bra-ket notation
lesson: math/02-vectors-and-dirac-notation
see: State vector
Notation for states: |ψ⟩ ("ket") is a column vector, ⟨ψ| ("bra") its conjugate transpose, and ⟨φ|ψ⟩ the inner product of two states.

### State vector
aliases: statevector, state vectors
lesson: circuits/01-qubits
see: Amplitude, Density matrix
The list of all amplitudes of a pure state. For n qubits it has 2ⁿ complex entries.

### Bloch sphere
lesson: principles/01-superposition-and-bloch-sphere
see: Qubit, Pure state
A sphere on which every pure state of one qubit is a point: |0⟩ at the north pole, |1⟩ at the south pole, and superpositions in between. Mixed states lie inside it.

### Spin
aliases: electron spin
lesson: principles/01-superposition-and-bloch-sphere
see: Qubit
An intrinsic angular momentum of particles. An electron's spin has two states along any axis, ↑ and ↓, which makes it a natural qubit.

### Phase
aliases: relative phase, global phase
lesson: principles/05-global-and-relative-phase
see: Interference, Amplitude
The angle of a complex amplitude. A global phase multiplies the whole state and has no observable effect; a relative phase between components changes how they interfere.

### Interference
aliases: interfere, interferes
lesson: principles/03-double-slit-interference
see: Phase
Amplitudes adding up (constructive) or cancelling (destructive) when paths combine, producing patterns such as the double-slit fringes.

## Measurement

### Measurement
aliases: measurements
lesson: principles/02-measurement-and-born-rule
see: Born rule, Collapse
Reading out a quantum system. It gives one definite result, with Born-rule probability, and leaves the system in the state matching that result.

### Born rule
lesson: principles/02-measurement-and-born-rule
see: Amplitude, Measurement
The rule that the probability of a measurement outcome is the squared magnitude of its amplitude.

### Collapse
aliases: state collapse, wave-function collapse
lesson: principles/02-measurement-and-born-rule
see: Measurement
The change of a state into the state of the measured outcome, after a measurement.

### No-cloning theorem
aliases: no-cloning
lesson: principles/07-measurement-information-no-cloning
see: Teleportation
No process can make an independent copy of an unknown quantum state.

### Observable
aliases: observables
lesson: principles/08-observables
see: Hermitian, Expectation value, Eigenvalue
A measurable quantity, represented by a Hermitian operator. Its eigenvalues are the possible measurement results.

### Expectation value
aliases: expectation values, expected value
lesson: principles/08-observables
see: Observable
The average result of measuring an observable many times on the same state: ⟨O⟩ = ⟨ψ|O|ψ⟩.

### Variational principle
lesson: principles/08-observables
see: Ground state, VQE
For every state, ⟨H⟩ is at least the ground-state energy, so lowering ⟨H⟩ approaches it.

## Linear algebra

### Hermitian
aliases: Hermitian operator, Hermitian matrix, Hermitian operators, Hermitian matrices, self-adjoint
lesson: math/04-hermitian-and-unitary
see: Observable, Eigenvalue
Equal to its own conjugate transpose, H = H†. Hermitian operators have real eigenvalues and represent observables.

### Unitary
aliases: unitary operator, unitary matrix, unitaries
lesson: math/04-hermitian-and-unitary
see: Quantum gate
Satisfying U†U = I, so it preserves lengths and therefore probabilities. Every quantum gate is unitary.

### Eigenvalue
aliases: eigenvalues, eigenvector, eigenvectors, eigenstate, eigenstates
lesson: math/05-eigenvalues
see: Hermitian, Observable
For an operator A, a vector v with Av = λv is an eigenvector, and λ its eigenvalue. An eigenstate of an observable has a definite measurement result.

### Tensor product
aliases: tensor products, Kronecker product
lesson: math/07-tensor-products
see: Product state
The way states and operators of separate systems combine into one. Two qubits give 2 × 2 = 4 amplitudes, n qubits 2ⁿ.

### Pauli matrices
aliases: Pauli matrix, Pauli operators, Pauli operator
lesson: math/10-pauli-algebra
see: Observable
The 2×2 matrices X, Y and Z (with the identity I). As gates they flip the bit (X), the phase (Z) or both (Y); every one-qubit observable is a sum of them.

## Gates and circuits

### Quantum gate
aliases: quantum gates
lesson: circuits/02-single-qubit-gates
see: Unitary
An operation on qubits, described by a unitary matrix. A circuit is a sequence of gates.

### Hadamard gate
aliases: Hadamard
lesson: circuits/02-single-qubit-gates
see: Superposition
The gate taking |0⟩ to |+⟩ and |1⟩ to |−⟩, creating equal superpositions.

### Rotation gate
aliases: rotation gates
lesson: circuits/02-single-qubit-gates
see: Bloch sphere
RX, RY and RZ, which rotate the Bloch vector about the x, y or z axis by an angle θ.

### CNOT
aliases: controlled-NOT
lesson: circuits/03-multi-qubit-gates
see: Controlled gate, Entanglement
The gate that flips its target qubit when its control qubit is 1. With a Hadamard before it, it creates entanglement.

### Controlled gate
aliases: controlled gates, control qubit
lesson: circuits/03-multi-qubit-gates
see: CNOT, Toffoli gate
A gate applied to its target qubits only when its control qubit (or qubits) is 1.

### Toffoli gate
aliases: Toffoli
lesson: circuits/06-reversible-logic
see: Reversible computation
The gate that flips its target when both controls are 1: a reversible AND.

### Reversible computation
aliases: reversible logic
lesson: circuits/06-reversible-logic
see: Unitary
Computation in which every step can be undone, as unitary gates require.

### Oracle
aliases: oracles
lesson: circuits/07-phase-kickback-and-oracles
see: Phase kickback, Grover's algorithm
A black-box gate that encodes a function, queried by algorithms such as Deutsch–Jozsa and Grover.

### Phase kickback
lesson: circuits/07-phase-kickback-and-oracles
see: Phase estimation
When a controlled gate acts on one of its eigenstates, the eigenvalue's phase appears on the control qubit instead.

### Grover's algorithm
aliases: Grover search, amplitude amplification
lesson: circuits/08-grover-search
see: Oracle
Finds a marked item among N in about √N queries, by repeatedly amplifying its amplitude.

### Quantum Fourier transform
aliases: QFT
lesson: circuits/09-qft
see: Phase estimation
The quantum version of the discrete Fourier transform, acting on amplitudes. It is a key step in phase estimation and Shor's algorithm.

### Circuit depth
aliases: depth
lesson: circuits/10-circuit-cost
see: Quantum gate
The number of gate layers that cannot run at the same time: a measure of how long a circuit takes.

### Clifford gates
aliases: Clifford gate, Clifford circuits
lesson: circuits/10-circuit-cost
see: T gate
The gates generated by H, S and CNOT. Circuits made only of them can be simulated efficiently on a classical computer.

### T gate
aliases: T-count
lesson: circuits/10-circuit-cost
see: Clifford gates
The π/8 phase gate. Added to the Clifford gates, it makes quantum computation universal; the T-count is how many a circuit uses.

## Entanglement and states

### Entanglement
aliases: entangled
lesson: principles/04-entanglement-and-bell-states
see: Bell state, Product state
Correlation between qubits that cannot be described by giving each qubit its own state, as in (|00⟩ + |11⟩)/√2.

### Bell state
aliases: Bell states, Bell pair, Bell pairs, EPR pair
lesson: principles/04-entanglement-and-bell-states
see: Entanglement
The four maximally entangled two-qubit states, such as |Φ⁺⟩ = (|00⟩ + |11⟩)/√2.

### Product state
aliases: product states, separable state
lesson: circuits/04-entanglement-in-circuits
see: Entanglement, Tensor product
A multi-qubit state that can be written as one state per qubit, |ψ⟩ ⊗ |φ⟩: not entangled.

### Density matrix
aliases: density matrices, density operator
lesson: principles/06-density-matrices-and-mixed-states
see: Mixed state, Purity
A matrix ρ that describes a state including classical uncertainty. For a pure state, ρ = |ψ⟩⟨ψ|.

### Pure state
aliases: pure states
lesson: principles/06-density-matrices-and-mixed-states
see: Mixed state
A state described by a single state vector. Its purity Tr(ρ²) is 1.

### Mixed state
aliases: mixed states
lesson: principles/06-density-matrices-and-mixed-states
see: Density matrix, Purity
A probabilistic mixture of pure states, described by a density matrix with purity below 1.

### Purity
lesson: principles/06-density-matrices-and-mixed-states
see: Mixed state
Tr(ρ²): 1 for a pure state, down to 1/d for the completely mixed state in d dimensions.

### Fidelity
lesson: circuits/11-noise-and-decoherence
see: Purity
How close two states are, from 0 (completely different) to 1 (the same). For pure states it is |⟨φ|ψ⟩|².

## Noise

### Decoherence
lesson: circuits/11-noise-and-decoherence
see: Noise channel, Dephasing
The loss of quantum behaviour (superposition, entanglement) as a system interacts with its surroundings.

### Noise channel
aliases: quantum channel, noise channels
lesson: circuits/11-noise-and-decoherence
see: Kraus operators
A description of how noise changes a density matrix: bit flip, phase flip, depolarizing, amplitude damping and others.

### Kraus operators
aliases: Kraus operator
lesson: circuits/11-noise-and-decoherence
see: Noise channel
A set of matrices Kᵢ that describe a noise channel: ρ → Σ Kᵢ ρ Kᵢ†.

### Depolarizing noise
aliases: depolarizing channel
lesson: circuits/11-noise-and-decoherence
see: Noise channel
Noise that, with probability p, replaces the state by a completely random one.

### Amplitude damping
lesson: circuits/11-noise-and-decoherence
see: Noise channel
Energy loss: |1⟩ decays toward |0⟩, as in spontaneous emission.

### Dephasing
aliases: phase damping
lesson: circuits/11-noise-and-decoherence
see: Decoherence, Phase
Noise that destroys the relative phase between |0⟩ and |1⟩ without changing their probabilities.

## Measurement in circuits

### Classical bit
aliases: classical bits
lesson: circuits/12-mid-circuit-measurement
see: Mid-circuit measurement
An ordinary 0/1 value that stores a measurement result inside a circuit.

### Mid-circuit measurement
aliases: mid-circuit measurements
lesson: circuits/12-mid-circuit-measurement
see: Feed-forward
Measuring a qubit during a circuit, not only at the end, and storing the result in a classical bit.

### Feed-forward
aliases: classical control, classically controlled
lesson: circuits/13-feed-forward-and-reset
see: Classical bit
Using a measurement result to decide which gates run later in the same circuit.

### Teleportation
aliases: quantum teleportation
lesson: circuits/14-teleportation
see: Bell state, No-cloning theorem
Moving an unknown qubit state to a distant qubit using a shared Bell pair and two classical bits. The original is destroyed in the process.

### Superdense coding
lesson: circuits/15-superdense-coding
see: Bell state
Sending two classical bits by transmitting a single qubit of a shared Bell pair.

### Deferred measurement
aliases: deferred-measurement principle
lesson: circuits/16-deferred-measurement
see: Feed-forward
The principle that measurements can be moved to the end of a circuit by replacing classical control with quantum control.

## Error correction

### Quantum error correction
aliases: error correction, error-correcting code, error-correcting codes
lesson: circuits/17-bit-flip-code
see: Logical qubit, Syndrome
Protecting quantum information by encoding one logical qubit in several physical qubits and fixing the errors that are detected.

### Logical qubit
aliases: logical qubits, physical qubit, physical qubits
lesson: circuits/17-bit-flip-code
see: Quantum error correction
A qubit encoded across several physical qubits by an error-correcting code.

### Syndrome
aliases: syndromes, error syndrome
lesson: circuits/17-bit-flip-code
see: Stabilizer
The measured parities that reveal which error happened, without revealing the encoded state.

### Bit flip
aliases: bit flips, bit-flip error
lesson: circuits/17-bit-flip-code
see: Phase flip, Pauli matrices
An error that swaps |0⟩ and |1⟩, like an X gate.

### Phase flip
aliases: phase flips, phase-flip error
lesson: circuits/18-phase-flip-code
see: Bit flip, Dephasing
An error that changes the sign of |1⟩'s amplitude, like a Z gate.

### Threshold
aliases: error threshold, fault-tolerance threshold
lesson: circuits/19-logical-error-rates
see: Quantum error correction
The physical error rate below which error correction lowers the logical error rate as codes grow larger.

### Stabilizer
aliases: stabilizers, stabilizer code, stabilizer codes
lesson: circuits/20-shor-code
see: Syndrome
An operator that leaves every code state unchanged. Measuring the stabilizers gives the syndrome.

## Algorithms

### Phase estimation
aliases: quantum phase estimation, QPE
lesson: circuits/21-phase-estimation
see: Quantum Fourier transform, Phase kickback
An algorithm that measures the phase φ of an eigenvalue e^{2πiφ} of a unitary, to a chosen number of bits.

### Parameterized circuit
aliases: parameterized circuits, variational circuit, variational circuits
lesson: circuits/22-parameterized-circuits
see: Ansatz, Parameter-shift rule
A circuit whose gate angles are adjustable parameters, tuned by a classical optimizer.

### Ansatz
aliases: ansätze, ansatzes
lesson: circuits/24-vqe
see: Parameterized circuit
The parameterized circuit used as the "guess" in a variational algorithm. Its structure limits which states can be reached.

### Parameter-shift rule
lesson: circuits/23-parameter-shift-rule
see: Parameterized circuit
An exact way to compute a gradient from two circuit runs, with a parameter shifted by +π/2 and −π/2.

### Hamiltonian
aliases: Hamiltonians
lesson: circuits/24-vqe
see: Ground state, Observable
The observable for a system's energy. It also determines how the system evolves in time; its lowest eigenvalue is the ground-state energy.

### Ground state
aliases: ground-state energy, ground states
lesson: circuits/24-vqe
see: Hamiltonian, Variational principle
The lowest-energy state of a system: the eigenstate of the Hamiltonian with the smallest eigenvalue.

### VQE
aliases: variational quantum eigensolver
lesson: circuits/24-vqe
see: Ansatz, Variational principle
An algorithm that finds a ground-state energy by optimizing a parameterized circuit to minimize ⟨H⟩.

### Local minimum
aliases: local minima
lesson: circuits/25-optimizers-and-landscapes
see: Barren plateau
A valley that is lower than its surroundings but not the lowest point overall.

### Barren plateau
aliases: barren plateaus
lesson: circuits/25-optimizers-and-landscapes
see: Local minimum
A region where the gradient is nearly zero in every direction, so optimizers make little progress.

### QAOA
aliases: quantum approximate optimization algorithm
lesson: circuits/26-qaoa-maxcut
see: MaxCut, Parameterized circuit
An algorithm that alternates cost and mixer layers, with angles γ and β, to find good solutions to optimization problems such as MaxCut.

### MaxCut
lesson: circuits/26-qaoa-maxcut
see: QAOA
Splitting a graph's nodes into two groups so that as many edges as possible join the groups.

## Hydrogen

### Schrödinger equation
lesson: hydrogen/01-schrodinger-and-hydrogen
see: Wave function, Energy level
The equation that governs how quantum states evolve and, for stationary states, which energies are allowed.

### Wave function
aliases: wave functions, wavefunction, wavefunctions
lesson: hydrogen/01-schrodinger-and-hydrogen
see: Probability density
The amplitude ψ(r) for finding a particle at position r. Its squared magnitude |ψ(r)|² is the probability density.

### Orbital
aliases: orbitals, atomic orbital, atomic orbitals
lesson: hydrogen/02-quantum-numbers-and-orbitals
see: Quantum numbers
A one-electron wave function of an atom, labelled by its quantum numbers n, l and m.

### Quantum numbers
aliases: quantum number, principal quantum number
lesson: hydrogen/02-quantum-numbers-and-orbitals
see: Orbital
The labels of hydrogen's states: n (energy and size), l (angular momentum, which sets the shape) and m (orientation).

### Probability density
aliases: probability densities
lesson: hydrogen/03-probability-density
see: Wave function, Born rule
|ψ|²: the probability per unit volume of finding the electron at a point.

### Energy level
aliases: energy levels
lesson: hydrogen/04-energy-levels-and-spectra
see: Spectral line
An allowed energy of a bound system. For hydrogen, Eₙ = −13.6 eV / n² (slightly corrected for the proton's finite mass).

### Spectral line
aliases: spectral lines
lesson: hydrogen/04-energy-levels-and-spectra
see: Energy level
Light emitted or absorbed when the electron moves between energy levels. The photon's energy equals the difference between the levels.

## Mathematics

### Complex number
aliases: complex numbers, imaginary unit, complex conjugate
lesson: math/01-complex-numbers
see: Amplitude, Phase
A number a + bi, with i² = −1. Its modulus |z| = √(a² + b²) is its distance from 0; the conjugate a − bi mirrors it. Amplitudes are complex numbers.

### Conjugate transpose
aliases: dagger, Hermitian conjugate, adjoint
lesson: math/04-hermitian-and-unitary
see: Hermitian, Unitary
A matrix flipped over its diagonal with every entry conjugated, written A†. It turns a ket into its bra, and (AB)† = B†A†.

### Inner product
aliases: inner products
lesson: math/02-vectors-and-dirac-notation
see: Dirac notation, Fidelity
The number ⟨φ|ψ⟩ measuring how two states overlap: 1 for the same normalized state, 0 for orthogonal ones. |⟨φ|ψ⟩|² is a probability.

### Outer product
aliases: outer products
lesson: math/08-density-matrices-and-projectors
see: Projector, Density matrix
The matrix |ψ⟩⟨φ|, a column times a row. For a normalized state, |ψ⟩⟨ψ| is a projector and the state's density matrix.

### Projector
aliases: projectors, projection operator
lesson: math/08-density-matrices-and-projectors
see: Measurement, Outer product
A matrix P with P² = P that keeps the part of a state along some direction. Measurements are described by projectors.

### Trace
lesson: math/08-density-matrices-and-projectors
see: Density matrix, Partial trace
The sum of a matrix's diagonal entries. A density matrix has trace 1, and Tr(ρA) is the expectation value of A.

### Partial trace
aliases: partial traces, reduced state, reduced density matrix
lesson: math/08-density-matrices-and-projectors
see: Density matrix, Entanglement
The operation that gives one part of a system its own state. For a Bell pair, each qubit's reduced state is completely random.

### Matrix exponential
aliases: matrix exponentials
lesson: math/09-matrix-exponentials
see: Rotation gate, Hamiltonian
e^A, defined by the series I + A + A²/2! + … . Rotation gates are e^{−iθP/2} for a Pauli P, and time evolution is e^{−iHt/ħ}.

### Commutator
aliases: commutators, anticommutator, anticommutators
lesson: math/10-pauli-algebra
see: Pauli matrices, Observable
[A, B] = AB − BA, zero when the order does not matter. Observables that do not commute, like X and Z, cannot both have definite values.

### Gradient
aliases: gradients, gradient descent
lesson: math/12-gradients-and-optimization
see: Parameter-shift rule, Local minimum
The vector of partial derivatives, pointing uphill. Gradient descent steps against it to minimize a cost, as the variational optimizers do.

## Quantum machine learning

### Feature map
aliases: feature maps, angle encoding, ZZ feature map
lesson: qml/01-data-to-quantum-states
see: Quantum kernel, Parameterized circuit
A circuit U(x) whose angles are set by a data point x, turning it into a quantum state |φ(x)⟩ = U(x)|0…0⟩.

### Quantum kernel
aliases: quantum kernels, kernel matrix, kernel matrices
lesson: qml/01-data-to-quantum-states
see: Feature map, Kernel trick
The similarity of two data points as quantum states: K(x, x′) = |⟨φ(x)|φ(x′)⟩|², 1 for the same point and near 0 for very different ones.

### Kernel trick
lesson: qml/02-kernel-classifiers
see: Quantum kernel, Support vector machine
Learning from the kernel values of all pairs of points alone, without ever writing out the states (or features) they come from.

### Support vector machine
aliases: support vector machines, SVM, SVMs, support vectors
lesson: qml/02-kernel-classifiers
see: Kernel trick, Kernel ridge
A classifier that finds the boundary with the widest margin between two classes. Only the support vectors, the points on or inside the margin, define it.

### Kernel ridge
aliases: kernel ridge regression, kernel ridge classification
lesson: qml/02-kernel-classifiers
see: Support vector machine
A kernel classifier with the closed-form weights α = (K + λI)⁻¹ y; the regularization λ makes it smoother.

### Variational classifier
aliases: variational classifiers, variational quantum classifier
lesson: qml/03-variational-classifiers
see: Parameterized circuit, Parameter-shift rule
A trainable circuit used as a classifier: its output ⟨Z₀⟩ plus a bias decides the class, and training tunes its gates.

### Training set
aliases: training sets, training data, training split
lesson: qml/02-kernel-classifiers
see: Test set, Overfitting
The data a classifier learns from.

### Test set
aliases: test sets, test data, test split
lesson: qml/02-kernel-classifiers
see: Training set, Data leakage
Data kept aside to measure how well a classifier does on points it has never seen: the honest score.

### Overfitting
aliases: overfit, overfits, overfitted
lesson: qml/04-generalization-and-its-limits
see: Bandwidth, Test set
Learning the training points too exactly, noise included: high training accuracy, lower test accuracy, and islands in the decision regions.

### Bandwidth
aliases: kernel bandwidth
lesson: qml/04-generalization-and-its-limits
see: Quantum kernel, Overfitting
A factor that scales the data before encoding. A small bandwidth makes the kernel vary slowly and the classifier smoother.

### Kernel concentration
aliases: exponential concentration
lesson: qml/04-generalization-and-its-limits
see: Quantum kernel, Bandwidth
Kernel values close to 0 for almost every pair of different points, common for entangling feature maps on many qubits: the classifier then learns little.

### Principal component analysis
aliases: PCA, principal components, principal component
lesson: qml/05-preparing-real-data
see: Eigenvalue
A way to reduce data to fewer features by keeping the directions in which it varies most: the leading eigenvectors of its covariance matrix.

### Data leakage
aliases: leakage
lesson: qml/05-preparing-real-data
see: Test set
Letting information about the test data influence the model, for example by fitting a scaling on all the data; it makes test scores look better than they are.

### Condition number
aliases: condition numbers
lesson: circuits/27-vqls
see: Eigenvalue
κ = σmax / σmin, the ratio of a matrix's largest to its smallest singular value. A large κ makes A x = b harder to solve.
