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
| `qs:algorithm/grover?n=3&marked=101` | Builds an algorithm. The keys are `deutsch`, `deutsch_jozsa`, `bernstein_vazirani`, `grover`, `qft` and `qpe`. |
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

## Editing the built-in lessons (contributors)

Built-in lessons live in `src/quantumscope/learn/content/<area>/`. After editing their equations, run `python tools/render_equations.py --prune` (this needs matplotlib). The tests check that every equation has an up-to-date image, that every Try it link works, that every quiz has exactly one correct answer, and that every lab can be completed.
