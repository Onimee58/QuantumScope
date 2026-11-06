---
title: "Lab: classify the circles"
area: qml
kind: lab
order: 90
objectives: Train a quantum kernel classifier | Compare two feature maps on the same data
---
# Lab: classify the circles

Two classes of points lie on two circles, one inside the other. No straight line separates them, but a quantum kernel can.

[Open the Quantum Kernel Classifier](qs:open/qml_kernel)

```step
title: Train with angle encoding
text: Choose the dataset Circles, the feature map Angle encoding and the classifier Support vector machine, then press Train. The decision regions should show a ring, and the test accuracy should be at least 90%.
check: qml dataset circles
check: qml kernel map angle
check: qml kernel test >= 0.9
```

```step
title: Try the ZZ feature map
text: Change the feature map to the ZZ feature map and train again. Compare the decision regions and the test accuracy with angle encoding.
check: qml kernel map zz
```

```quiz
Q: Which feature map is better for the circles here?
* Angle encoding: its smooth kernel matches the circles' simple shape
- The ZZ map, because entanglement always helps
E: More expressive is not always better: the ZZ map's kernel varies faster than these data need.
```
