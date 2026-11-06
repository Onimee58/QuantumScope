---
title: "Lab: MNIST, from pixels to qubits"
area: qml
kind: lab
order: 91
objectives: Prepare a real dataset for a quantum classifier | Classify handwritten digits with a quantum kernel | Use the bandwidth to smooth the classifier
---
# Lab: MNIST, from pixels to qubits

Each MNIST image has 784 pixels. To classify them with 4 qubits, the data must first be prepared.

[Open the Datasets experiment](qs:open/qml_datasets)

```step
title: Check and prepare MNIST
text: Choose MNIST and set Qubits (= features) to 4. Read the checker's findings: 10 classes, constant pixels, 784 features, many samples. Press Apply suggestions, then Prepare. The data now has 4 features.
check: qml dataset mnist
check: qml features = 4
```

```step
title: Classify the digits
text: Open the Quantum Kernel Classifier (+ in Quantum ML), choose From the Datasets tab, and press Train. Telling 0 from 1 should reach at least 95% test accuracy.
check: qml kernel test >= 0.95
```

```step
title: Smooth the classifier
text: Lower the Bandwidth to 0.5 or less and train again. Look at how the decision regions change: fewer islands, a smoother boundary.
check: qml bandwidth <= 0.5
check: qml kernel test >= 0.9
```
