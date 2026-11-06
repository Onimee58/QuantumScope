---
title: Matrix exponentials and rotations
area: math
kind: lecture
order: 9
objectives: Compute e^{−iθX/2} from the exponential series | Recognize rotation gates as exponentials of Paulis | Relate time evolution to e^{−iHt}
---
# Matrix exponentials and rotations

Rotation gates, time evolution and phases all come from one operation: the **exponential of a matrix**.

## The exponential series

For numbers, $e^x = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \dots$. The same series defines $e^A$ for a square matrix $A$:

$$e^{A} = I + A + \frac{A^2}{2!} + \frac{A^3}{3!} + \dots$$

## Paulis square to the identity

The series becomes simple for Pauli matrices because $X^2 = Y^2 = Z^2 = I$. Splitting it into even and odd powers gives, for $P = X$, $Y$ or $Z$:

$$e^{-i\theta P/2} = \cos\frac{\theta}{2}\, I - i\,\sin\frac{\theta}{2}\, P$$

This is the same pattern as Euler's formula, $e^{-i\theta/2} = \cos\frac{\theta}{2} - i\sin\frac{\theta}{2}$, with the matrix $P$ in place of the number 1.

## Rotation gates

The rotation gates are exactly these exponentials:

$$R_X(\theta) = e^{-i\theta X/2}, \qquad R_Y(\theta) = e^{-i\theta Y/2}, \qquad R_Z(\theta) = e^{-i\theta Z/2}$$

$R_X(\theta)$ turns the Bloch vector by the angle $\theta$ about the $x$ axis, and likewise for $y$ and $z$. For example

$$R_Y(\theta) = \begin{pmatrix} \cos\frac{\theta}{2} & -\sin\frac{\theta}{2} \\ \sin\frac{\theta}{2} & \cos\frac{\theta}{2} \end{pmatrix}$$

so $R_Y(\pi)|0\rangle = |1\rangle$ and $R_Y(\frac{\pi}{2})|0\rangle = |+\rangle$.

The angle is halved inside the formula because a full turn on the Bloch sphere ($\theta = 2\pi$) gives $e^{-i\pi P} = -I$: the state picks up a sign, a **global phase**, which no measurement can detect. Only $\theta = 4\pi$ gives exactly $I$ again.

## Time evolution

A system with Hamiltonian $H$ (its energy observable) evolves for a time $t$ by the unitary

$$U(t) = e^{-iHt/\hbar}$$

Because $H$ is Hermitian, $U(t)$ is unitary. An eigenstate of $H$ with energy $E$ only picks up a phase, $e^{-iEt/\hbar}$: this is why energy eigenstates are called **stationary states**, and why hydrogen's orbitals do not change shape over time.

[Try it: RY(90°) turns |0⟩ into |+⟩](qs:circuit?n=1&gates=RY:0:pi/2)

## Check your understanding

```quiz
Q: What is RX(π) up to a global phase?
* X
- I
- H
E: e^{−iπX/2} = cos(π/2) I − i sin(π/2) X = −iX, which is X times a global phase.
```

```quiz
Q: Why does an energy eigenstate look unchanged over time?
- Its energy is zero
* It only gains a phase e^{−iEt/ħ}, which is unobservable on its own
- Hamiltonians are not unitary
E: e^{−iHt/ħ} acting on an eigenstate just multiplies it by e^{−iEt/ħ}, a global phase.
```

## Summary

- $e^A$ is defined by the exponential series; for Paulis, $e^{-i\theta P/2} = \cos\frac{\theta}{2} I - i\sin\frac{\theta}{2} P$.
- $R_X$, $R_Y$, $R_Z$ are exactly these exponentials: rotations of the Bloch sphere.
- Time evolution is $e^{-iHt/\hbar}$; energy eigenstates only gain a phase.
