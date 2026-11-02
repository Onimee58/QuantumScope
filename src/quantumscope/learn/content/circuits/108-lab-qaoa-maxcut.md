---
title: "Lab: cut a graph with QAOA"
area: circuits
kind: lab
order: 108
objectives: Optimize QAOA angles for MaxCut | Read the likeliest cut from the graph view
---
# Lab: cut a graph with QAOA

[Open QAOA on a square, one layer](qs:algorithm/qaoa?graph=ring4&layers=1)

```step
title: Optimize one layer
text: Press Show the graph in the verification panel, then Optimize. The likeliest result becomes a maximum cut (0101 or 1010), and the expected cut reaches 3 of 4 edges.
check: verified
check: expectation <= -2.99
```

```step
title: Two layers
text: Choose Change parameters… and set 2 layers, then Optimize. Now every measurement gives a maximum cut.
check: expectation <= -3.999
```

```quiz
Q: With one layer, what fraction of the square's maximum cut does QAOA reach on average?
* 3/4
- 1/2
- All of it
E: The expected cut is 3 of the maximum 4, the known ratio for rings at one layer.
```
