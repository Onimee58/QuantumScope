---
title: "Lab: train a quantum circuit"
area: qml
kind: lab
order: 92
objectives: Train a variational classifier | Read a training curve
---
# Lab: train a quantum circuit

A variational classifier is a circuit with trainable gates. Here you train one to separate the two moons.

[Open the Variational Classifier](qs:open/qml_variational)

```step
title: Train on the moons
text: Choose the dataset Moons, keep 3 trainable layers and BFGS, and press Train. Watch the loss fall and the decision regions take shape. The test accuracy should reach at least 80%.
check: qml dataset moons
check: qml variational test >= 0.8
```

```step
title: Look inside
text: Press Open in circuit simulator. The circuit for one test point opens in Quantum Circuits with the observable Z0: its ⟨Z0⟩ is the classifier's output before the bias.
check: observable Z0
```

```quiz
Q: The training curve is flat after 20 steps but accuracy is only 80%. What could help?
* More layers, or a new starting point (seed)
- Fewer test points
- A smaller learning rate only
E: A flat curve means the optimizer has converged; a more expressive circuit or another starting point can find a better minimum.
```
