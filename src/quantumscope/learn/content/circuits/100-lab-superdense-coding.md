---
title: "Lab: send two bits with one qubit"
area: circuits
kind: lab
order: 100
objectives: Encode two classical bits in one qubit of a Bell pair | Decode them with a Bell measurement
---
# Lab: send two bits with one qubit

You will send the message **10** by superdense coding.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Share a Bell pair
text: Put H on q0, then a CX with control q0 and target q1.
check: qubits 2
check: state H:0;CX:0,1
```

```step
title: Encode 10
text: Alice encodes the first bit with Z and the second with X. For 10, put a Z on q0.
check: state H:0;CX:0,1;Z:0
```

```step
title: Decode
text: Bob applies a CX with control q0 and target q1, then H on q0, and measures both qubits with M→c (q0 into c0, q1 into c1). The record is 10 every time.
check: record 10=1
```

```quiz
Q: What would Alice apply to send 11?
- Only X
- Only Z
* X and then Z
E: The second bit needs X and the first bit needs Z.
```
