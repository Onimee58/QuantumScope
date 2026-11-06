---
title: Generalization, bandwidth and kernel concentration
area: qml
kind: lecture
order: 4
objectives: Recognize overfitting in decision regions | Use the bandwidth to control a kernel | Explain kernel concentration and the effect of shot noise
math: 06-probability
---
# Generalization, bandwidth and kernel concentration

A classifier is only useful if it **generalizes**: if it is right on new data, not just on the points it learned from. Quantum kernels make this both easy to see and easy to get wrong.

## Overfitting

A classifier **overfits** when it learns the training points too exactly, noise included. In the decision regions this shows as **islands**: small patches of one class around single training points. Training accuracy is then high, while test accuracy drops.

## Bandwidth

QuantumScope's **bandwidth** $\beta$ scales the data before encoding, $x \to \beta x$ (Shaydulin and Wild, 2022). For angle encoding, for instance,

$$K_\beta(x, x') = \prod_k \cos^2\frac{\beta\,(x_k - x'_k)}{2}$$

so a small $\beta$ makes the kernel change slowly: nearby points look similar, and the boundary becomes smoother. A large $\beta$ makes it change fast, which can capture fine detail but also invites overfitting. No single value is best: on two Iris species the ZZ map goes from 75% test accuracy at $\beta = 1$ to 100% at $\beta = 0.1$, while the circles need a large $\beta$. The bandwidth has to be chosen for the data, like any other model setting.

## Kernel concentration

With an entangling feature map on more qubits, a serious problem appears: the states of different data points become almost orthogonal, so

$$K(x, x') \approx 0 \quad \text{for almost every pair } x \neq x'$$

This is **kernel concentration** (Thanasilp et al., 2024). The kernel matrix looks like the identity, the classifier learns little more than "every point is different", and on hardware the tiny values are lost in shot noise. QuantumScope warns when the average kernel value of different points falls below 0.05; a smaller bandwidth usually helps.

## Shot noise

On a quantum computer each kernel value is estimated from $N$ shots, with an error of about $\sqrt{K(1-K)/N}$. Small kernel values are therefore the hardest to measure, which is exactly where concentration pushes them. Set **Shots per entry** in the Quantum Kernel Classifier to see how accuracy changes with fewer shots.

## An honest outlook

For small, classical datasets like these, quantum kernels are **not known to beat** good classical methods: the classical Gaussian (RBF) kernel is a strong baseline. Researchers look for advantages in data with a quantum structure, or in problems that are hard to simulate classically. QuantumScope is for understanding how these methods work, and why their settings matter.

[Try it: compare bandwidths on Iris with the ZZ feature map](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: Training accuracy 100%, test accuracy 70%, and islands in the decision regions. What is happening?
* Overfitting: the classifier memorized the training points
- The test set is broken
- The kernel is concentrated, so it underfits
E: Islands around single training points, with a large gap between training and test accuracy, are the signs of overfitting.
```

```quiz
Q: The kernel matrix is close to the identity. What should you try?
- More shots only
* A smaller bandwidth (or fewer qubits, or a simpler feature map)
- A larger bandwidth
E: Near-zero kernel values for different points are kernel concentration; scaling the data down makes nearby states overlap again.
```

## Summary

- Overfitting shows as islands and a gap between training and test accuracy.
- The bandwidth controls how fast the kernel varies; choose it for the data.
- Kernel concentration makes different points look unrelated, and shot noise hides small kernel values.
