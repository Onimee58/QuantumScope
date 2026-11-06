# Learn: lectures, labs and your own course material

Each area (Hydrogen, Quantum Principles, Quantum Circuits) has a **📖 Learn** button beside the **+** on its tab bar. It opens the Learn window with:

- lectures and labs, listed by area;
- search;
- **Back** and **Forward**;
- text size (**A−**, **A+**);
- **Export PDF…**, which saves the lesson as a printable handout on white paper.

**Lectures** explain a topic with equations, worked examples and *Check your understanding* questions; choose **Show answer** to reveal each answer. Links marked **▶ Try it** set up the matching experiment in QuantumScope.

**Labs** are guided exercises. Keep the Learn window beside the circuit. Each step turns **✓ Done** as soon as your circuit meets its goal, and the progress counter shows how far you are.

## Your own lessons ("My course")

Choose **My course folder…** in the Learn window. Every `.md` file in that folder appears under **My course**. Lessons are plain Markdown, so you can write them in any text editor.

An optional header at the top sets the title, the order and the learning objectives:

```
---
title: Week 3 — Measurement
kind: lecture            (or lab)
order: 3
objectives: State the Born rule | Predict measurement statistics
---
```

Without a header, the first `# Heading` becomes the title.

### What you can write

| Feature | How to write it |
|---|---|
| Headings, **bold**, *italic*, `code` | `## Heading`, `**bold**`, `*italic*`, `` `code` `` |
| Lists, tables, notes | `- item`, `1. item`, `\| a \| b \|` tables, `> note` |
| Images | `![caption](picture.png)`, with the file in the same folder |
| Try it links | `[Try it: Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&inspector=1)` |
| Questions | a ` ```quiz ` block (see below) |
| Lab steps | a ` ```step ` block (see below) |

**Equations in your lessons.** The built-in lessons use pre-rendered equations, which your own lessons can't produce. Use Unicode instead (ψ, α, β, √, ⟩, ⊗, ½), or insert an image of the equation, for example one exported from LaTeX.

### Try it links

| Link | What it does |
|---|---|
| `qs:circuit?n=2&gates=H:0;CX:0,1&noise=Moderate&elements=depolarizing:1:2:0.4` | Adds noise. `noise` takes a preset (Ideal, Gentle, Moderate or Very noisy); `elements` takes channels as `channel:qubit:column:strength`, separated by `;`. A link without `noise=` starts with noise off. The same `noise=` works on algorithm links. |
| `qs:circuit?n=2&gates=H:0;CX:0,1&states=0,0&inspector=1` | Builds a circuit. Gates are `NAME:qubits[:angle]`, separated by `;`, with angles like `pi/2`. `states` gives each qubit's start: `0`, `1`, `+`, `-`, `+i` or `-i`. `inspector=1` also opens the State Inspector. |
| `qs:algorithm/bit_flip_code?logical=1&error=q1&p=0.1` | Builds an example from the Examples menu with its parameters (here the bit-flip code; also `phase_flip_code`, `shor_code`, `teleportation` and `superdense`) |
| `qs:circuit?n=1&gates=RY:0:0.4&bind=0:0:%5Ctheta&observable=Z0` | A circuit with a parameter: `bind=row:column:name[:factor]` ties a gate's angle to a parameter (`%5Ctheta` is `\theta`, which becomes θ); `observable` sets the observable |
| `qs:algorithm/grover?n=3&marked=101` | Builds an algorithm. The keys are `deutsch`, `deutsch_jozsa`, `bernstein_vazirani`, `grover`, `qft`, `qpe`, `vqe` and `qaoa`. |
| `qs:circuit?n=1&gates=X:0&cols=1&measures=0:0:0&conditions=0:1:0:1` | Builds a dynamic circuit. `cols` gives each gate's column, in order (otherwise gates fill columns 0, 1, 2, …); `measures` places M→c as `qubit:column:bit`; `resets` as `qubit:column`; `conditions` as `gate-row:column:bit:value`. Entries are separated by `;`. |
| `qs:example/Full adder` | Loads an example from the Examples menu. |
| `qs:gate/H`, `qs:try/CX` | Opens the Gate Explorer, or its Try it circuit. |
| `qs:inspector` | Opens the State Inspector. |
| `qs:open/dynamics3d` | Opens a view: `circuits`, `converter`, `orbital`, `dynamics2d`, `dynamics3d`, `doubleslit`, `superposition`, `entanglement`, `teleportation` or `qec` (the Error-correction explorer). |
| `qs:lesson/circuits/01-qubits` | Opens another lesson. |

### Questions

````
```quiz
Q: What is H|0⟩?
- |0⟩
* (|0⟩ + |1⟩)/√2
- |1⟩
E: The Hadamard maps |0⟩ to |+⟩.
```
````

Mark the correct answer with `*` and the others with `-`. `E:` is the explanation shown with the answer.

### Lab steps

````
```step
title: Entangle the qubits
text: Add a CX gate from q0 to q1.
hint: Drop CX on q1, then click q0.
check: state H:0;CX:0,1
```
````

A step is done when all of its `check:` lines pass. Once a later step passes, the earlier steps also count as done, since labs build on themselves.

| Check | Passes when |
|---|---|
| `qubits 2` | the circuit has exactly 2 qubits |
| `state H:0;CX:0,1` | the final state equals this circuit's output from \|0…0⟩, up to global phase |
| `probability 00=0.5 11=0.5` | the measurement probabilities are these (bit strings list q0 first) |
| `entangled 0` | q0 is maximally entangled with the rest (reduced entropy of at least 0.99 bit) |
| `gates <= 4` | the circuit uses at most 4 gates (also `>=` and `=`) |
| `uses H,CX` | the circuit contains these gate types |
| `starts 0:-` | q0 starts in \|−⟩ |
| `noise depolarizing` | a noise channel of this kind is placed in the circuit |
| `fidelity <= 0.8` | the fidelity of the (noisy) final state with the ideal one is at most 0.8 (also `>=`) |
| `purity <= 0.9` | the purity of the (noisy) final state is at most 0.9 (also `>=`) |
| `measures >= 2` | the circuit has at least 2 mid-circuit measurements (also `<=`, `=`) |
| `conditions = 2` | the circuit has exactly 2 classically conditioned gates (also `<=`, `>=`) |
| `branches = 4` | the circuit ends with 4 measurement branches (also `<=`, `>=`) |
| `record 00=0.5 11=0.5` | the classical records have these probabilities (c0 first) |
| `teleports 0 2` | in every branch, q2 ends in q0's starting state |
| `settles 0 0` | in every branch, q0 ends in \|0⟩ (`settles 0 1`: in \|1⟩) |
| `labeled 3 syndrome` | q3 is labeled "syndrome" (case does not matter) |
| `parameters >= 1` | the circuit has at least 1 parameter (also `<=`, `=`) |
| `bound >= 2` | at least 2 gate angles follow a parameter (also `<=`, `=`) |
| `observable Z0` | the observable is Z0 (`observable` alone: any observable) |
| `expectation <= -0.99` | ⟨observable⟩ for the final state is at most −0.99 (also `>=`) |
| `reaches 0.001` | ⟨observable⟩ is within 0.001 of its exact minimum |
| `verified` | the example's own check passes |

## Editing the built-in lessons (contributors)

Built-in lessons live in `src/quantumscope/learn/content/<area>/`. After editing their equations, run `python tools/render_equations.py --prune` (this needs matplotlib). The tests check that every equation has an up-to-date image, that every Try it link works, that every quiz has exactly one correct answer, and that every lab can be completed.

## Glossary links (v0.7.3)

Terms such as *Hermitian* or *Hamiltonian* are linked automatically: in every lesson, including yours in **My course**, the **first** occurrence of each glossary term is underlined. Clicking it opens a short definition, with related terms and **Learn more**, which opens the lesson that teaches it. All the terms are also listed on **Glossary** in the Learn contents.

- **Automatic linking** happens in paragraphs, lists, notes and tables, never in headings, quizzes, lab steps, code, equations or existing links. Longer terms win: "phase flip" links as itself, not as "phase". Acronyms (QFT, VQE) match exactly; other terms match in any case.
- **An explicit link:** write `[[Hermitian]]`, or `[[shown text|Hermitian]]` to link other words to a term. An unknown term stays plain text.
- **Turning a term off in one lesson,** where the word means something else, uses the header:

```
noglossary: Orbital, Circuit depth
```

- **Adding or editing terms:** edit `learn/content/glossary.md`. Each `### Term` may have `aliases:` (other forms that link), `lesson:` (the lecture key for Learn more) and `see:` (related terms), followed by the definition. `## Group` headings group the Glossary page.
- **PDF handouts** print the terms as plain text, with a **Terms used** box of their definitions at the end.

## Mathematics and "Math you need" (v0.7.7)

**Learn → Mathematics** has 12 lessons on the mathematics the other lessons use: complex numbers; vectors and Dirac notation; matrices acting on states; conjugate transpose, Hermitian and unitary; eigenvalues and eigenvectors; probability; tensor products; outer products, projectors and density matrices; matrix exponentials; Pauli algebra; the discrete Fourier transform; and gradients and optimization. They assume high-school algebra and trigonometry.

**Every physics lecture shows a "Math you need" box** under its objectives, with links to the lessons it builds on. Authors list them in the lesson's header, by file name, without the `math/` folder:

```
math: 07-tensor-products, 08-density-matrices-and-projectors
```

Your own lessons in **My course** can use the field too. The glossary's linear-algebra terms (Hermitian, unitary, eigenvalue, tensor product, Pauli matrices, Dirac notation), and ten new terms in its **Mathematics** group, open these lessons from **Learn more**.

## Quantum ML lessons and lab checks (v0.8.0)

**Learn → Quantum ML** has five lectures:
1. from data to quantum states;
2. kernel classifiers and the SVM;
3. variational classifiers;
4. generalization, bandwidth and kernel concentration;
5. preparing real data.

There are also three labs: classify the circles; MNIST, from pixels to qubits; and train a quantum circuit. **Quantum Circuits** gains a VQLS lecture and the lab "solve a linear system".

Lab steps in your own course can check what the student did in the Quantum ML area:

```
check: qml dataset mnist            the last data prepared or trained on is this dataset
check: qml features = 4             the prepared data has this many features (also <=, >=)
check: qml kernel test >= 0.95      the kernel classifier's last test accuracy (also: train)
check: qml kernel map zz            …trained with this feature map (angle or zz)
check: qml bandwidth <= 0.5         the kernel classifier's last bandwidth
check: qml shots >= 100             the kernel was estimated from at least this many shots
check: qml variational test >= 0.85 the variational classifier's last test accuracy (also: train)
```

Steps tick as soon as an experiment is run. Link to the experiments with `qs:open/qml_datasets`, `qs:open/qml_kernel` and `qs:open/qml_variational`.
