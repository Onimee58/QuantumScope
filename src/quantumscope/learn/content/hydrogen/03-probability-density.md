---
title: Probability density and radial probability
area: hydrogen
kind: lecture
order: 3
objectives: Distinguish |ψ|² from the radial probability distribution | Find the most probable radius and the mean radius | Interpret clouds and enclosure surfaces
---
# Probability density and radial probability

## Two different questions

$|\psi(\vec r)|^2$ is a **probability density**: the probability of finding the electron in a small volume $dV$ at $\vec r$ is $|\psi|^2 dV$. For 1s it is largest at the nucleus.

The **radial probability** asks instead how likely the electron is to be at distance $r$, in any direction. The thin shell at radius $r$ has volume $4\pi r^2 dr$, which grows with $r$, giving

$$P(r) = r^2 R_{n\ell}(r)^2$$

## Most probable and mean radius

For 1s, $P(r)$ peaks at exactly $r = a_\mu$ — the Bohr radius — although the density peaks at $r = 0$. The two answers differ because there is very little volume near the nucleus.

The mean distance is

$$\langle r\rangle = \frac{3n^2 - \ell(\ell+1)}{2}\,a_\mu$$

so $\langle r\rangle = 1.5\,a_\mu$ for 1s, $6\,a_\mu$ for 2s and $5\,a_\mu$ for 2p. The size grows roughly as $n^2$.

## Pictures of orbitals

An orbital has no sharp edge, so pictures choose what to show. QuantumScope's **enclosure surfaces** contain a chosen fraction of the probability (for example 90%); **clouds** shade the density. The "Fit to states" button in the Dynamics views uses the radius holding 99.5% of the probability — about $4.64\,a_\mu$ for 1s.

[Try it: radial structure in the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: Where is the 1s probability density |ψ|² largest?
* At the nucleus
- At r = a_μ
- At r = 1.5 a_μ
E: |ψ|² falls off as e^(−2r/a_μ) from r = 0; the peak at a_μ belongs to the radial probability r²R².
```

```quiz
Q: What is ⟨r⟩ for a 3d orbital?
- 9 a_μ
* 10.5 a_μ
- 13.5 a_μ
E: (3·9 − 2·3)/2 = (27 − 6)/2 = 10.5 a_μ.
```

## Summary

- |ψ|² is a density per volume; P(r) = r²R² is the probability per distance.
- For 1s the most probable radius is a_μ but ⟨r⟩ = 1.5 a_μ; ⟨r⟩ = (3n² − ℓ(ℓ+1))a_μ/2.
- Clouds and enclosure surfaces are choices about how to show a distribution without an edge.
