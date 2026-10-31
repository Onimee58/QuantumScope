---
title: Phase damping
---
# Phase damping

The qubit gradually loses its phase information while its energy stays the same.

## Kraus operators

$$K_0 = \begin{pmatrix}1 & 0\\ 0 & \sqrt{1-\lambda}\end{pmatrix}, \quad K_1 = \begin{pmatrix}0 & 0\\ 0 & \sqrt{\lambda}\end{pmatrix}$$

## Effect on the Bloch sphere

$$(x,\ y,\ z) \rightarrow \left(\sqrt{1-\lambda}\,x,\ \sqrt{1-\lambda}\,y,\ z\right)$$

Populations are untouched; coherences shrink by $\sqrt{1-\lambda}$. Phase damping with strength $\lambda$ has exactly the same effect on a single qubit as a phase flip with $p = \frac{1}{2}\left(1 - \sqrt{1-\lambda}\right)$.

## Where it comes from

This is **dephasing**: random shifts of the qubit's frequency, for example from fluctuating fields. Together with energy relaxation it sets the **T₂** time, the lifetime of superpositions.
