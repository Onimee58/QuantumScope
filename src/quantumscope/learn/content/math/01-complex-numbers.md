---
title: Complex numbers
area: math
kind: lecture
order: 1
objectives: Add, multiply and conjugate complex numbers | Use the modulus and the polar form | Read e^{iφ} as a rotation
---
# Complex numbers

Quantum amplitudes are **complex numbers**. This lesson covers everything the other lessons use: arithmetic, size, angle, and the exponential $e^{i\varphi}$.

## The imaginary unit

The number $i$ is defined by $i^2 = -1$. A **complex number** has a real part and an imaginary part:

$$z = a + b\,i \qquad (a, b \text{ real})$$

Think of it as the point $(a, b)$ in a plane: the real part is the horizontal coordinate, the imaginary part the vertical one.

**Adding** works part by part: $(1 + 2i) + (3 - i) = 4 + i$.

**Multiplying** uses $i^2 = -1$:

$$(1 + 2i)(3 - i) = 3 - i + 6i - 2i^2 = 5 + 5i$$

## Conjugate and modulus

The **complex conjugate** flips the sign of the imaginary part: $\bar{z} = a - b\,i$. Geometrically it is a mirror image in the horizontal axis.

The **modulus** $|z|$ is the distance from the origin:

$$|z| = \sqrt{a^2 + b^2}, \qquad |z|^2 = z\,\bar{z}$$

This is the formula behind every quantum probability: an amplitude $\alpha$ gives probability $|\alpha|^2 = \alpha\bar{\alpha}$. For $\alpha = \frac{1 + i}{2}$, $|\alpha|^2 = \frac{1}{4} + \frac{1}{4} = \frac{1}{2}$.

## Polar form and Euler's formula

A point in the plane can also be given by its distance $r$ and its angle $\varphi$ from the positive real axis. **Euler's formula** connects the two descriptions:

$$e^{i\varphi} = \cos\varphi + i\,\sin\varphi$$

So every complex number can be written $z = r\,e^{i\varphi}$, with $r = |z|$. Some values worth remembering:

| $\varphi$ | $e^{i\varphi}$ |
|---|---|
| $0$ | $1$ |
| $\pi/2$ | $i$ |
| $\pi$ | $-1$ |
| $3\pi/2$ | $-i$ |

Every $e^{i\varphi}$ has modulus 1: it lies on the unit circle.

## Multiplying means rotating and scaling

In polar form, multiplication is simple: multiply the sizes and **add the angles**:

$$r_1 e^{i\varphi_1} \cdot r_2 e^{i\varphi_2} = r_1 r_2\, e^{i(\varphi_1 + \varphi_2)}$$

Multiplying by $e^{i\varphi}$ therefore **rotates** a number by $\varphi$ without changing its size. That is exactly what a **phase** does to an amplitude: it changes the angle, never the probability $|\alpha|^2$. Relative angles between amplitudes, however, decide whether they add up or cancel: **interference**.

[Try it: change the phase φ of a qubit and watch the Bloch arrow turn](qs:open/superposition)

## Check your understanding

```quiz
Q: What is (2 + i)(2 − i)?
- 4 − i
* 5
- 3
E: (2 + i)(2 − i) = 4 − 2i + 2i − i² = 4 + 1 = 5. A number times its conjugate is always |z|², a real number.
```

```quiz
Q: An amplitude is multiplied by e^{iπ/3}. What happens to its probability?
* Nothing: |e^{iπ/3}| = 1
- It is multiplied by π/3
- It becomes complex
E: Multiplying by e^{iφ} rotates the amplitude in the complex plane. Its modulus, and so the probability |α|², stays the same.
```

## Summary

- $z = a + bi$ is a point in the plane; $\bar{z} = a - bi$ is its mirror image.
- $|z|^2 = z\bar{z}$, the rule behind every quantum probability.
- $e^{i\varphi} = \cos\varphi + i\sin\varphi$ lies on the unit circle; multiplying by it rotates by $\varphi$.
