---
title: Quantum numbers and orbitals
area: hydrogen
kind: lecture
order: 2
objectives: List the allowed values of n, ℓ and m | Count states per energy level | Predict the number of radial and angular nodes
---
# Quantum numbers and orbitals

## The three quantum numbers

| Number | Name | Allowed values | Sets |
|---|---|---|---|
| n | principal | 1, 2, 3, … | energy and overall size |
| ℓ | orbital angular momentum | 0, 1, …, n − 1 | shape (s, p, d, f for ℓ = 0, 1, 2, 3) |
| m | magnetic | −ℓ, …, +ℓ | orientation about the z axis |

## Counting states

For each $\ell$ there are $2\ell + 1$ values of $m$, so level $n$ holds

$$\sum_{\ell=0}^{n-1}(2\ell+1) = n^2$$

orbitals, all with the same energy in this model (spin doubles this to $2n^2$). For $n = 2$: one 2s and three 2p orbitals.

## Nodes

An orbital has $n - \ell - 1$ **radial nodes** (spheres where $\psi = 0$) and $\ell$ **angular nodes** (planes or cones), $n - 1$ in total. The 2s orbital has one radial node; 2p has one nodal plane; 3d has two angular nodes.

## Complex and real orbitals

The states $\psi_{n\ell m}$ with $m \ne 0$ are complex: their density is symmetric around $z$ and they carry angular momentum about that axis. Chemistry's familiar $p_x$ and $p_y$ are **real** combinations of $m = +1$ and $m = -1$; they have the same energy, and they point along $x$ and $y$.

[Try it: compare orbitals in the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: How many orbitals (ignoring spin) have n = 3?
- 3
- 6
* 9
- 18
E: n² = 9: one 3s, three 3p and five 3d.
```

```quiz
Q: How many radial nodes does a 3p orbital have?
- 0
* 1
- 2
E: n − ℓ − 1 = 3 − 1 − 1 = 1.
```

## Summary

- n ≥ 1, 0 ≤ ℓ ≤ n − 1, −ℓ ≤ m ≤ ℓ; level n holds n² orbitals.
- Radial nodes: n − ℓ − 1; angular nodes: ℓ.
- Real orbitals such as pₓ are combinations of the complex m = ±1 states.
